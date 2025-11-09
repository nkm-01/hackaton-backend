# AI Integration Module

Модуль интеграции с AI моделью (DeepSeek) и векторной БД Qdrant.

## Компоненты

### 1. `ai_client.py`
Основной клиент для работы с AI и Qdrant:
- **AIClient** - singleton класс, инициализируется автоматически при запуске Django
- Подключение к Qdrant (localhost:6333)
- Загрузка модели эмбеддингов (intfloat/multilingual-e5-large)
- Инициализация LLM клиента (DeepSeek)

**Методы:**
- `ask_question(question, limit)` - задать вопрос и получить ответ с источниками
- `get_random_points(count)` - получить случайные точки из Qdrant для генерации тестов

### 2. `load_documents.py`
Процессор для загрузки и индексации документов:
- **DocumentProcessor** - класс для обработки документов
- Разделение документов на секции с помощью LLM
- Извлечение метаданных (название, год)
- Индексация в Qdrant

**Методы:**
- `process_document(text)` - обработать текст документа
- `index_document(sections, document_id)` - индексировать секции в Qdrant
- `remove_document(document_id)` - удалить документ из Qdrant

### 3. `apps.py`
Django AppConfig для автоматической инициализации AI клиента при запуске сервера.

## Схема данных Qdrant

**Collection:** `rag_collection`

**Payload структура:**
```python
{
    "text": str,           # Текст секции
    "title": str,          # Название документа
    "year": int | None,    # Год издания
    "document_id": str     # ID документа в Django (UUID)
}
```

**ВАЖНО:** Не изменять схему данных и промпты!

**Использование document_id:**
- При индексации документа передается ID из модели Django Document
- Позволяет связать точки в Qdrant с документами в БД
- Используется для удаления всех точек документа при его удалении
- Возвращается в источниках при консультациях

## Промпты

### SYSTEM_PROMPT
Используется для консультаций. Определяет поведение AI как ассистента по охране труда.

### SECTION_ANALYSIS_PROMPT
Используется для разделения документов на секции. Определяет формат анализа границ текста.

## Использование

### Получение AI клиента
```python
from integrations.ai_client import get_ai_client

ai_client = get_ai_client()
result = ai_client.ask_question("Ваш вопрос")
```

### Обработка документов
```python
from integrations.load_documents import get_document_processor

processor = get_document_processor()
sections = processor.process_document(text)
processor.index_document(sections, document_id="doc_123")
```

### Тестирование через management команду
```bash
python manage.py test_ai_query "Максимальное давление в баллоне"
python manage.py test_ai_query "Требования к спецодежде" --limit 10
```

## Требования

- Python 3.10+
- Qdrant (запущен на localhost:6333)
- API ключ DeepSeek в .env файле (LLM_API_KEY)

## Переменные окружения

Создайте файл `.env` в корне проекта:
```
LLM_API_KEY=your_deepseek_api_key
```

## Инициализация

AI клиент автоматически инициализируется при запуске Django сервера благодаря `IntegrationsConfig.ready()`.

При запуске вы увидите:
```
============================================================
Starting AI Client initialization...
============================================================
Initializing AI Client...
Loading embedder model...
Connecting to Qdrant...
Creating collection 'rag_collection'...
Collection created!
AI Client initialized successfully!
============================================================
AI Client ready!
Collection: rag_collection
Vector size: 1024
============================================================
```

## Константы обработки документов

**НЕ ИЗМЕНЯТЬ:**
- `PAGE_SIZE = 240` - размер страницы в словах
- `TITLE_INFO_SIZE = PAGE_SIZE * 2` - размер области для поиска метаданных
- `CHUNK_SIZE = PAGE_SIZE * 20` - размер chunk для обработки

## Troubleshooting

### Qdrant не запущен
```
ERROR: Failed to initialize AI Client: [Errno 111] Connection refused
```
Решение: Запустите Qdrant с помощью Docker:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

### Отсутствует API ключ
```
ValueError: LLM_API_KEY not found in .env file
```
Решение: Создайте `.env` файл с ключом LLM_API_KEY

### Модель эмбеддингов не загружается
Первый запуск может занять время - модель загружается из HuggingFace (~1-2 минуты).
