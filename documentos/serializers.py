# documentos/serializers.py
from rest_framework import serializers
from .models import Document, ValidationStep

class ValidationStepInputSerializer(serializers.Serializer):
    order = serializers.IntegerField()
    approver_user_id = serializers.UUIDField()

class DocumentInfoSerializer(serializers.Serializer):
    name = serializers.CharField()
    mime_type = serializers.CharField()
    size_bytes = serializers.IntegerField(required=False)
    bucket_key = serializers.CharField()

class EntitySerializer(serializers.Serializer):
    entity_type = serializers.CharField()
    entity_id = serializers.UUIDField()

class ValidationFlowSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    steps = ValidationStepInputSerializer(many=True)

class DocumentCreateSerializer(serializers.Serializer):
    company_id = serializers.UUIDField()
    entity = EntitySerializer()
    document = DocumentInfoSerializer()
    validation_flow = ValidationFlowSerializer(required=False)
