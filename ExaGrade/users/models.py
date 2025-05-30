from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    is_instructor = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    student_responses = models.ManyToManyField("electronic_exams.StudentResponse", related_name="grades_received", blank=True)

    profile_image = models.ImageField(
        upload_to="profiles/",
        default="profiles/profile-default.png",
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        if not self.profile_image:
            self.profile_image = "profiles/profile-default.png"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

def get_grades(self):
        """Retrieve all grades for the student."""
        return self.student_responses.all()