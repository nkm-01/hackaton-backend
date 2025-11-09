from django.contrib import admin
from django.utils.html import format_html
from .models import GeneratedTest


@admin.register(GeneratedTest)
class GeneratedTestAdmin(admin.ModelAdmin):
    """Админка для просмотра сгенерированных тестов"""
    
    list_display = [
        'created_at',
        'questions_count',
        'preview_first_question',
    ]
    
    list_filter = [
        'created_at',
        'questions_count',
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'questions_count',
        'questions_display',
    ]
    
    fieldsets = (
        ('Информация о тесте', {
            'fields': ('id', 'created_at', 'questions_count')
        }),
        ('Вопросы', {
            'fields': ('questions_display',)
        }),
    )
    
    def preview_first_question(self, obj):
        """Превью первого вопроса"""
        if obj.questions and len(obj.questions) > 0:
            question = obj.questions[0].get('question', '')
            if len(question) > 80:
                return question[:80] + "..."
            return question
        return "Нет вопросов"
    preview_first_question.short_description = "Первый вопрос"  # type: ignore
    
    def questions_display(self, obj):
        """Красивое отображение вопросов"""
        if not obj.questions:
            return "Нет вопросов"
        
        html = []
        for i, q in enumerate(obj.questions, 1):
            html.append(f'<div style="margin-bottom: 20px; padding: 10px; background-color: #f5f5f5; border-radius: 5px;">')
            html.append(f'<strong>Вопрос {i}:</strong> {q.get("question", "")}<br>')
            html.append('<strong>Варианты:</strong><ul>')
            
            options = q.get('options', [])
            correct = q.get('correct', 0)
            
            for j, option in enumerate(options):
                style = "color: green; font-weight: bold;" if j == correct else ""
                marker = "✓" if j == correct else "○"
                html.append(f'<li style="{style}">{marker} {option}</li>')
            
            html.append('</ul></div>')
        
        return format_html(''.join(html))
    questions_display.short_description = "Вопросы теста"  # type: ignore
    
    def has_add_permission(self, request):
        """Запретить создание тестов через админку (только через API)"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Разрешить удаление старых тестов"""
        return True
