from django.core.validators import MinValueValidator
from django.db import models


class TestConfig(models.Model):
	name = models.CharField(max_length=100, unique=True)
	description = models.CharField(max_length=255, blank=True)
	number_count = models.PositiveIntegerField(validators=[MinValueValidator(2)])
	max_operand = models.PositiveIntegerField(validators=[MinValueValidator(1)])
	question_count = models.PositiveIntegerField(validators=[MinValueValidator(1)])
	allow_negative_intermediate = models.BooleanField(default=False)
	duration_seconds = models.PositiveIntegerField(validators=[MinValueValidator(10)])
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("name",)
		verbose_name = "测试配置"
		verbose_name_plural = "测试配置"

	def __str__(self) -> str:
		return self.name


class TestAttempt(models.Model):
	config = models.ForeignKey(TestConfig, on_delete=models.PROTECT, related_name="attempts")
	created_at = models.DateTimeField(auto_now_add=True)
	submitted_at = models.DateTimeField(null=True, blank=True)
	elapsed_seconds = models.PositiveIntegerField(default=0)
	total_questions = models.PositiveIntegerField(default=0)
	correct_questions = models.PositiveIntegerField(default=0)
	completed = models.BooleanField(default=False)

	class Meta:
		ordering = ("-created_at",)
		verbose_name = "测试结果"
		verbose_name_plural = "测试结果"

	def __str__(self) -> str:
		return f"{self.config.name} @ {self.created_at:%Y-%m-%d %H:%M:%S}"

	@property
	def score_percentage(self) -> float:
		if self.total_questions == 0:
			return 0.0
		return round(self.correct_questions * 100 / self.total_questions, 1)


class AttemptQuestion(models.Model):
	attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name="questions")
	position = models.PositiveIntegerField()
	expression = models.CharField(max_length=255)
	correct_answer = models.IntegerField()
	user_answer = models.IntegerField(null=True, blank=True)
	is_correct = models.BooleanField(default=False)

	class Meta:
		ordering = ("position",)
		unique_together = ("attempt", "position")
		verbose_name = "题目明细"
		verbose_name_plural = "题目明细"

	def __str__(self) -> str:
		return f"{self.attempt} #{self.position}"
