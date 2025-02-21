from rest_framework import serializers
from .models import Project, ProjectMaterial, MaterialChunks, Attempt, Assessment

class ProjectMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMaterial
        fields = '__all__'

class MaterialChunksSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialChunks
        fields = '__all__'

class AttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attempt
        fields = '__all__'

class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = '__all__'

class ProjectSerializer(serializers.ModelSerializer):
    materials = ProjectMaterialSerializer(many=True, read_only=True)  # Nested representation

    class Meta:
        model = Project
        fields = '__all__'
