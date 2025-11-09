"""
Management команда для тестирования AI модуля
Использование: python manage.py test_ai_query "Ваш вопрос"
"""
from django.core.management.base import BaseCommand
from integrations.ai_client import get_ai_client


class Command(BaseCommand):
    help = 'Тестирование запроса к AI модулю'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'question',
            type=str,
            help='Вопрос для AI консультанта'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=15,
            help='Количество документов для контекста (по умолчанию 15)'
        )
    
    def handle(self, *args, **options):
        question = options['question']
        limit = options['limit']
        
        self.stdout.write(self.style.SUCCESS(f'\nВопрос: {question}'))
        self.stdout.write(self.style.SUCCESS(f'Количество документов в контексте: {limit}\n'))
        
        try:
            ai_client = get_ai_client()
            result = ai_client.ask_question(question, limit=limit)
            
            self.stdout.write(self.style.SUCCESS('=' * 80))
            self.stdout.write(self.style.SUCCESS('ОТВЕТ:'))
            self.stdout.write(self.style.SUCCESS('=' * 80))
            self.stdout.write(result.response)
            self.stdout.write('')
            
            self.stdout.write(self.style.SUCCESS('=' * 80))
            self.stdout.write(self.style.SUCCESS('ИСТОЧНИКИ:'))
            self.stdout.write(self.style.SUCCESS('=' * 80))
            
            for source in result.sources[:5]:  # Показываем только топ-5
                self.stdout.write(f"\n[{source['index']}] {source['title']}")
                if source['year']:
                    self.stdout.write(f"    Год: {source['year']}")
                if source.get('document_id'):
                    self.stdout.write(f"    Document ID: {source['document_id']}")
                self.stdout.write(f"    Score: {source['score']:.4f}")
                self.stdout.write(f"    Превью: {source['text_preview']}")
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 80))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nОшибка: {str(e)}'))
