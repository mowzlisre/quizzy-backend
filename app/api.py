from django.shortcuts import render
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework import viewsets
from .models import Project, ProjectMaterial, MaterialChunks, Attempt, Assessment
from.serializers import ProjectSerializer

class ProjectsView(APIView):
    def get(self, request):
        projects = Project.objects.filter(user__username=request.user.username)
        data = ProjectSerializer(projects, many=True).data
        return JsonResponse(data, safe=False)