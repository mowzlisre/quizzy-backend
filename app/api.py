from rest_framework.views import APIView
from django.http import JsonResponse
from .models import Project, ProjectMaterial, Assessment, Attempt
from .serializers import ProjectSerializer, AssessmentSerializer, NewAttemptSerializer
import os, uuid
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from .mongo import mongo_collection
from rest_framework.permissions import IsAuthenticated
import json
from .tasks import process_uploaded_file
import random
from .questions.question_process import extract_important_tokens, get_buffered_counts, generate_topic_list, generate_questions, process_mcq_questions, assign_question_type, filter_final_questions
from .utils import generate_aes_key, aes_encrypt, encrypt_key_with_secret_key, decrypt_key_with_secret_key, aes_decrypt

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


class CreateAssessment(APIView):
    def post(self, request):
        try:
            data = request.data
            project = Project.objects.get(id=data.get('uuid'))
            assessment = Assessment.objects.create(
                id=uuid.uuid4(),
                project=project,
                author=User.objects.get(id=1),
                assessment_title=data.get('title'),
                difficulty="Easy",
                status="Started",
                createdAt=timezone.now()
            )

            materials = ProjectMaterial.objects.filter(id__in=data.get('materials'))
            important_tokens = extract_important_tokens(materials)
            question_counts = data.get("questionCounts")
            concentrations = data.get("concentration")

            buffered_counts = get_buffered_counts(question_counts)
            topics = generate_topic_list(buffered_counts, concentrations, important_tokens)
            generated_questions = generate_questions(topics)
            selective = assign_question_type(generated_questions, buffered_counts)
            selective = process_mcq_questions(selective)
            final_questions = filter_final_questions(selective, question_counts)

            aes_key = generate_aes_key()
            encrypted_questions = aes_encrypt(final_questions, aes_key)
            encrypted_key = encrypt_key_with_secret_key(aes_key)

            # Save encrypted questions and key
            assessment.quiz = encrypted_questions  # Assuming this is a JSONField
            assessment.ek = encrypted_key  # You may need to add this field
            assessment.save()
            return JsonResponse({
                "status": "success",
                "message": "Assessment created and questions generated.",
                "questions_generated": len(final_questions)
            })

        except Exception as e:
            return JsonResponse({"status": "failed", "error": str(e)}, safe=False)


class NewAttempt(APIView):
    def post(self, request):
        try:
            assessment = Assessment.objects.get(id=request.data.get('uuid'))

            encrypted_quiz = assessment.quiz
            encrypted_key = assessment.ek
            aes_key = decrypt_key_with_secret_key(encrypted_key)
            decrypted_quiz = aes_decrypt(
                ciphertext=encrypted_quiz['ciphertext'],
                iv=encrypted_quiz['iv'],
                key=aes_key
            )

            question_type_points = {
                'mcq': 2,
                'fill': 2,
                'shortAnswer': 3,
                'longAnswer': 5
            }

            total_score = 0
            for question in decrypted_quiz:
                points = question_type_points[question['type']]
                question['max_points'] = points
                total_score += points

            # Process the attempt
            attempt = assessment.attempts.create(
                id=uuid.uuid4(),
                max_score=total_score,
                attempt_score=0,
                timeStamp=timezone.now(),
                submission=False,
                timed= True if request.data.get('mode', False) == "timed" else False,
                total_duration=request.data.get('duration', 0),
                partial_credits=request.data.get('partialScoring', False),
                negative_score=request.data.get('negativeScoring', False),
                proctored=request.data.get('proctoredMode', False),
                proctor_meta={},
            )

            attempt = NewAttemptSerializer(attempt).data
            attempt["uuid"] = request.data.get('uuid')
            return JsonResponse(attempt, safe=False)
        
        except Assessment.DoesNotExist:
            return JsonResponse({"status": "failed", "error": "Assessment not found"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "failed", "error": str(e)}, status=500)

class StartAttempt(APIView):
    def post(self, request):
        try:
            assessment = Assessment.objects.get(id=request.data.get('uuid'))
            attempt = assessment.attempts.get(id=request.data.get('id'))
            attempt.start_time = timezone.now()
            attempt.save()


            encrypted_quiz = assessment.quiz
            encrypted_key = assessment.ek
            aes_key = decrypt_key_with_secret_key(encrypted_key)
            decrypted_quiz = aes_decrypt(
                ciphertext=encrypted_quiz['ciphertext'],
                iv=encrypted_quiz['iv'],
                key=aes_key
            )

            question_type_points = {
                'mcq': 2,
                'fill': 2,
                'shortAnswer': 3,
                'longAnswer': 5
            }

            for question in decrypted_quiz:
                points = question_type_points[question['type']]
                question['max_points'] = points
            attempt = NewAttemptSerializer(attempt).data
            attempt["quiz"] = decrypted_quiz
            for i, q in enumerate(attempt["quiz"]):
                q["id"] = i+1
                q['isAnswered'] = False
                q['isMarked'] = False
                q['answer'] = ''
            from pprint import pprint
            pprint(attempt)
            return JsonResponse(attempt, safe=False)
        
        except Assessment.DoesNotExist:
            return JsonResponse({"status": "failed", "error": "Assessment not found"}, status=404)
        except Attempt.DoesNotExist:
            return JsonResponse({"status": "failed", "error": "Attempt not found"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "failed", "error": str(e)}, status=500)