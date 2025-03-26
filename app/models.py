from django.db import models
from django.contrib.auth.models import User
import uuid
from .utils import time_since

class ProjectMaterial(models.Model):
    FILE_TYPES = (
        ('pdf', 'PDF'),
        ('docx', 'Word Document'),
        ('txt', 'Text File'),
        ('pptx', 'PowerPoint Presentation'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="project_materials")
    name = models.TextField()
    file = models.URLField()
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    important_tokens = models.JSONField()

class MaterialChunks(models.Model):
    text = models.TextField()
    material = models.ForeignKey(ProjectMaterial, on_delete=models.CASCADE, related_name="chunks")

class Attempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    max_score = models.PositiveSmallIntegerField(default=0)
    attempt_score = models.PositiveSmallIntegerField(default=0)
    answers = models.JSONField(blank=True, null=True)
    feedback = models.JSONField(blank=True, null=True)
    time_taken = models.PositiveSmallIntegerField(default=0)
    timeStamp = models.DateTimeField()
    submission = models.BooleanField(default=False)
    timed = models.BooleanField(default=False)
    total_duration = models.PositiveSmallIntegerField(default=0)
    partial_credits = models.BooleanField(default=False)
    negative_score = models.BooleanField(default=False)
    proctored = models.BooleanField(default=False)
    proctor_meta = models.JSONField()

class Assessment(models.Model):
    DIFFICULTY = (
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    )
    assessment_id = models.CharField(max_length=10)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment_title = models.CharField(max_length=256)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='author')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY)
    quiz = models.JSONField(null=True, blank=True)
    attempts = models.ManyToManyField(Attempt, blank=True)
    status = models.CharField(max_length=20)
    feedback = models.JSONField(null=True, blank=True)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name="assessments", null=True, blank=True)
    createdAt = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.assessment_id:
            latest = Assessment.objects.order_by('-createdAt').first()
            if latest and latest.assessment_id:
                last_number = int(latest.assessment_id[1:])
            else:
                last_number = 0
            new_number = last_number + 1
            self.assessment_id = f"A{new_number:03d}" 
        super().save(*args, **kwargs)
        
    @property
    def created(self):
        return time_since(self.createdAt)

    @property
    def recentattempt(self):
        return time_since(self.lastAttempt)

class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")
    materials = models.ManyToManyField(ProjectMaterial, related_name="projects")
