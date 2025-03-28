from django.urls import path
from app import api

urlpatterns = [
    path('projects', api.ProjectsView.as_view()),
    path('project/<id>', api.ProjectView.as_view()),
    path('project/<id>/assessments', api.AssessmentsView.as_view()),
    path('assessment/new', api.CreateAssessment.as_view()),
    path('attempt/new', api.NewAttempt.as_view()),
    path('attempt/start', api.StartAttempt.as_view()),
    path('assessment/<id>', api.AssessmentView.as_view()),
    path('project/<id>/upload', api.MaterialUploadView.as_view()),
    path('project/<id>/delete', api.DeleteFileFromProject.as_view()),
]