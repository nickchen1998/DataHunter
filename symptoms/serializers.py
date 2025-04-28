from rest_framework.serializers import ModelSerializer


class SymptomSerializer(ModelSerializer):

    class Meta:
        model = "symptoms.Symptom"
        fields = "__all__"
        extra_kwargs = {
            "question_embeddings": {"write_only": True},
        }
