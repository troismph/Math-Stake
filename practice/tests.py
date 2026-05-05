import random

from django.test import TestCase
from django.urls import reverse

from .models import AttemptQuestion, TestAttempt, TestConfig
from .services import generate_paper, step_has_transfer


class ProblemGenerationTests(TestCase):
	def test_generated_problems_follow_constraints(self):
		config = TestConfig.objects.create(
			name="三项加减法",
			number_count=3,
			max_operand=20,
			question_count=8,
			allow_negative_intermediate=True,
			duration_seconds=90,
		)

		problems = generate_paper(config, rng=random.Random(7), max_attempts=5000)

		self.assertTrue(problems)
		self.assertLessEqual(len(problems), config.question_count)
		self.assertEqual(len({problem.expression for problem in problems}), len(problems))

		for problem in problems:
			tokens = problem.expression.split()
			total = int(tokens[0])
			for index in range(1, len(tokens), 2):
				operator = tokens[index]
				operand = int(tokens[index + 1])
				self.assertTrue(step_has_transfer(total, operator, operand))
				total = total + operand if operator == "+" else total - operand

			self.assertEqual(total, problem.answer)
			self.assertGreaterEqual(problem.answer, 0)


class AttemptSubmissionTests(TestCase):
	def test_blank_answers_are_counted_as_wrong(self):
		config = TestConfig.objects.create(
			name="两项口算",
			number_count=2,
			max_operand=20,
			question_count=3,
			allow_negative_intermediate=False,
			duration_seconds=60,
		)
		attempt = TestAttempt.objects.create(config=config, total_questions=3)
		first = AttemptQuestion.objects.create(attempt=attempt, position=1, expression="9 + 8", correct_answer=17)
		second = AttemptQuestion.objects.create(attempt=attempt, position=2, expression="14 - 8", correct_answer=6)
		third = AttemptQuestion.objects.create(attempt=attempt, position=3, expression="8 + 7", correct_answer=15)

		response = self.client.post(
			reverse("practice:submit", args=[attempt.pk]),
			{
				f"question_{first.pk}": "17",
				f"question_{second.pk}": "",
				f"question_{third.pk}": "12",
			},
		)

		self.assertRedirects(response, reverse("practice:result", args=[attempt.pk]))

		attempt.refresh_from_db()
		first.refresh_from_db()
		second.refresh_from_db()
		third.refresh_from_db()

		self.assertTrue(attempt.completed)
		self.assertEqual(attempt.correct_questions, 1)
		self.assertEqual(attempt.total_questions, 3)
		self.assertTrue(first.is_correct)
		self.assertFalse(second.is_correct)
		self.assertIsNone(second.user_answer)
		self.assertFalse(third.is_correct)
