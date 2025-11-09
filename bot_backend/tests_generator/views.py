"""Views для модуля генерации тестов"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import GeneratedTest
from .serializers import (
    TestGenerateRequestSerializer,
    TestResponseSerializer,
    TestListSerializer
)
from .services import get_test_generator_service


class GenerateTestView(APIView):
    """API endpoint для генерации теста"""
    
    def post(self, request):
        """
        Сгенерировать новый тест
        """
        # Валидация входных данных
        serializer = TestGenerateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        questions_count = serializer.validated_data.get('questions_count', 10)
        
        # Генерация теста через сервис
        service = get_test_generator_service()
        try:
            result = service.generate_test(questions_count)
            return Response(
                result,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestDetailView(APIView):
    """API endpoint для получения теста"""
    
    def get(self, request, test_id):
        """
        Получить тест по ID
        """
        test = get_object_or_404(GeneratedTest, id=test_id)
        serializer = TestResponseSerializer(test)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TestHistoryView(APIView):
    """API endpoint для получения истории тестов"""
    
    def get(self, request):
        """
        Получить историю сгенерированных тестов
        """
        service = get_test_generator_service()
        tests = service.get_tests_history()
        
        serializer = TestListSerializer(tests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
