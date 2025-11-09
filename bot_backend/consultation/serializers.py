"""Сериализаторы для модуля консультаций"""
from rest_framework import serializers
from .models import Consultation, ConsultationDocument


class ConsultationDocumentSerializer(serializers.ModelSerializer):
    """Сериализатор для документов в консультации"""
    document_id = serializers.UUIDField(source='document.id', read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)
    
    class Meta:
        model = ConsultationDocument
        fields = ['order', 'document_id', 'document_title']


class ConsultationQuerySerializer(serializers.Serializer):
    """Сериализатор для входящего запроса консультации"""
    query = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=5000,
        help_text="Текст вопроса для консультации"
    )


class ConsultationResponseSerializer(serializers.ModelSerializer):
    """Сериализатор для ответа консультации"""
    
    related_documents = ConsultationDocumentSerializer(
        source='consultationdocument_set',
        many=True,
        read_only=True
    )
    
    class Meta:
        model = Consultation
        fields = [
            'id', 
            'query', 
            'response', 
            'sources', 
            'response_time', 
            'created_at',
            'related_documents'
        ]
        read_only_fields = fields


class ConsultationListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка консультаций (краткая информация)"""
    
    query_preview = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Consultation
        fields = [
            'id',
            'query_preview',
            'created_at',
            'response_time',
            'documents_count'
        ]
        read_only_fields = fields
    
    def get_query_preview(self, obj):
        """Получить превью вопроса (первые 100 символов)"""
        if len(obj.query) > 100:
            return obj.query[:100] + "..."
        return obj.query
    
    def get_documents_count(self, obj):
        """Получить количество связанных документов"""
        return obj.documents.count()
