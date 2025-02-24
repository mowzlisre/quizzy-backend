from rest_framework import serializers
from .models import Project, ProjectMaterial, MaterialChunks, Attempt, Assessment
from .utils import time_since
class ProjectMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMaterial
        fields = '__all__'

class MaterialChunksSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialChunks
        fields = '__all__'

class AttemptSerializer(serializers.ModelSerializer):
    created = serializers.SerializerMethodField()

    class Meta:
        model = Attempt
        fields = '__all__'

    def get_created(self, obj):
        return time_since(obj.timeStamp)

class AssessmentSerializer(serializers.ModelSerializer):
    created = serializers.SerializerMethodField()
    recentAttempt = serializers.SerializerMethodField()
    author_name = serializers.CharField(source="author.username", read_only=True)
    attempts = AttemptSerializer(many=True, read_only=True)

    class Meta:
        model = Assessment
        fields = '__all__'
        extra_fields = ['author_name']

    def get_created(self, obj):
        return obj.created
    
    def get_recentAttempt(self, obj):
        """Returns the most recent attempt based on timestamp"""
        recent_attempt = obj.attempts.order_by('-timeStamp').first()
        return time_since(recent_attempt.timeStamp)

class ProjectSerializer(serializers.ModelSerializer):
    materials = ProjectMaterialSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = '__all__'
