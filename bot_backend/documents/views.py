"""Views для модуля документов"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
import threading

from .models import Document
from .serializers import (
    DocumentListSerializer,
    DocumentDetailSerializer,
    DocumentUploadSerializer,
    DocumentStatusSerializer
)
from .services import get_document_service


class DocumentViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с документами"""
    
    queryset = Document.objects.all()
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'list':
            return DocumentListSerializer
        elif self.action == 'create':
            return DocumentUploadSerializer
        elif self.action == 'status':
            return DocumentStatusSerializer
        return DocumentDetailSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Загрузка нового документа
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        
        # Запуск обработки документа в фоне
        service = get_document_service()
        thread = threading.Thread(target=service.process_document, args=(document,))
        thread.daemon = True
        thread.start()
        
        # Возврат информации о документе
        detail_serializer = DocumentDetailSerializer(document, context={'request': request})
        return Response(
            detail_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    def destroy(self, request, *args, **kwargs):
        """
        Удаление документа
        """
        document = self.get_object()
        service = get_document_service()
        
        try:
            service.delete_document(document)
            return Response(
                {"message": "Документ успешно удален"},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка при удалении документа: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        Получить статус обработки документа
        """
        document = self.get_object()
        serializer = DocumentStatusSerializer(document)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reindex(self, request, pk=None):
        """
        Переиндексировать документ
        """
        document = self.get_object()
        
        if document.status == 'processing':
            return Response(
                {"error": "Документ уже обрабатывается"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Запуск переиндексации в фоне
        service = get_document_service()
        thread = threading.Thread(target=service.reindex_document, args=(document,))
        thread.daemon = True
        thread.start()
        
        return Response(
            {"message": "Переиндексация запущена"},
            status=status.HTTP_200_OK
        )
