"""
Модуль для загрузки и индексации документов в Qdrant.
Сохраняет оригинальные промпты и схему данных.
"""
import os
from typing import List, Optional, Dict
from dataclasses import dataclass

from openai import OpenAI
from qdrant_client.models import PointStruct

from .ai_client import get_ai_client, SECTION_ANALYSIS_PROMPT
import uuid


@dataclass
class DocumentSection:
    """Секция документа"""
    text: str
    title: str
    year: Optional[int] = None


class DocumentProcessor:
    """Процессор для обработки и индексации документов"""
    
    def __init__(self):
        self.ai_client = get_ai_client()
        self.llm = self.ai_client.llm
        self.embedder = self.ai_client.embedder
        self.qdrant_client = self.ai_client.qdrant_client
        self.collection_name = self.ai_client.collection_name
        
        # Константы (НЕ ИЗМЕНЯТЬ!)
        self.PAGE_SIZE = self.ai_client.PAGE_SIZE
        self.TITLE_INFO_SIZE = self.ai_client.TITLE_INFO_SIZE
        self.CHUNK_SIZE = self.ai_client.CHUNK_SIZE
    
    def _query_llm_for_sections(self, chunk: str) -> str:
        """Запрос к LLM для анализа секций документа (НЕ ИЗМЕНЯТЬ!)"""
        response = self.llm.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SECTION_ANALYSIS_PROMPT},
                {"role": "user", "content": chunk}
            ],
            temperature=0.01
        )
        content = response.choices[0].message.content.strip()
        print(f'LLM Response: {content}')
        print('---')
        return content
    
    def _strip_code_fence(self, content: str) -> str:
        """Удаление markdown code fence маркеров (НЕ ИЗМЕНЯТЬ!)"""
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        return content
    
    def _get_section_chunks(self, chunk: str) -> List[str]:
        """
        Разделение chunk на секции на основе анализа LLM (НЕ ИЗМЕНЯТЬ!)
        """
        content = self._query_llm_for_sections(chunk)
        content = self._strip_code_fence(content)
        
        # Check for NO RESULT
        if "<NO RESULT" in content.upper():
            return []
        
        # Extract content between <RESULT> tags
        start_tag = "<RESULT>"
        end_tag = "</RESULT>"
        if start_tag in content and end_tag in content:
            start_idx = content.find(start_tag) + len(start_tag)
            end_idx = content.find(end_tag, start_idx)
            content = content[start_idx:end_idx].strip()
        
        # Parse markers and build sections (streaming, preserving order)
        sections = []
        current_section_start = None
        
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
                
            # Remove numbering prefix (4 digits and colon)
            if len(line) > 5 and line[:4].isdigit() and line[4] == ':':
                line = line[5:].strip()
            
            # Check marker type
            if line.startswith("section startfrom "):
                text = line[len("section startfrom "):].strip()
                marker_type = "startfrom"
            elif line.startswith("section continue"):
                text = line[len("section continue"):].strip()
                marker_type = "continue"
            elif line.startswith("rubbish skipfrom "):
                text = line[len("rubbish skipfrom "):].strip()
                marker_type = "skipfrom"
            else:
                continue
            
            # Remove ellipsis at the end
            if text.endswith('...'):
                text = text[:-3].strip()
            elif text.endswith('…'):
                text = text[:-1].strip()
            
            # Find position in chunk
            pos = chunk.find(text)
            if pos == -1:
                continue
            
            # Process marker
            if marker_type == "skipfrom":
                # Close current section before rubbish
                if current_section_start is not None:
                    sections.append(chunk[current_section_start:pos])
                    current_section_start = None
            elif marker_type == "startfrom":
                # Start new section
                current_section_start = pos
            elif marker_type == "continue":
                # Continue current section - don't close it, just skip rubbish
                if current_section_start is None:
                    # If no section was open, start from continue point
                    current_section_start = pos
        
        # Close last section if still open
        if current_section_start is not None:
            sections.append(chunk[current_section_start:])
        
        return sections
    
    def _extract_meta(self, chunk: str) -> Optional[Dict[str, any]]:
        """Извлечение метаданных документа (НЕ ИЗМЕНЯТЬ!)"""
        content = self._query_llm_for_sections(chunk)
        content = self._strip_code_fence(content)
        
        # Extract content between <META> tags
        start_tag = "<META>"
        end_tag = "</META>"
        if start_tag not in content or end_tag not in content:
            return None
        
        start_idx = content.find(start_tag) + len(start_tag)
        end_idx = content.find(end_tag, start_idx)
        meta_content = content[start_idx:end_idx].strip()
        
        # Parse META fields
        meta = {}
        for line in meta_content.splitlines():
            line = line.strip()
            if not line or ':' not in line:
                continue
            
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == "title":
                meta["title"] = value
            elif key == "year":
                try:
                    meta["year"] = int(value)
                except ValueError:
                    meta["year"] = value
        
        return meta if meta else None
    
    def process_document(self, text: str) -> List[DocumentSection]:
        """
        Обработка текста документа и разделение на секции
        
        Args:
            text: Текст документа
            
        Returns:
            Список секций документа
        """
        document_words = text.replace('\n', ' ').split()
        
        # Извлечение метаданных из начала документа
        meta = self._extract_meta(' '.join(document_words[:self.TITLE_INFO_SIZE]))
        title = meta.get('title', 'Неизвестный документ') if meta else 'Неизвестный документ'
        year = meta.get('year') if meta else None
        
        # Разделение на chunks
        chunks = []
        for i in range(0, len(document_words), self.CHUNK_SIZE):
            chunk = document_words[i:i + self.CHUNK_SIZE]
            chunks.append(' '.join(chunk))
        
        # Обработка chunks и получение секций
        sections = []
        for chunk in chunks:
            print('Processing chunk...')
            borders = self._get_section_chunks(chunk)
            if borders:
                sections.extend([b for b in borders if len(b) > 80])
            elif sections:
                sections[-1] += ' ' + chunk
            else:
                sections.append(chunk)
        
        # Создание объектов DocumentSection
        result = []
        for section_text in sections:
            result.append(DocumentSection(
                text=section_text,
                title=title,
                year=year
            ))
        
        return result
    
    def index_document(self, sections: List[DocumentSection], document_id: str):
        """
        Индексация секций документа в Qdrant (НЕ ИЗМЕНЯТЬ СХЕМУ!)
        
        Args:
            sections: Список секций документа
            document_id: ID документа для формирования уникальных ID точек
        """
        texts = [section.text for section in sections]
        
        # Генерация эмбеддингов
        vectors = self.embedder.encode(texts).tolist()
        
        # Создание точек для Qdrant
        points = []
        for i, section in enumerate(sections):
            
            payload = {
                "text": section.text,
                "title": section.title,
                "year": section.year,
                "document_id": document_id
            }
            
            points.append(PointStruct(
                id=uuid.uuid4().hex,
                vector=vectors[i],
                payload=payload
            ))
        
        # Загрузка в Qdrant
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        print(f"Indexed {len(points)} sections for document {document_id}")
    
    def remove_document(self, document_id: str):
        """
        Удаление документа из Qdrant по document_id
        
        Args:
            document_id: ID документа
        """
        # Удаление всех точек с данным document_id
        self.qdrant_client.delete(
            collection_name=self.collection_name,
            points_selector={
                "filter": {
                    "must": [
                        {
                            "key": "document_id",
                            "match": {"value": document_id}
                        }
                    ]
                }
            }
        )
        
        print(f"Removed document {document_id} from Qdrant")


def get_document_processor() -> DocumentProcessor:
    """Получить экземпляр процессора документов"""
    return DocumentProcessor()
