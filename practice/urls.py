from django.urls import path

from . import views

app_name = "practice"

urlpatterns = [
    path("", views.home, name="home"),
    path("tests/<int:config_id>/start/", views.start_test, name="start"),
    path("attempts/<int:attempt_id>/", views.attempt_detail, name="attempt"),
    path("attempts/<int:attempt_id>/submit/", views.submit_attempt, name="submit"),
    path("attempts/<int:attempt_id>/result/", views.result_detail, name="result"),
]