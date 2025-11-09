from django.db import models
import uuid
import os


def document_upload_path(instance, filename):
    """Генерация пути для загрузки документа"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('documents', filename)


class Document(models.Model):
    """Модель документа"""
    
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('rtf', 'RTF'),
        ('docx', 'DOCX'),
        ('txt', 'TXT'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает обработки'),
        ('processing', 'Обрабатывается'),
        ('processed', 'Обработан'),
        ('error', 'Ошибка'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name="Название документа")
    file = models.FileField(
        upload_to=document_upload_path,
        verbose_name="Файл документа"
    )
    file_type = models.CharField(
        max_length=10,
        choices=FILE_TYPE_CHOICES,
        verbose_name="Тип файла"
    )
    file_size = models.BigIntegerField(
        verbose_name="Размер файла (байт)",
        null=True,
        blank=True
    )
    upload_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата загрузки"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус обработки"
    )
    error_message = models.TextField(
        blank=True,
        verbose_name="Сообщение об ошибке"
    )
    pages_count = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Количество страниц"
    )
    
    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"
        ordering = ["-upload_date"]
    
    def __str__(self):
        return self.title
    
    def get_file_size_display(self):
        """Получить размер файла в человекочитаемом формате"""
        if not self.file_size:
            return "Неизвестно"
        
        size = self.file_size
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} ТБ"
