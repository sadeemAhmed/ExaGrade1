from django.urls import path
from . import views
from .views import (
    DeleteExamView,
    ExamListView,
    ExamDetailView,
    CreateExamView,
    TakeExamView,
    ExamResultsView,
    EditExamView,
    DeleteQuestionView,
    ToggleExamView,
    UpdateQuestionView,
    auto_save_response,
)

app_name = "electronic_exams"

urlpatterns = [
    path("", ExamListView.as_view(), name="exam_list"),
    path("<int:pk>/", ExamDetailView.as_view(), name="exam_detail"),
    path("create/", CreateExamView.as_view(), name="create_exam"), 
    path("<int:pk>/results/", ExamResultsView.as_view(), name="exam_results"),
    path("<int:pk>/edit/", EditExamView.as_view(), name="edit_exam"),
    path("question/<int:question_id>/delete/", DeleteQuestionView.as_view(), name="delete_question"),
     path("edit/<int:pk>/", EditExamView.as_view(), name="edit_exam"),
    path("<int:pk>/toggle/", ToggleExamView.as_view(), name="toggle_exam"),
    path("update-question/<int:pk>/", UpdateQuestionView.as_view(), name="update_question"),
    path("<int:pk>/delete/", DeleteExamView.as_view(), name="delete_exam"),
    
    path("take/<int:pk>/", TakeExamView.as_view(), name="take_exam"),
    #path("exam/<int:pk>/results/", ExamResultsView.as_view(), name="exam_results"),
    path("auto-save/", auto_save_response, name="auto_save_response"),
    path("<int:exam_id>/students_grades/", views.exam_students_grades, name="exam_students_grades"),
]
