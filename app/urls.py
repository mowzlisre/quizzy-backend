from django.urls import path
from app import api

urlpatterns = [
    path('projects', api.ProjectsView.as_view()),
    path('project/<id>', api.ProjectView.as_view()),
    path('project/<id>/assessments', api.AssessmentsView.as_view()),
    path('assessment/<id>', api.AssessmentView.as_view()),
]