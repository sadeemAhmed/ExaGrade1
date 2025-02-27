from django.db import models

# Create your models here.
from django.db import models
from users.models import CustomUser  # Assuming CustomUser is your user model

class ElectronicExam(models.Model):
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="electronic_exams")
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    exam = models.ForeignKey(ElectronicExam, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=[
            ("MCQ", "Multiple Choice"),
            ("TF", "True/False"),
            ("SHORT", "Short Answer"),
            ("LONG", "Long Answer"),
        ],
    )
    ideal_answer = models.TextField(blank=True, null=True)  # For AI grading

    def __str__(self):
        return self.text

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class StudentResponse(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="responses")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="responses")
    answer_text = models.TextField()
    is_correct = models.BooleanField(null=True, blank=True)  # For AI grading
    score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.student} - {self.question.text}"
