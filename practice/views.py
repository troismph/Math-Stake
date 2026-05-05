from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import AttemptQuestion, TestAttempt, TestConfig
from .services import generate_paper


@require_GET
def home(request):
	test_configs = TestConfig.objects.filter(is_active=True)
	return render(request, "practice/home.html", {"test_configs": test_configs})


@require_POST
def start_test(request, config_id):
	config = get_object_or_404(TestConfig, pk=config_id, is_active=True)
	problems = generate_paper(config)
	attempt = TestAttempt.objects.create(config=config, total_questions=len(problems))

	AttemptQuestion.objects.bulk_create(
		[
			AttemptQuestion(
				attempt=attempt,
				position=index,
				expression=problem.expression,
				correct_answer=problem.answer,
			)
			for index, problem in enumerate(problems, start=1)
		]
	)

	if not problems:
		attempt.completed = True
		attempt.submitted_at = timezone.now()
		attempt.save(update_fields=["completed", "submitted_at"])
		messages.warning(request, "这次没有生成可用题目，请调整后台配置后再试。")
		return redirect("practice:result", attempt_id=attempt.pk)

	return redirect("practice:attempt", attempt_id=attempt.pk)


@require_GET
def attempt_detail(request, attempt_id):
	attempt = get_object_or_404(TestAttempt.objects.select_related("config"), pk=attempt_id)
	if attempt.completed:
		return redirect("practice:result", attempt_id=attempt.pk)

	elapsed = int((timezone.now() - attempt.created_at).total_seconds())
	remaining_seconds = max(attempt.config.duration_seconds - elapsed, 0)
	return render(
		request,
		"practice/attempt.html",
		{
			"attempt": attempt,
			"questions": attempt.questions.all(),
			"remaining_seconds": remaining_seconds,
		},
	)


@require_POST
def submit_attempt(request, attempt_id):
	attempt = get_object_or_404(TestAttempt.objects.select_related("config"), pk=attempt_id)
	if attempt.completed:
		return redirect("practice:result", attempt_id=attempt.pk)

	questions = list(attempt.questions.all())
	correct_count = 0
	for question in questions:
		raw_answer = request.POST.get(f"question_{question.pk}", "").strip()
		if raw_answer:
			try:
				question.user_answer = int(raw_answer)
			except ValueError:
				question.user_answer = None
		else:
			question.user_answer = None

		question.is_correct = question.user_answer == question.correct_answer
		if question.is_correct:
			correct_count += 1

	AttemptQuestion.objects.bulk_update(questions, ["user_answer", "is_correct"])

	submitted_at = timezone.now()
	elapsed_seconds = int((submitted_at - attempt.created_at).total_seconds())
	attempt.submitted_at = submitted_at
	attempt.elapsed_seconds = max(0, min(elapsed_seconds, attempt.config.duration_seconds))
	attempt.correct_questions = correct_count
	attempt.total_questions = len(questions)
	attempt.completed = True
	attempt.save(
		update_fields=[
			"submitted_at",
			"elapsed_seconds",
			"correct_questions",
			"total_questions",
			"completed",
		]
	)
	return redirect("practice:result", attempt_id=attempt.pk)


@require_GET
def result_detail(request, attempt_id):
	attempt = get_object_or_404(TestAttempt.objects.select_related("config"), pk=attempt_id)
	if not attempt.completed:
		return redirect("practice:attempt", attempt_id=attempt.pk)

	incorrect_questions = attempt.questions.filter(is_correct=False)
	return render(
		request,
		"practice/result.html",
		{
			"attempt": attempt,
			"incorrect_questions": incorrect_questions,
		},
	)
