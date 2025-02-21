from django.urls import path
from app import api

urlpatterns = [
    path('projects', api.ProjectsView.as_view()),
]