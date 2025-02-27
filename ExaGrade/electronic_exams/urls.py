from django.urls import path
from .views import ExamListView, ExamDetailView, CreateExamView, TakeExamView

app_name = "electronic_exams"  # ✅ Namespace is required for `{% url 'electronic_exams:electronic_exam_detail' %}`

urlpatterns = [
    path("", ExamListView.as_view(), name="exam_list"),
    path("<int:pk>/", ExamDetailView.as_view(), name="electronic_exam_detail"),  # ✅ Fix here
    path("create/", CreateExamView.as_view(), name="create_electronic_exam"),
    path("take/<int:pk>/", TakeExamView.as_view(), name="take_exam"),
]
