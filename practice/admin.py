from django.contrib import admin

from .models import AttemptQuestion, TestAttempt, TestConfig


@admin.register(TestConfig)
class TestConfigAdmin(admin.ModelAdmin):
	list_display = (
		"name",
		"number_count",
		"max_operand",
		"question_count",
		"allow_negative_intermediate",
		"duration_seconds",
		"is_active",
	)
	list_filter = ("is_active", "allow_negative_intermediate")
	search_fields = ("name", "description")


class AttemptQuestionInline(admin.TabularInline):
	model = AttemptQuestion
	extra = 0
	can_delete = False
	readonly_fields = ("position", "expression", "correct_answer", "user_answer", "is_correct")


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
	list_display = (
		"config",
		"created_at",
		"completed",
		"correct_questions",
		"total_questions",
		"score_percentage",
		"elapsed_seconds",
	)
	list_filter = ("completed", "config")
	search_fields = ("config__name",)
	readonly_fields = (
		"config",
		"created_at",
		"submitted_at",
		"elapsed_seconds",
		"total_questions",
		"correct_questions",
		"completed",
		"score_percentage",
	)
	inlines = (AttemptQuestionInline,)

	def has_add_permission(self, request):
		return False
