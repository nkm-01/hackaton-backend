"""Сервисный слой для работы с консультациями"""
import time
from typing import Dict, List

from integrations.ai_client import get_ai_client
from .models import Consultation


class ConsultationService:
    """Сервис для обработки консультационных запросов"""
    
    def __init__(self):
        self.ai_client = get_ai_client()
    
    def ask_question(self, query: str) -> Dict:
        """
        Отправить вопрос в AI модуль и получить ответ
        
        Args:
            query: Текст вопроса
            
        Returns:
            dict: Словарь с ответом, источниками и временем обработки
        """
        start_time = time.time()
        
        try:
            # Отправка запроса в AI модуль
            result = self.ai_client.ask_question(query)
            
            response_time = time.time() - start_time
            
            # Сохранение консультации в БД
            consultation = Consultation.objects.create(
                query=query,
                response=result.response,
                response_time=response_time,
                sources=result.sources
            )
            
            return {
                "id": str(consultation.id),
                "query": consultation.query,
                "response": consultation.response,
                "sources": consultation.sources,
                "response_time": response_time,
                "created_at": consultation.created_at
            }
            
        except Exception as e:
            raise Exception(f"Ошибка при обращении к AI модулю: {str(e)}")
    
    def get_history(self, limit: int = 50):
        """
        Получить историю консультаций
        
        Args:
            limit: Максимальное количество записей
            
        Returns:
            QuerySet: Список консультаций
        """
        return Consultation.objects.all()[:limit]
    
    def get_consultation(self, consultation_id: str):
        """
        Получить детали конкретной консультации
        
        Args:
            consultation_id: ID консультации
            
        Returns:
            Consultation: Объект консультации
        """
        return Consultation.objects.get(id=consultation_id)

