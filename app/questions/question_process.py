import requests
import time
import json
import random
from app.rag.faiss import fetchRelevantDocuments

def generate_valid_question(context, retries=5, delay=0):
    for attempt in range(retries):
        try:
            response = requests.post("http://localhost:8001/generate/qa", json={"context": context})
            if response.status_code != 200:
                continue
            data = response.json()
            question = data.get("question")
            answer = data.get("answer")
            if not question or question.strip() in ["", "No Answer", None]:
                continue
            if not answer or answer.strip() in ["", "No Answer", None]:
                continue
            return {
                "question": question,
                "answer": answer,
                "context": context
            }
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
        time.sleep(delay)
    return None

def assign_question_type(generated_questions, question_counts):
    # Sort questions by answer length (longest first)
    sorted_questions = sorted(generated_questions, key=lambda q: len(q.get("answer", "").split()), reverse=True)

    # Create a flat list of types to assign, based on counts
    types_to_assign = []
    for q_type, count in question_counts.items():
        types_to_assign.extend([q_type] * count)

    # Assign types in the requested order
    for i, question in enumerate(sorted_questions):
        if i < len(types_to_assign):
            question["type"] = types_to_assign[i]
        else:
            question["type"] = "shortAnswer"  # fallback type if more questions than counts

    return sorted_questions

def extract_important_tokens(materials):
        tokens = []
        for material in materials:
            tokens.extend(json.loads(material.important_tokens))
        return tokens

def get_buffered_counts(question_counts):
    return {
        qtype: count + 2 if count > 0 else 0
        for qtype, count in question_counts.items()
    }

def generate_topic_list(buffered_counts, concentrations, important_tokens):
    total_questions = sum(buffered_counts.values())
    topics = []

    for _ in range(total_questions):
        if concentrations and important_tokens:
            topic_source = random.choices(["concentration", "important"], weights=[0.7, 0.3])[0]
            topic = random.choice(concentrations if topic_source == "concentration" else important_tokens)
        elif concentrations:
            topic = random.choice(concentrations)
        else:
            topic = random.choice(important_tokens)
        topics.append(topic)
    return topics

def generate_questions(topics):
    questions = []
    for topic in topics:
        context_results = fetchRelevantDocuments(topic, 5).get("results", [])
        if not context_results:
            continue
        context = random.choice(context_results)["text"]
        question_data = generate_valid_question(context)
        if question_data:
            questions.append(question_data)
    return questions

def process_mcq_questions(questions):
    for question in questions:
        if question.get("type") == "mcq":
            attempt = 0
            while attempt < 5:
                try:
                    response = requests.post("http://localhost:8001/generate/mcq", json={
                        "question": question["question"],
                        "context": question["context"],
                        "answer": question["answer"]
                    })
                    mcq = response.json()

                    if (
                        isinstance(mcq.get("options"), list) and
                        all(isinstance(opt, str) for opt in mcq["options"]) and
                        len(set(mcq["options"])) >= 4 and
                        mcq.get("answer") in mcq["options"]
                    ):
                        question.update(mcq)
                        break
                except Exception as e:
                    pass
                attempt += 1
                time.sleep(1)
    return questions


def filter_final_questions(questions, original_counts):
    final = []
    for qtype, count in original_counts.items():
        typed = [q for q in questions if q.get("type") == qtype]
        final.extend(typed[:count])
    return final