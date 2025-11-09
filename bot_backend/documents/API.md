# Documents API

API для управления документами в системе консультаций по охране труда.

## Endpoints

### 1. Список документов
```
GET /api/documents/
```

**Response:**
```json
[
  {
    "id": "uuid",
    "title": "Название документа",
    "file_type": "pdf",
    "file_size": 1024000,
    "file_size_display": "1.0 МБ",
    "file_url": "http://localhost:8000/media/documents/file.pdf",
    "upload_date": "2025-11-09T12:00:00Z",
    "status": "processed",
    "pages_count": 42
  }
]
```

### 2. Детали документа
```
GET /api/documents/{id}/
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Название документа",
  "file": "/media/documents/file.pdf",
  "file_type": "pdf",
  "file_size": 1024000,
  "file_size_display": "1.0 МБ",
  "file_url": "http://localhost:8000/media/documents/file.pdf",
  "upload_date": "2025-11-09T12:00:00Z",
  "status": "processed",
  "error_message": "",
  "pages_count": 42
}
```

### 3. Загрузка документа
```
POST /api/documents/
Content-Type: multipart/form-data
```

**Request:**
```
file: (binary)
title: "Название документа" (опционально)
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Название документа",
  "file": "/media/documents/file.pdf",
  "file_type": "pdf",
  "file_size": 1024000,
  "file_size_display": "1.0 МБ",
  "file_url": "http://localhost:8000/media/documents/file.pdf",
  "upload_date": "2025-11-09T12:00:00Z",
  "status": "pending",
  "error_message": "",
  "pages_count": null
}
```

**Валидация:**
- Допустимые форматы: PDF, RTF, DOCX, TXT
- Максимальный размер: 100 МБ
- Обработка начинается автоматически в фоне

### 4. Удаление документа
```
DELETE /api/documents/{id}/
```

**Response:**
```json
{
  "message": "Документ успешно удален"
}
```

**Действия при удалении:**
- Удаление файла из файловой системы
- Удаление всех точек документа из Qdrant
- Удаление записи из БД

### 5. Статус обработки документа
```
GET /api/documents/{id}/status/
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Название документа",
  "status": "processing",
  "error_message": ""
}
```

**Статусы:**
- `pending` - Ожидает обработки
- `processing` - Обрабатывается
- `processed` - Обработан
- `error` - Ошибка

### 6. Переиндексация документа
```
POST /api/documents/{id}/reindex/
```

**Response:**
```json
{
  "message": "Переиндексация запущена"
}
```

**Действия при переиндексации:**
- Удаление старых данных из Qdrant
- Повторное извлечение текста
- Повторная обработка и индексация

## Процесс обработки документа

1. **Загрузка** - Документ сохраняется в файловой системе, создается запись в БД со статусом `pending`
2. **Извлечение текста** - Текст извлекается в зависимости от формата (PDF/RTF/DOCX/TXT)
3. **Анализ структуры** - LLM анализирует документ и разделяет на секции
4. **Индексация** - Секции векторизуются и сохраняются в Qdrant
5. **Завершение** - Статус меняется на `processed`

## Использование в фронтенде

### Загрузка документа
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('title', 'Название документа');

fetch('http://localhost:8000/api/documents/', {
  method: 'POST',
  body: formData
})
  .then(response => response.json())
  .then(data => {
    console.log('Document uploaded:', data);
    // Можно проверять статус через /api/documents/{id}/status/
  });
```

### Проверка статуса
```javascript
const checkStatus = async (documentId) => {
  const response = await fetch(`http://localhost:8000/api/documents/${documentId}/status/`);
  const data = await response.json();
  
  if (data.status === 'processed') {
    console.log('Документ обработан!');
  } else if (data.status === 'error') {
    console.error('Ошибка обработки:', data.error_message);
  } else {
    console.log('Статус:', data.status);
    // Повторить проверку через несколько секунд
    setTimeout(() => checkStatus(documentId), 3000);
  }
};
```

### Получение списка документов
```javascript
fetch('http://localhost:8000/api/documents/')
  .then(response => response.json())
  .then(documents => {
    documents.forEach(doc => {
      console.log(`${doc.title} - ${doc.status} - ${doc.file_size_display}`);
    });
  });
```

### Удаление документа
```javascript
fetch(`http://localhost:8000/api/documents/${documentId}/`, {
  method: 'DELETE'
})
  .then(response => response.json())
  .then(data => {
    console.log(data.message);
  });
```

## Админ-панель

Через Django Admin (`/admin/`) доступны:

1. **Список документов** с фильтрами по статусу, типу и дате
2. **Загрузка новых документов** - автоматически запускается обработка
3. **Просмотр деталей** - полная информация о документе
4. **Удаление** - с автоматической очисткой Qdrant
5. **Кнопка "Пересканировать"** - в детальном просмотре для любого документа
6. **Кнопка "Переиндексировать"** - в детальном просмотре для обработанных документов

### Массовые действия:
- **Пересканировать выбранные документы** - повторная обработка
- **Переиндексировать выбранные документы** - обновление индекса
- **Повторить обработку документов с ошибками** - умная обработка только ошибочных

Подробнее: см. `ADMIN_GUIDE.md`

## Обработка ошибок

При ошибках обработки:
- Статус документа становится `error`
- В поле `error_message` сохраняется описание ошибки
- Можно попробовать переиндексировать через API или админку

Типичные ошибки:
- Поврежденный файл
- Неподдерживаемый формат
- Ошибка извлечения текста
- Ошибка подключения к Qdrant
- Ошибка LLM API

## Требования

- PyPDF2 - для работы с PDF
- python-docx - для работы с DOCX
- striprtf - для работы с RTF

Установка:
```bash
pip install PyPDF2 python-docx striprtf
```
