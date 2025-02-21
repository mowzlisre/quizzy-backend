from django.contrib import admin
from .models import Project, ProjectMaterial, MaterialChunks, Attempt, Assessment

@admin.register(ProjectMaterial)
class ProjectMaterialAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "file_type", "uploaded_at")
    search_fields = ("name", "user__username")
    list_filter = ("file_type", "uploaded_at")

@admin.register(MaterialChunks)
class MaterialChunksAdmin(admin.ModelAdmin):
    list_display = ("material", "text")
    search_fields = ("material__name", "text")

@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("max_score", "attempt_score")
    search_fields = ("max_score", "attempt_score")

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("assessment_id", "assessment_title", "difficulty", "attempts", "status")
    search_fields = ("assessment_title", "assessment_id")
    list_filter = ("difficulty", "status")

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "user")
    search_fields = ("name", "user__username")

