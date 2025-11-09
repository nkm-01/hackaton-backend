from django.db import models
import uuid


class ConsultationDocument(models.Model):
    """Промежуточная модель для связи консультации с документами"""
    
    consultation = models.ForeignKey(
        'Consultation',
        on_delete=models.CASCADE,
        verbose_name="Консультация"
    )
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        verbose_name="Документ"
    )
    order = models.PositiveIntegerField(
        verbose_name="Номер в чате",
        help_text="Порядковый номер документа в списке источников"
    )
    
    class Meta:
        verbose_name = "Документ консультации"
        verbose_name_plural = "Документы консультации"
        ordering = ['order']
        unique_together = [['consultation', 'document']]
    
    def __str__(self):
        return f"{self.document.title} (#{self.order})"


class Consultation(models.Model):
    """Модель для хранения истории консультаций"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.TextField(verbose_name="Вопрос")
    response = models.TextField(verbose_name="Ответ", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    response_time = models.FloatField(
        verbose_name="Время обработки (сек)", 
        null=True, 
        blank=True
    )
    sources = models.JSONField(
        verbose_name="Источники информации", 
        default=list,
        blank=True
    )
    documents = models.ManyToManyField(
        'documents.Document',
        through='ConsultationDocument',
        related_name='consultations',
        verbose_name="Связанные документы",
        blank=True
    )
    
    class Meta:
        verbose_name = "Консультация"
        verbose_name_plural = "Консультации"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Консультация от {self.created_at.strftime('%d.%m.%Y %H:%M')}"
