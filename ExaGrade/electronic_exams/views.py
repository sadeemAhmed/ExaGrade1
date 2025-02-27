from django.shortcuts import render, get_object_or_404
from django.views import View
from .models import ElectronicExam
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

class ExamListView(View):
    def get(self, request):
        exams = ElectronicExam.objects.all()
        return render(request, "electronic_exams/exam_list.html", {"exams": exams})

class ExamDetailView(View):  # ✅ Ensure this class exists
    def get(self, request, pk):
        exam = get_object_or_404(ElectronicExam, pk=pk)
        return render(request, "electronic_exams/exam_detail.html", {"exam": exam})

@method_decorator(login_required, name="dispatch")
class CreateExamView(View):
    def get(self, request):
        return render(request, "electronic_exams/create_exam.html")

    def post(self, request):
        # Logic for creating an exam
        return render(request, "electronic_exams/create_exam.html")

@method_decorator(login_required, name="dispatch")
class TakeExamView(View):
    def get(self, request, pk):
        exam = get_object_or_404(ElectronicExam, pk=pk)
        return render(request, "electronic_exams/take_exam.html", {"exam": exam})
