from django.shortcuts import render
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework import viewsets
from .models import Project, ProjectMaterial, MaterialChunks, Attempt, Assessment
from .serializers import ProjectSerializer, AssessmentSerializer

class ProjectsView(APIView):
    def get(self, request):
        projects = Project.objects.filter(user__username=request.user.username)
        data = ProjectSerializer(projects, many=True).data
        return JsonResponse(data, safe=False)

class ProjectView(APIView):
    def get(self, request, id):
        project = Project.objects.get(user__username=request.user.username, id=id)
        data = ProjectSerializer(project).data
        return JsonResponse(data, safe=False)
    
class AssessmentsView(APIView):
    def get(self, request, id):
        assessments = Assessment.objects.filter(project__id=id)
        data = AssessmentSerializer(assessments, many=True).data
        return JsonResponse(data, safe=False)
    
class AssessmentView(APIView):
    def get(self, request, id):
        assessment = Assessment.objects.get(id=id)
        data = AssessmentSerializer(assessment).data
        return JsonResponse(data, safe=False)