import json
import re
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum 
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy
from django.views.generic import UpdateView  # ✅ Ensure this is imported
import requests 
from django.conf import settings 
from .gpt_ai import grade_with_gpt


# ✅ Import models properly
from .models import ElectronicExam, Question, Choice, StudentResponse
from courses.models import Course
from users.models import CustomUser

# ✅ Exam List View
@method_decorator(login_required, name="dispatch")
class ExamListView(View):
    def get(self, request):
        if request.user.is_instructor:
            exams = ElectronicExam.objects.all()  # ✅ Instructors see all exams
        else:
            exams = ElectronicExam.objects.filter(course__students=request.user)  # ✅ Students see only their course exams
        
        student_grades = {}

        if request.user.is_student:
            student_responses = StudentResponse.objects.filter(student=request.user)

            for exam in exams:
                # ✅ Total score from responses
                total_score = student_responses.filter(question__exam=exam).aggregate(total_score=Sum("score"))["total_score"]
                
                # ✅ Normalize grade to exam's total marks
                if total_score is not None:
                    student_grades[exam.id] = round((total_score / exam.total_marks) * exam.total_marks, 2)
                else:
                    student_grades[exam.id] = "Not Taken Yet"

                # ✅ If the exam has AI-graded questions, mark as "Not Graded Yet"
                if student_responses.filter(question__exam=exam, question__question_type__in=["SHORT", "LONG"]).exists():
                    student_grades[exam.id] = "Not Graded Yet"

        return render(request, "electronic_exams/exam_list.html", {
            "exams": exams,
            "student_grades": student_grades
        })


# ✅ Exam Detail View
@method_decorator(login_required, name="dispatch")
class ExamDetailView(View):
    def get(self, request, pk):
        exam = get_object_or_404(ElectronicExam, pk=pk)

        # ✅ Instructors can see all students' grades
        students = None
        if request.user.is_instructor:
            students = StudentResponse.objects.filter(question__exam=exam).select_related("student")

        # ✅ Students see only their grade
        student_grade = "Not Taken Yet"
        show_take_exam_button = True

        if request.user.is_student:
            student_responses = StudentResponse.objects.filter(student=request.user, question__exam=exam)

            if student_responses.exists():
                total_score = student_responses.aggregate(total_score=Sum("score"))["total_score"]

                # ✅ If AI is needed for grading, show "Not Graded Yet"
                if student_responses.filter(question__question_type__in=["SHORT", "LONG"]).exists():
                    student_grade = "Not Graded Yet"
                else:
                    student_grade = total_score if total_score is not None else "Not Graded Yet"

                show_take_exam_button = False  # Hide "Take Exam" if already taken

        return render(
            request, 
            "electronic_exams/exam_detail.html", 
            {
                "exam": exam,
                "questions": exam.questions.all(),
                "students": students,  # ✅ Instructors see all students
                "student_grade": student_grade,  # ✅ Students see only their grade
                "show_take_exam_button": show_take_exam_button  # ✅ Control button visibility
            }
        )

# ✅ Create Exam View
@method_decorator(login_required, name="dispatch")
class CreateExamView(View):
    def get(self, request):
        if not request.user.is_instructor:  # ✅ Prevent students from creating exams
            messages.error(request, "⚠️ Only instructors can create exams!")
            return redirect("electronic_exams:exam_list")

        courses = Course.objects.all()
        return render(request, "electronic_exams/create_exam.html", {"courses": courses})

    def post(self, request):
        if not request.user.is_instructor:  # ✅ Block students from posting
            messages.error(request, "⚠️ Only instructors can create exams!")
            return redirect("electronic_exams:exam_list")

        exam_title = request.POST.get("exam_name")
        course_id = request.POST.get("course")
        total_marks = request.POST.get("total_marks")
        duration = request.POST.get("exam_time")

        if not exam_title or not course_id or not total_marks:
            messages.error(request, "Please fill in all required fields!")
            return redirect("electronic_exams:create_exam")

        course = get_object_or_404(Course, id=course_id)
        exam = ElectronicExam.objects.create(
            title=exam_title,
            course=course,
            total_marks=int(total_marks),
            duration_minutes=int(duration) if duration else None
        )

        # ✅ Process and Save Questions
        self._process_questions(request, exam)

        messages.success(request, "✅ Exam created successfully!")
        return redirect("electronic_exams:exam_list")

    # ✅ Add the missing `_process_questions` method
    def _process_questions(self, request, exam):
        """Handles saving questions from form inputs"""

        # ✅ True/False Questions
        for question, answer in zip(request.POST.getlist("tf_questions[]"), request.POST.getlist("tf_answers[]")):
            Question.objects.create(exam=exam, text=question, question_type="TF", ideal_answer=answer)

        # ✅ Multiple Choice Questions
        for question, options, answer in zip(request.POST.getlist("mcq_questions[]"), request.POST.getlist("mcq_options[]"), request.POST.getlist("mcq_answers[]")):
            q = Question.objects.create(exam=exam, text=question, question_type="MCQ", ideal_answer=answer)
            for option in options.split(","):
                Choice.objects.create(question=q, text=option.strip(), is_correct=option.strip() == answer.strip())

        # ✅ Short Answer Questions
        for question, answer in zip(request.POST.getlist("short_questions[]"), request.POST.getlist("short_model_answers[]")):
            Question.objects.create(exam=exam, text=question, question_type="SHORT", ideal_answer=answer)

        # ✅ Long Answer Questions
        for question, answer in zip(request.POST.getlist("long_questions[]"), request.POST.getlist("long_model_answers[]")):
            Question.objects.create(exam=exam, text=question, question_type="LONG", ideal_answer=answer)

# ✅ Exam Results View
@method_decorator(login_required, name="dispatch")
class ExamResultsView(View):
    def get(self, request, pk):
        exam = get_object_or_404(ElectronicExam, pk=pk)
        student_responses = StudentResponse.objects.filter(student=request.user, question__exam=exam)
        return render(request, "electronic_exams/exam_results.html", {"exam": exam, "responses": student_responses})


# ✅ Edit Exam View (Fixed Course Issue)
@method_decorator(login_required, name="dispatch")
class EditExamView(UpdateView):
    model = ElectronicExam
    fields = ["title", "total_marks", "course"]
    template_name = "electronic_exams/edit_exam.html"
    success_url = reverse_lazy("electronic_exams:exam_list")

    def dispatch(self, request, *args, **kwargs):
        exam = get_object_or_404(ElectronicExam, pk=self.kwargs["pk"])
        if not request. user.is_instructor:  # ✅ Prevent students from editing
            messages.error(request, "⚠️ Only instructors can edit exams!")
            return redirect("electronic_exams:exam_list")

        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["exam"] = self.object
        context["courses"] = Course.objects.all()  # ✅ Ensure courses are available in the template
        return context

# ✅ Delete Question View
@method_decorator(login_required, name="dispatch")
class DeleteQuestionView(View):
    def post(self, request, question_id):
        get_object_or_404(Question, id=question_id).delete()
        return JsonResponse({"message": "Question deleted successfully!"})


# ✅ Toggle Exam Activation
@method_decorator(login_required, name="dispatch")
class ToggleExamView(View):
    def post(self, request, pk):
        exam = get_object_or_404(ElectronicExam, pk=pk)
        exam.is_active = not exam.is_active
        exam.save()
        return JsonResponse({"status": "success", "is_active": exam.is_active})
    

@method_decorator(login_required, name="dispatch")
class UpdateQuestionView(UpdateView):
    model = Question
    fields = ["text", "question_type", "ideal_answer"]
    template_name = "electronic_exams/update_question.html"
    
    def get_success_url(self):
        return reverse_lazy("electronic_exams:exam_detail", kwargs={"pk": self.object.exam.pk})

@method_decorator(login_required, name="dispatch")
class DeleteExamView(View):
    def post(self, request, pk):
        """Deletes an exam after confirmation."""
        exam = get_object_or_404(ElectronicExam, pk=pk)

        if not request.user.is_instructor:  # ✅ Prevent students from deleting
            messages.error(request, "⚠️ Only instructors can delete exams!")
            return redirect("electronic_exams:exam_list")

        exam.delete()
        return JsonResponse({"status": "success"})

################################### Student's pov ######################################
################################### Student's pov ######################################

@method_decorator(login_required, name="dispatch")
class TakeExamView(View):
    def get(self, request, pk):
        """Render the exam-taking page with a timer and full-screen mode."""
        exam = get_object_or_404(ElectronicExam, pk=pk)
        questions = exam.questions.all()
        exam_duration_seconds = exam.duration_minutes * 60 if exam.duration_minutes else 0

        return render(
            request,
            "electronic_exams/take_exam.html",
            {
                "exam": exam,
                "questions": questions,
                "exam_duration_seconds": exam_duration_seconds,  # ✅ Ensure seconds
            }
        )

    def post(self, request, pk):
        """Handles exam submission & ensures AI grading works properly."""
        exam = get_object_or_404(ElectronicExam, pk=pk)
        student = request.user

        total_score = 0  # ✅ Accumulate total score
        total_marks = exam.total_marks  # ✅ Instructor-defined total marks

        for question in exam.questions.all():
            response_text = request.POST.get(f"q{question.id}", "").strip()
            is_correct = None
            score = 0  # ✅ Default score is 0
            ai_feedback = None

            # ✅ Auto-grade MCQ & TF
            if question.question_type in ["MCQ", "TF"]:
                correct_answer = question.ideal_answer.strip() if question.ideal_answer else None
                is_correct = response_text.lower() == correct_answer.lower() if correct_answer else None
                score = question.marks if is_correct else 0  # ✅ Score = question marks if correct

            # ✅ AI-Graded Questions (Short & Long)
            if question.question_type in ["SHORT", "LONG"]:
                score, ai_feedback = grade_with_gpt(question.text, response_text, question.ideal_answer, question.marks)

            # ✅ Save Student Response
            StudentResponse.objects.update_or_create(
                student=student, question=question,
                defaults={
                    "answer_text": response_text,
                    "is_correct": is_correct,
                    "score": score,
                    "ai_feedback": ai_feedback
                }
            )

            if score is not None:
                total_score += score  # ✅ Accumulate only graded responses

        # ✅ Normalize score based on instructor-defined total marks
        final_score = (total_score / total_marks) * exam.total_marks if total_marks else 0

        return JsonResponse({
            "status": "success",
            "redirect_url": reverse_lazy("electronic_exams:exam_list"),
            "final_score": round(final_score, 2)  # ✅ Return properly scaled score
        })
    
@login_required
def auto_save_response(request):
    """Handles real-time auto-save for student answers."""
    if request.method == "POST":
        data = json.loads(request.body)
        question_id = data.get("question_id")
        response_text = data.get("response")
        question = get_object_or_404(Question, id=question_id)

        response, created = StudentResponse.objects.get_or_create(
            student=request.user, question=question
        )
        response.answer_text = response_text
        response.save()

        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)


@login_required
def exam_students_grades(request, exam_id):
    """View for instructors to see student grades for a specific exam."""
    exam = get_object_or_404(ElectronicExam, id=exam_id)
    students_grades = StudentResponse.objects.filter(question__exam=exam).select_related("student")

    return render(request, "electronic_exams/exam_students_grades.html", {
        "exam": exam,
        "students_grades": students_grades,
    })


