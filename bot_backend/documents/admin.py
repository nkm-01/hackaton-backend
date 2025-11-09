from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.shortcuts import redirect
from django.contrib import messages
import threading
from .models import Document
from .services import get_document_service


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Админка для управления документами"""
    
    def get_urls(self):
        """Добавление custom URLs для действий с документами"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/rescan/',
                self.admin_site.admin_view(self.rescan_document_view),
                name='documents_document_rescan',
            ),
            path(
                '<path:object_id>/reindex/',
                self.admin_site.admin_view(self.reindex_document_view),
                name='documents_document_reindex',
            ),
        ]
        return custom_urls + urls
    
    def rescan_document_view(self, request, object_id):
        """View для пересканирования документа"""
        document = Document.objects.get(pk=object_id)
        
        if document.status == 'processing':
            messages.warning(request, f"Документ '{document.title}' уже обрабатывается")
        else:
            # Сброс статуса если была ошибка
            if document.status == 'error':
                document.status = 'pending'
                document.error_message = ''
                document.save()
            
            # Запуск обработки в фоне
            service = get_document_service()
            thread = threading.Thread(target=service.process_document, args=(document,))
            thread.daemon = True
            thread.start()
            
            messages.success(request, f"Запущено пересканирование документа '{document.title}'")
        
        return redirect('admin:documents_document_change', object_id)
    
    def reindex_document_view(self, request, object_id):
        """View для переиндексации документа"""
        document = Document.objects.get(pk=object_id)
        
        if document.status == 'processing':
            messages.warning(request, f"Документ '{document.title}' уже обрабатывается")
        else:
            # Запуск переиндексации в фоне
            service = get_document_service()
            thread = threading.Thread(target=service.reindex_document, args=(document,))
            thread.daemon = True
            thread.start()
            
            messages.success(request, f"Запущена переиндексация документа '{document.title}'")
        
        return redirect('admin:documents_document_change', object_id)
    
    list_display = [
        'title',
        'file_type',
        'status_colored',
        'file_size_display',
        'pages_count',
        'upload_date',
    ]
    
    list_filter = [
        'status',
        'file_type',
        'upload_date',
    ]
    
    search_fields = [
        'title',
    ]
    
    readonly_fields = [
        'id',
        'upload_date',
        'file_size',
        'pages_count',
        'action_buttons',
    ]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'title', 'file', 'file_type')
        }),
        ('Метаданные', {
            'fields': ('file_size', 'pages_count', 'upload_date')
        }),
        ('Статус обработки', {
            'fields': ('status', 'error_message', 'action_buttons')
        }),
    )
    
    actions = ['reindex_documents', 'process_documents', 'retry_failed_documents']
    
    def save_model(self, request, obj, form, change):
        """Переопределение сохранения для автоматической обработки"""
        is_new = obj._state.adding
        super().save_model(request, obj, form, change)
        
        # Если это новый документ, запускаем обработку
        if is_new:
            service = get_document_service()
            thread = threading.Thread(target=service.process_document, args=(obj,))
            thread.daemon = True
            thread.start()
            
            self.message_user(
                request,
                f"Документ '{obj.title}' загружен и отправлен на обработку"
            )
    
    def delete_model(self, request, obj):
        """Переопределение удаления для очистки Qdrant"""
        service = get_document_service()
        try:
            service.delete_document(obj)
            self.message_user(
                request,
                f"Документ '{obj.title}' удален вместе с данными из Qdrant"
            )
        except Exception as e:
            self.message_user(
                request,
                f"Ошибка при удалении документа: {str(e)}",
                level='error'
            )
    
    def delete_queryset(self, request, queryset):
        """Переопределение массового удаления для очистки Qdrant"""
        service = get_document_service()
        count = 0
        errors = 0
        
        for document in queryset:
            try:
                service.delete_document(document)
                count += 1
            except Exception as e:
                errors += 1
                print(f"Error deleting document {document.id}: {str(e)}")
        
        self.message_user(
            request,
            f"Удалено документов: {count}. Ошибок: {errors}"
        )
    
    def status_colored(self, obj):
        """Цветной статус"""
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'processed': 'green',
            'error': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = "Статус"  # type: ignore
    
    def file_size_display(self, obj):
        """Размер файла в человекочитаемом формате"""
        return obj.get_file_size_display()
    file_size_display.short_description = "Размер"  # type: ignore
    
    def action_buttons(self, obj):
        """Кнопки действий для документа"""
        if obj.pk:
            buttons = []
            
            # Кнопка пересканирования (для всех статусов кроме processing)
            if obj.status != 'processing':
                rescan_url = reverse('admin:documents_document_rescan', args=[obj.pk])
                buttons.append(
                    f'<a class="button" href="{rescan_url}" '
                    f'style="background-color: #417690; color: white; padding: 5px 10px; '
                    f'text-decoration: none; border-radius: 4px; display: inline-block; '
                    f'margin-right: 10px;">🔄 Пересканировать</a>'
                )
            
            # Кнопка переиндексации (только для processed)
            if obj.status == 'processed':
                reindex_url = reverse('admin:documents_document_reindex', args=[obj.pk])
                buttons.append(
                    f'<a class="button" href="{reindex_url}" '
                    f'style="background-color: #ba2121; color: white; padding: 5px 10px; '
                    f'text-decoration: none; border-radius: 4px; display: inline-block;">♻️ Переиндексировать</a>'
                )
            
            # Специальное сообщение для error
            if obj.status == 'error':
                buttons.insert(0, 
                    '<span style="color: red; font-weight: bold;">⚠️ Документ с ошибкой - '
                    'нажмите "Пересканировать" для повторной обработки</span><br><br>'
                )
            
            return mark_safe(''.join(buttons))
        return '-'
    action_buttons.short_description = "Действия"  # type: ignore
    
    def reindex_documents(self, request, queryset):
        """Action для повторной индексации документов"""
        service = get_document_service()
        count = 0
        skipped = 0
        
        for document in queryset:
            if document.status == 'processing':
                skipped += 1
                continue
            
            # Запуск переиндексации в фоне
            thread = threading.Thread(target=service.reindex_document, args=(document,))
            thread.daemon = True
            thread.start()
            count += 1
        
        message = f"Запущена переиндексация {count} документов"
        if skipped:
            message += f" (пропущено {skipped} обрабатывающихся документов)"
        
        self.message_user(request, message)
    reindex_documents.short_description = "Переиндексировать выбранные документы"  # type: ignore
    
    def process_documents(self, request, queryset):
        """Action для обработки/пересканирования документов"""
        service = get_document_service()
        count = 0
        skipped = 0
        
        for document in queryset:
            if document.status == 'processing':
                skipped += 1
                continue
            
            # Запуск обработки в фоне
            thread = threading.Thread(target=service.process_document, args=(document,))
            thread.daemon = True
            thread.start()
            count += 1
        
        message = f"Запущена обработка {count} документов"
        if skipped:
            message += f" (пропущено {skipped} обрабатывающихся документов)"
        
        self.message_user(request, message)
    process_documents.short_description = "Пересканировать выбранные документы"  # type: ignore
    
    def retry_failed_documents(self, request, queryset):
        """Action для повторной обработки документов с ошибками"""
        service = get_document_service()
        
        # Фильтруем только документы со статусом error
        failed_docs = queryset.filter(status='error')
        count = failed_docs.count()
        
        if count == 0:
            self.message_user(
                request,
                "Среди выбранных документов нет документов с ошибками",
                level='warning'
            )
            return
        
        for document in failed_docs:
            # Сброс статуса и очистка сообщения об ошибке
            document.status = 'pending'
            document.error_message = ''
            document.save()
            
            # Запуск обработки в фоне
            thread = threading.Thread(target=service.process_document, args=(document,))
            thread.daemon = True
            thread.start()
        
        self.message_user(
            request,
            f"Запущена повторная обработка {count} документов с ошибками"
        )
    retry_failed_documents.short_description = "Повторить обработку документов с ошибками"  # type: ignore
