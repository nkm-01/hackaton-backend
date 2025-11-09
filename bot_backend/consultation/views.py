from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Consultation
from .serializers import (
    ConsultationQuerySerializer,
    ConsultationResponseSerializer,
    ConsultationListSerializer
)
from .services import ConsultationService


class AskConsultationView(APIView):
    """API endpoint для отправки вопроса консультанту"""
    
    def post(self, request):
        """
        Отправить вопрос и получить консультацию
        """
        # Валидация входных данных
        serializer = ConsultationQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        query = serializer.validated_data['query']
        
        # Обработка запроса через сервис
        service = ConsultationService()
        try:
            result = service.ask_question(query)
            return Response(
                result,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConsultationHistoryView(APIView):
    """API endpoint для получения истории консультаций"""
    
    def get(self, request):
        """
        Получить список всех консультаций
        """
        service = ConsultationService()
        consultations = service.get_history()
        
        serializer = ConsultationListSerializer(consultations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ConsultationDetailView(APIView):
    """API endpoint для получения деталей консультации"""
    
    def get(self, request, consultation_id):
        """
        Получить детальную информацию о консультации
        """
        consultation = get_object_or_404(Consultation, id=consultation_id)
        serializer = ConsultationResponseSerializer(consultation)
        return Response(serializer.data, status=status.HTTP_200_OK)
