from rest_framework.views import APIView
from django.http import JsonResponse
from .models import Project, ProjectMaterial, MaterialChunks, Attempt, Assessment
from .serializers import ProjectSerializer, AssessmentSerializer
import os, uuid
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from app.preprocess.text_extract import extract_text
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from .mongo import mongo_collection, chunk_text
from .preprocess.tfidf import performTFIDF
from sentence_transformers import SentenceTransformer
from .rag.faiss import fetchRelevantDocuments
from rest_framework.permissions import IsAuthenticated
import requests
import json
from .tasks import process_uploaded_file

class ProjectsView(APIView):
    permission_classes = [IsAuthenticated]
    
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
    

class MaterialUploadView(APIView):
    def post(self, request, id):
        try:
            project = Project.objects.get(id=id)

            if "files" not in request.FILES:
                print("No File")
                return JsonResponse({"error": "No files provided"}, status=400)

            for file in request.FILES.getlist("files"):
                original_name = file.name  # Store the original file name
                ext = original_name.split('.')[-1].lower()

                # Generate a random file name
                random_filename = f"{uuid.uuid4().hex}.{ext}"
                file_path = os.path.join(settings.UPLOAD_DIR, random_filename)
                saved_path = default_storage.save(file_path, ContentFile(file.read()))
                full_path = os.path.abspath(saved_path)

                # Save File Object in Database
                material = ProjectMaterial()
                material.user = User.objects.get(id=request.user.id)
                material.name = original_name 
                material.file_type = ext
                material.file = full_path
                material.uploaded_at = timezone.now()
                material.important_tokens = json.dumps([])
                material.save()
                project.materials.add(material)
                project.save()
                process_uploaded_file.delay(
                    material.id,
                    project.id,
                    request.user.id,
                    original_name,
                    full_path
                )
            return JsonResponse({"status": "success"}, safe=False)

        except Project.DoesNotExist:
            return JsonResponse({"error": "Project not found"}, status=404)


class DeleteFileFromProject(APIView):
    def post(self, request, id):
        try:
            project = Project.objects.get(id=id)
            material = ProjectMaterial.objects.get(id=request.data.get('id'))
            if material in project.materials.all():
                deleted_count = mongo_collection.delete_many({
                    "project_id": str(project.id),
                    "file_id": str(material.id)
                }).deleted_count

                project.materials.remove(material)
                project.save()

                if material.file:
                    try:
                        os.remove(material.file)
                    except FileNotFoundError:
                        pass

                material.delete()

                return JsonResponse({
                    "status": "success",
                    "message": f"File and {deleted_count} chunks deleted"
                })

            return JsonResponse({"error": "File not found in project"}, status=400)

        except Project.DoesNotExist:
            return JsonResponse({"error": "Project not found"}, status=404)
        except ProjectMaterial.DoesNotExist:
            return JsonResponse({"error": "File not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
