from django.db import models
import uuid


class GeneratedTest(models.Model):
    """Модель для хранения сгенерированных тестов"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    questions_count = models.IntegerField(
        verbose_name="Количество вопросов",
        default=10
    )
    questions = models.JSONField(
        verbose_name="Вопросы и варианты ответов",
        default=list
    )
    
    class Meta:
        verbose_name = "Сгенерированный тест"
        verbose_name_plural = "Сгенерированные тесты"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Тест от {self.created_at.strftime('%d.%m.%Y %H:%M')} ({self.questions_count} вопросов)"
