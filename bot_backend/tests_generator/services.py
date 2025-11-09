"""Сервисный слой для генерации тестов"""
from typing import List, Dict
from integrations.ai_client import get_ai_client
from .models import GeneratedTest


class TestGeneratorService:
    """Сервис для генерации тестовых вопросов"""
    
    def __init__(self):
        self.ai_client = get_ai_client()
    
    def generate_test(self, questions_count: int = 10) -> Dict:
        """
        Генерация теста с вопросами
        
        Args:
            questions_count: Количество вопросов (по умолчанию 10)
            
        Returns:
            dict: Сгенерированный тест с вопросами
        """
        try:
            # Получение случайных точек из Qdrant
            # Берем больше точек для лучшего контекста
            points = self.ai_client.get_random_points(count=questions_count)
            
            if not points:
                raise Exception("Не удалось получить данные из Qdrant. Возможно, база данных пуста.")
            
            # Генерация вопросов на основе точек
            questions = self.ai_client.generate_test_questions(points, count=questions_count)
            
            # Сохранение теста в БД
            test = GeneratedTest.objects.create(
                questions_count=len(questions),
                questions=questions
            )
            
            return {
                "id": str(test.id),
                "questions_count": test.questions_count,
                "questions": test.questions,
                "created_at": test.created_at
            }
            
        except Exception as e:
            raise Exception(f"Ошибка при генерации теста: {str(e)}")
    
    def get_test(self, test_id: str) -> GeneratedTest:
        """
        Получить тест по ID
        
        Args:
            test_id: ID теста
            
        Returns:
            GeneratedTest: Объект теста
        """
        return GeneratedTest.objects.get(id=test_id)
    
    def get_tests_history(self, limit: int = 20) -> List[GeneratedTest]:
        """
        Получить историю сгенерированных тестов
        
        Args:
            limit: Максимальное количество записей
            
        Returns:
            List[GeneratedTest]: Список тестов
        """
        return GeneratedTest.objects.all()[:limit]


def get_test_generator_service() -> TestGeneratorService:
    """Получить экземпляр сервиса генерации тестов"""
    return TestGeneratorService()
