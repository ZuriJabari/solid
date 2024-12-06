from rest_framework import serializers
from decimal import Decimal

class ErrorSerializer(serializers.Serializer):
    """Common error response serializer"""
    error = serializers.CharField()
    code = serializers.CharField(required=False)
    details = serializers.DictField(required=False)

class MessageSerializer(serializers.Serializer):
    """Common message response serializer"""
    message = serializers.CharField()

class StatusSerializer(serializers.Serializer):
    """Common status response serializer"""
    status = serializers.CharField()
    message = serializers.CharField(required=False)

class SuccessSerializer(serializers.Serializer):
    """Common success response serializer"""
    success = serializers.BooleanField(default=True)
    message = serializers.CharField(required=False)

class PaginatedResponseSerializer(serializers.Serializer):
    """Common paginated response serializer"""
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = serializers.ListField()

class ValidationErrorSerializer(serializers.Serializer):
    """Common validation error response serializer"""
    field_errors = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField())
    )
    non_field_errors = serializers.ListField(
        child=serializers.CharField(),
        required=False
    ) 