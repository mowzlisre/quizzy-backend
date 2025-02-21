from django.db import models
from django.contrib.auth.models import User
import uuid

class ProjectMaterial(models.Model):
    FILE_TYPES = (
        ('pdf', 'PDF'),
        ('docx', 'Word Document'),
        ('txt', 'Text File'),
        ('pptx', 'PowerPoint Presentation'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="project_materials")
    name = models.TextField()
    file = models.URLField()
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class MaterialChunks(models.Model):
    text = models.TextField()
    material = models.ForeignKey(ProjectMaterial, on_delete=models.CASCADE, related_name="chunks")

class Attempt(models.Model):
    max_score = models.PositiveSmallIntegerField(default=0)
    attempt_score = models.PositiveSmallIntegerField(default=0)
    answers = models.JSONField()
    feedback = models.JSONField()

class Assessment(models.Model):
    DIFFICULTY = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )
    assessment_id = models.CharField(max_length=10)
    assessment_title = models.CharField(max_length=256)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY)
    quiz = models.JSONField()
    attempts = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=20)
    feedback = models.JSONField()
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name="assessments", null=True, blank=True)

class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")
    materials = models.ManyToManyField(ProjectMaterial, related_name="projects")
