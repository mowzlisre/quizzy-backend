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
import numpy as np
from .mongo import mongo_collection
import faiss

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
                material.save()
                project.materials.add(material)
                project.save()
                
                extracted_text = extract_text(full_path, original_name)

                if extracted_text:
                    chunk_size = 500  
                    chunks = chunk_text(extracted_text, chunk_size)
                    model = SentenceTransformer("all-MiniLM-L6-v2")
                    important_tokens = performTFIDF(full_path)

                    mongo_collection.insert_many([
                        {
                            "project_id": str(project.id),
                            "file_id": str(material.id),
                            "file_name": original_name,
                            "chunk_index": i,
                            "chunk_text": chunk,
                            "important_tokens" : important_tokens,
                            "created_at": timezone.now(),
                            "embeddings" : model.encode(chunk).tolist()
                        }
                        for i, chunk in enumerate(chunks)
                    ])

            return JsonResponse({"status": "success"})

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
        
class FetchRelevantChunks(APIView):
    def get(self, request):
        model = SentenceTransformer("all-MiniLM-L6-v2")

        # 3. Fetch All Stored Embeddings from MongoDB
        documents = list(mongo_collection.find({}, {"_id": 1, "embedding": 1}))
        if not documents:
            print("No embeddings found in MongoDB.")
            exit()

        embeddings = np.array([doc["embedding"] for doc in documents]).astype("float32")
        ids = np.array([str(doc["_id"]) for doc in documents])  # Store MongoDB ObjectIds

        # 4. Create FAISS Index
        dimension = 384  # The embedding dimension for 'all-MiniLM-L6-v2'
        index = faiss.IndexFlatL2(dimension)  # L2 distance (Euclidean)
        index.add(embeddings)  # Add vectors to FAISS index

        # 5. Encode Query into an Embedding
        query = "Who is mafia"
        query_embedding = np.array(model.encode(query)).astype("float32").reshape(1, -1)

        # 6. Perform FAISS Search
        k = 5  # Number of results to retrieve
        distances, indices = index.search(query_embedding, k)

        # 7. Retrieve Matched Documents from MongoDB
        matched_ids = [ids[i] for i in indices[0]]  # Get corresponding MongoDB ObjectIds
        matched_docs = list(mongo_collection.find({"_id": {"$in": [ObjectId(id) for id in matched_ids]}}))

        # 8. Print the Most Relevant Documents
        for doc in matched_docs:
            print(doc["text"])

        print("Search complete.")