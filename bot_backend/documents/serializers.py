"""Сериализаторы для модуля документов"""
from rest_framework import serializers
from .models import Document


class DocumentListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка документов"""
    
    file_size_display = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'file_type',
            'file_size',
            'file_size_display',
            'file_url',
            'upload_date',
            'status',
            'pages_count',
        ]
        read_only_fields = fields
    
    def get_file_size_display(self, obj):
        """Получить размер файла в человекочитаемом формате"""
        return obj.get_file_size_display()
    
    def get_file_url(self, obj):
        """Получить URL файла"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации о документе"""
    
    file_size_display = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'file',
            'file_type',
            'file_size',
            'file_size_display',
            'file_url',
            'upload_date',
            'status',
            'error_message',
            'pages_count',
        ]
        read_only_fields = [
            'id',
            'file_size',
            'upload_date',
            'status',
            'error_message',
            'pages_count',
        ]
    
    def get_file_size_display(self, obj):
        """Получить размер файла в человекочитаемом формате"""
        return obj.get_file_size_display()
    
    def get_file_url(self, obj):
        """Получить URL файла"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Сериализатор для загрузки документа"""
    
    class Meta:
        model = Document
        fields = [
            'title',
            'file',
        ]
    
    def validate_file(self, value):
        """Валидация загружаемого файла"""
        # Проверка расширения файла
        allowed_extensions = ['pdf', 'rtf', 'docx', 'txt']
        ext = value.name.split('.')[-1].lower()
        
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"Недопустимый формат файла. Разрешены: {', '.join(allowed_extensions)}"
            )
        
        # Проверка размера файла (максимум 100 МБ)
        max_size = 100 * 1024 * 1024  # 100 MB
        if value.size > max_size:
            raise serializers.ValidationError(
                "Размер файла не должен превышать 100 МБ"
            )
        
        return value
    
    def create(self, validated_data):
        """Создание документа с автоматическим определением типа и размера"""
        file = validated_data['file']
        
        # Определение типа файла
        file_type = file.name.split('.')[-1].lower()
        
        # Создание документа
        document = Document.objects.create(
            title=validated_data.get('title', file.name),
            file=file,
            file_type=file_type,
            file_size=file.size,
            status='pending'
        )
        
        return document


class DocumentStatusSerializer(serializers.ModelSerializer):
    """Сериализатор для статуса обработки документа"""
    
    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'status',
            'error_message',
        ]
        read_only_fields = fields
