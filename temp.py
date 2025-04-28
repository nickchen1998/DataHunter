import json
from symptoms.models import Symptom
from datetime import datetime


def temp():
    with open("symptoms.json", "r", encoding="utf-8") as f:
        datas = json.load(f)

    for data in datas:
        if not Symptom.objects.filter(subject_id=data["subject_id"]).exists():
            try:
                Symptom.objects.create(
                    subject_id=data["subject_id"],
                    department=data["department"],
                    symptom=data["symptom"],
                    question=data["question"],
                    answer=data["answer"],
                    gender=data["gender"],
                    question_time=datetime.fromisoformat(data["question_time"]["$date"]),
                    answer_time=datetime.fromisoformat(data["answer_time"]["$date"]),
                    question_embeddings=data["question_embeddings"],
                )
            except:
                continue
