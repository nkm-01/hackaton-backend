from django.contrib import admin
from .models import Consultation, ConsultationDocument


class ConsultationDocumentInline(admin.TabularInline):
    """Инлайн для отображения документов в консультации"""
    model = ConsultationDocument
    extra = 0
    fields = ['order', 'document']
    readonly_fields = ['order', 'document']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    """Админка для просмотра истории консультаций"""
    
    list_display = [
        'created_at',
        'query_preview',
        'response_time',
        'documents_count',
    ]
    
    list_filter = [
        'created_at',
    ]
    
    search_fields = [
        'query',
        'response',
    ]
    
    readonly_fields = [
        'id',
        'query',
        'response',
        'created_at',
        'response_time',
        'sources',
        'documents',
    ]
    
    inlines = [ConsultationDocumentInline]
    
    fieldsets = (
        ('Информация о запросе', {
            'fields': ('id', 'query', 'created_at')
        }),
        ('Ответ', {
            'fields': ('response', 'response_time')
        }),
        ('Источники', {
            'fields': ('sources',),
            'classes': ('collapse',)
        }),
    )
    
    def query_preview(self, obj):
        """Превью вопроса"""
        if len(obj.query) > 80:
            return obj.query[:80] + "..."
        return obj.query
    query_preview.short_description = "Вопрос"  # type: ignore
    
    def documents_count(self, obj):
        """Количество связанных документов"""
        return obj.documents.count()
    documents_count.short_description = "Документов"  # type: ignore
    
    def has_add_permission(self, request):
        """Запретить создание консультаций через админку"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Разрешить удаление старых консультаций"""
        return True


@admin.register(ConsultationDocument)
class ConsultationDocumentAdmin(admin.ModelAdmin):
    """Админка для связи консультаций с документами"""
    
    list_display = ['consultation', 'document', 'order']
    list_filter = ['consultation__created_at']
    search_fields = ['consultation__query', 'document__title']
    
    def has_add_permission(self, request):
        return False
