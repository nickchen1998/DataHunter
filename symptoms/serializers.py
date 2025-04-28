from rest_framework.serializers import ModelSerializer
from symptoms.models import Symptom


class SymptomSerializer(ModelSerializer):

    class Meta:
        model = Symptom
        fields = "__all__"
        extra_kwargs = {
            "question_embeddings": {"write_only": True},
        }
