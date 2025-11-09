"""
AI Client для работы с Qdrant и языковой моделью.
Инициализируется при запуске Django приложения.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
import os
import dotenv

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from openai import OpenAI


# Системный промпт для консультаций (НЕ ИЗМЕНЯТЬ!)
SYSTEM_PROMPT = """
Охрана труда.
Нормативная база.
Безопасность труда.
Только на основе документов.
Подтверждай ссылками на документы.
Точный ответ.
При недостатке информации отвечай "Не знаю".
Ты - ассистент по охране труда. Помогай с ответами на вопросы по охране труда, используя предоставленные документы.
Правила:
* Отвечай только на основе предоставленных документов.
* Других документов не существует. Упоминай только предоставленные документы.
* Если информации недостаточно, отвечай "Не знаю".
"""

# Промпт для разделения документов на секции (НЕ ИЗМЕНЯТЬ!)
SECTION_ANALYSIS_PROMPT = """
Анализ границ текста. Разделение на разделы. Точный вывод. Только формат. Строго соблюдай порядок. Нумерация.
Разрешенные операторы:
- section startfrom <text> — начало нового раздела с указанного текста
- rubbish skipfrom <text> — начало мусора с указанного текста
- section continue <text> — продолжение текущего раздела с указанного текста после мусора
В блоке META:
- TITLE: <название документа>
- YEAR: <год издания документа>
Ниже даны фрагменты текста. Напиши, есть ли в них границы разделов по смыслу, в том числе в рамках главы. Отдельно отметь фрагменты, которые содержат бесполезную информацию как мусор (титульники, оглавления, списки редакций и пр.) Если мусор посередине раздела, то продолжи его инструкцией continue.
Если фрагмент содержит титульный лист, используй блок META вместе с RESULT.
Укажи в формате:
```
<RESULT>
0001:section startfrom Отсюда начинается новая тема
0002:section startfrom А сейчас рассмотрим другую тему
0003:rubbish skipfrom Сноска 1
0004:section startfrom Далее идет следующая тема
0005:rubbish skipfrom Сноска 2
0006:section continue задача механизма состоит в
</RESULT>
```
или
```
<NO RESULT/>
```
а также
```
<META>
TITLE: Приказ об охране труда № 123 от 04 апреля 2020 года
YEAR: 2020
</META>
```
---
"""


@dataclass
class DocumentMeta:
    """Метаданные документа"""
    title: str
    year: Optional[int] = None


@dataclass
class ConsultationResult:
    """Результат консультации"""
    response: str
    sources: List[Dict[str, any]]


class AIClient:
    """
    Клиент для работы с AI моделью и векторной БД Qdrant.
    Singleton - инициализируется один раз при запуске приложения.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Загрузка API ключа
        dotenv.load_dotenv()
        self.api_key = dotenv.get_key(dotenv.find_dotenv(), "LLM_API_KEY")
        
        if not self.api_key:
            raise ValueError("LLM_API_KEY not found in .env file")
        
        # Инициализация компонентов
        print("Initializing AI Client...")
        
        # LLM клиент
        self.llm = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com/v1"
        )
        
        # Embedder модель
        print("Loading embedder model...")
        self.embedder = SentenceTransformer("intfloat/multilingual-e5-large")
        self.vector_size = self.embedder.get_sentence_embedding_dimension()
        
        # Qdrant клиент
        print("Connecting to Qdrant...")
        self.qdrant_client = QdrantClient("localhost", port=6333)
        
        # Название коллекции (НЕ ИЗМЕНЯТЬ!)
        self.collection_name = "rag_collection"
        
        # Создание коллекции если не существует
        self._ensure_collection_exists()
        
        # Константы для обработки документов (НЕ ИЗМЕНЯТЬ!)
        self.PAGE_SIZE = 240
        self.TITLE_INFO_SIZE = self.PAGE_SIZE * 2
        self.CHUNK_SIZE = self.PAGE_SIZE * 20
        
        self._initialized = True
        print("AI Client initialized successfully!")
    
    def _ensure_collection_exists(self):
        """Создать коллекцию в Qdrant если она не существует"""
        if not self.qdrant_client.collection_exists(self.collection_name):
            print(f"Creating collection '{self.collection_name}'...")
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            print("Collection created!")
    
    def ask_question(self, question: str, limit: int = 15) -> ConsultationResult:
        """
        Задать вопрос и получить ответ на основе документов из Qdrant
        
        Args:
            question: Вопрос пользователя
            limit: Количество документов для контекста
            
        Returns:
            ConsultationResult с ответом и источниками
        """
        # Получить эмбеддинг вопроса
        question_vector = self.embedder.encode([question]).tolist()[0]
        
        # Поиск релевантных документов
        results = self.qdrant_client.query_points(
            collection_name=self.collection_name,
            query=question_vector,
            limit=limit
        ).points
        
        # Формирование контекста для LLM
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
        
        sources = []
        for i, result in enumerate(sorted(results, key=lambda x: x.score, reverse=True)):
            text = result.payload.get('text', '')
            title = result.payload.get('title', 'Неизвестный документ')
            year = result.payload.get('year')
            document_id = result.payload.get('document_id')
            
            messages.append({
                'role': 'system',
                'content': f"[{i}] {text}"
            })
            
            sources.append({
                'index': i,
                'title': title,
                'year': year,
                'document_id': document_id,
                'score': result.score,
                'text_preview': text[:200] + '...' if len(text) > 200 else text
            })
        
        # Добавление вопроса пользователя
        messages.append({'role': 'user', 'content': question})
        
        # Получение ответа от LLM
        response = self.llm.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.01
        )
        
        answer = response.choices[0].message.content.strip()
        
        return ConsultationResult(
            response=answer,
            sources=sources
        )
    
    def get_random_points(self, count: int = 10) -> List[Dict[str, any]]:
        """
        Получить случайные точки из Qdrant для генерации тестов
        
        Args:
            count: Количество точек
            
        Returns:
            Список точек с текстом и метаданными
        """
        # Используем scroll для получения случайных точек
        points, _ = self.qdrant_client.scroll(
            collection_name=self.collection_name,
            limit=count,
            with_payload=True,
            with_vectors=False
        )
        
        result = []
        for point in points:
            result.append({
                'id': point.id,
                'text': point.payload.get('text', ''),
                'title': point.payload.get('title', 'Неизвестный документ'),
                'year': point.payload.get('year'),
                'document_id': point.payload.get('document_id')
            })
        
        return result


# Глобальный экземпляр клиента (будет инициализирован при запуске Django)
_ai_client_instance = None


def get_ai_client() -> AIClient:
    """
    Получить глобальный экземпляр AI клиента
    
    Returns:
        AIClient instance
    """
    global _ai_client_instance
    if _ai_client_instance is None:
        _ai_client_instance = AIClient()
    return _ai_client_instance
