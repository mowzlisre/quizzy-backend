# materials/tasks.py
import subprocess
import json
from celery import shared_task
from django.utils import timezone
from .models import Project, ProjectMaterial
from .mongo import mongo_collection, chunk_text
from app.preprocess.text_extract import extract_text
import requests

@shared_task
def process_uploaded_file(material_id, project_id, user_id, original_name, full_path):
    project = Project.objects.get(id=project_id)
    material = ProjectMaterial.objects.get(id=material_id)

    extracted_text = extract_text(full_path, original_name)
    if not extracted_text:
        return  # or handle error

    # chunk text
    chunk_size = 500
    chunks, text = chunk_text(extracted_text, chunk_size)

    # get topics
    res = requests.post("http://localhost:8001/generate/topics", json={"context": text})
    topics = res.json() if isinstance(res.json(), list) else []
    important_tokens = list(set(topics))
    material.important_tokens = json.dumps(important_tokens)
    material.save()

    # Send chunks to embed_chunks.py
    process = subprocess.Popen(
        ["python", "app/embed_chunks.py"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    input_data = json.dumps(chunks).encode()
    stdout, stderr = process.communicate(input=input_data)

    if process.returncode != 0:
        # Log error somewhere or raise
        print("Embedding subprocess error:", stderr.decode())
        return

    embeddings = json.loads(stdout)  # list of embedding vectors

    # Insert to Mongo
    docs = []
    for i, chunk in enumerate(chunks):
        docs.append({
            "project_id": str(project.id),
            "file_id": str(material.id),
            "file_name": original_name,
            "chunk_index": i,
            "chunk_text": chunk,
            "created_at": timezone.now(),
            "embeddings": embeddings[i]
        })
    if docs:
        mongo_collection.insert_many(docs)
