# materials/tasks.py
from celery import shared_task
from .models import Project, ProjectMaterial
from django.contrib.auth.models import User
from sentence_transformers import SentenceTransformer
from django.utils import timezone
import requests
from .mongo import mongo_collection, chunk_text
from app.preprocess.text_extract import extract_text
import json


@shared_task
def process_uploaded_file(material_id, project_id, user_id, original_name, full_path):
    project = Project.objects.get(id=project_id)
    material = ProjectMaterial.objects.get(id=material_id)

    extracted_text = extract_text(full_path, original_name)

    if extracted_text:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        chunk_size = 500  
        chunks, text = chunk_text(extracted_text, chunk_size)
        res = requests.post("http://localhost:8001/generate/topics", json={"context": text})
        if isinstance(res.json(), list):
            topics = res.json()
        important_tokens = list(set(topics))
        material.important_tokens = json.dumps(important_tokens)
        # material.important_tokens = json.dumps([])
        material.save()
        mongo_collection.insert_many([
            {
                "project_id": str(project.id),
                "file_id": str(material.id),
                "file_name": original_name,
                "chunk_index": i,
                "chunk_text": chunk,
                "created_at": timezone.now(),
                "embeddings" : model.encode(chunk).tolist()
            }
            for i, chunk in enumerate(chunks)
        ])
