"""
Django app для интеграции с AI модулем.
Автоматически инициализирует AI клиент при запуске сервера.
"""
from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'integrations'
    verbose_name = 'AI Интеграция'
    
    def ready(self):
        """
        Выполняется при запуске Django приложения.
        Инициализирует AI клиент.
        """
        # Избегаем повторной инициализации при reload
        import os
        if os.environ.get('RUN_MAIN') != 'true':
            return
        
        print("=" * 60)
        print("Starting AI Client initialization...")
        print("=" * 60)
        
        try:
            from .ai_client import get_ai_client
            
            # Инициализация клиента
            ai_client = get_ai_client()
            
            print("=" * 60)
            print("AI Client ready!")
            print(f"Collection: {ai_client.collection_name}")
            print(f"Vector size: {ai_client.vector_size}")
            print("=" * 60)
            
        except Exception as e:
            print("=" * 60)
            print(f"ERROR: Failed to initialize AI Client: {e}")
            print("=" * 60)
            # Не падаем, продолжаем работу Django
