"""Сериализаторы для модуля генерации тестов"""
from rest_framework import serializers
from .models import GeneratedTest


class TestGenerateRequestSerializer(serializers.Serializer):
    """Сериализатор для запроса генерации теста"""
    questions_count = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=20,
        help_text="Количество вопросов в тесте (1-20)"
    )


class QuestionSerializer(serializers.Serializer):
    """Сериализатор для вопроса"""
    question = serializers.CharField()
    options = serializers.ListField(
        child=serializers.CharField(),
        min_length=2,
        max_length=10
    )
    correct = serializers.IntegerField(min_value=0)


class TestResponseSerializer(serializers.ModelSerializer):
    """Сериализатор для ответа с тестом"""
    questions = QuestionSerializer(many=True)
    
    class Meta:
        model = GeneratedTest
        fields = [
            'id',
            'questions_count',
            'questions',
            'created_at'
        ]
        read_only_fields = fields


class TestListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка тестов (краткая информация)"""
    
    class Meta:
        model = GeneratedTest
        fields = [
            'id',
            'questions_count',
            'created_at'
        ]
        read_only_fields = fields
