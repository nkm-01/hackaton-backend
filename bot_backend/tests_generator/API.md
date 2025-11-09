# Tests Generator API

API для генерации тестовых вопросов по охране труда на основе документов из векторной БД.

## Как это работает

1. Система получает 10 случайных фрагментов из Qdrant
2. Фрагменты отправляются в LLM (DeepSeek)
3. LLM генерирует тестовые вопросы с вариантами ответов
4. Тест сохраняется в БД и возвращается клиенту

## Endpoints

### 1. Генерация нового теста

```
POST /api/tests/generate/
```

**Request Body (опционально):**
```json
{
  "questions_count": 10
}
```

**Параметры:**
- `questions_count` (опционально) - Количество вопросов (1-20, по умолчанию 10)

**Response (201 Created):**
```json
{
  "id": "uuid",
  "questions_count": 10,
  "questions": [
    {
      "question": "Какие требования предъявляются к средствам индивидуальной защиты (СИЗ)?",
      "options": [
        "Должны быть модными и удобными",
        "Должны соответствовать характеру и условиям труда, иметь сертификацию",
        "Должны быть недорогими и доступными",
        "Должны нравиться работникам"
      ],
      "correct": 1
    },
    {
      "question": "Какова периодичность проведения инструктажа по охране труда?",
      "options": [
        "Один раз в год",
        "Каждый месяц",
        "По усмотрению руководителя",
        "В соответствии с требованиями нормативных документов"
      ],
      "correct": 3
    }
  ],
  "created_at": "2025-11-09T12:00:00Z"
}
```

**Формат вопроса:**
- `question` - текст вопроса
- `options` - массив вариантов ответа (обычно 4)
- `correct` - индекс правильного ответа (нумерация с 0)

**Errors:**

400 Bad Request:
```json
{
  "questions_count": ["Убедитесь, что это значение меньше либо равно 20."]
}
```

500 Internal Server Error:
```json
{
  "error": "Не удалось получить данные из Qdrant. Возможно, база данных пуста."
}
```

### 2. Получение теста по ID

```
GET /api/tests/{test_id}/
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "questions_count": 10,
  "questions": [...],
  "created_at": "2025-11-09T12:00:00Z"
}
```

### 3. История тестов

```
GET /api/tests/history/
```

**Response (200 OK):**
```json
[
  {
    "id": "uuid",
    "questions_count": 10,
    "created_at": "2025-11-09T12:00:00Z"
  },
  {
    "id": "uuid",
    "questions_count": 15,
    "created_at": "2025-11-09T11:00:00Z"
  }
]
```

## Примеры использования

### cURL

**Генерация теста с 10 вопросами:**
```bash
curl -X POST http://localhost:8000/api/tests/generate/ \
  -H "Content-Type: application/json" \
  -d '{"questions_count": 10}'
```

**Генерация с параметрами по умолчанию:**
```bash
curl -X POST http://localhost:8000/api/tests/generate/ \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Python

```python
import requests

# Генерация теста
response = requests.post(
    'http://localhost:8000/api/tests/generate/',
    json={'questions_count': 10}
)

test = response.json()

print(f"Сгенерировано вопросов: {test['questions_count']}")

# Вывод вопросов
for i, q in enumerate(test['questions'], 1):
    print(f"\n{i}. {q['question']}")
    for j, option in enumerate(q['options']):
        marker = "✓" if j == q['correct'] else " "
        print(f"  {marker} {j}. {option}")
```

### JavaScript

```javascript
// Генерация теста
const response = await fetch('http://localhost:8000/api/tests/generate/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    questions_count: 10
  })
});

const test = await response.json();

// Отображение вопросов
test.questions.forEach((q, i) => {
  console.log(`${i + 1}. ${q.question}`);
  q.options.forEach((option, j) => {
    const marker = j === q.correct ? '✓' : ' ';
    console.log(`  ${marker} ${j}. ${option}`);
  });
});
```

## Использование в фронтенде

### Генерация и отображение теста

```javascript
async function generateTest(questionsCount = 10) {
  try {
    const response = await fetch('http://localhost:8000/api/tests/generate/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ questions_count: questionsCount })
    });
    
    if (!response.ok) {
      throw new Error('Ошибка генерации теста');
    }
    
    const test = await response.json();
    displayTest(test);
    return test;
  } catch (error) {
    console.error('Ошибка:', error);
    alert('Не удалось сгенерировать тест');
  }
}

function displayTest(test) {
  const container = document.getElementById('test-container');
  
  test.questions.forEach((q, index) => {
    const questionDiv = document.createElement('div');
    questionDiv.className = 'question';
    
    const questionText = document.createElement('h3');
    questionText.textContent = `${index + 1}. ${q.question}`;
    questionDiv.appendChild(questionText);
    
    q.options.forEach((option, optionIndex) => {
      const label = document.createElement('label');
      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.name = `question_${index}`;
      radio.value = optionIndex;
      radio.dataset.correct = optionIndex === q.correct;
      
      label.appendChild(radio);
      label.appendChild(document.createTextNode(option));
      questionDiv.appendChild(label);
      questionDiv.appendChild(document.createElement('br'));
    });
    
    container.appendChild(questionDiv);
  });
}

// Проверка ответов
function checkAnswers() {
  const radios = document.querySelectorAll('input[type="radio"]:checked');
  let correct = 0;
  
  radios.forEach(radio => {
    if (radio.dataset.correct === 'true') {
      correct++;
      radio.parentElement.style.color = 'green';
    } else {
      radio.parentElement.style.color = 'red';
    }
  });
  
  alert(`Правильных ответов: ${correct} из ${radios.length}`);
}
```

## Админ-панель

Через Django Admin (`/admin/`) доступны:

1. **Просмотр сгенерированных тестов**
   - Список всех тестов с датой и количеством вопросов
   - Фильтрация по дате и количеству вопросов
   - Превью первого вопроса

2. **Детальный просмотр теста**
   - Все вопросы с вариантами ответов
   - Правильные ответы отмечены зеленым цветом и ✓
   - Красивое форматирование

3. **Удаление старых тестов**
   - Можно удалять ненужные тесты

**Примечание:** Создание тестов через админку запрещено - только через API.

## Особенности генерации

### Как LLM создает вопросы:

1. **Контекст**: Используются случайные фрагменты из документов
2. **Разнообразие**: Каждый раз новые фрагменты = новые вопросы
3. **Качество**: Вопросы основаны только на реальной информации из документов
4. **Сложность**: Неправильные варианты правдоподобны, но четко неверны

### Требования к документам:

- В Qdrant должны быть проиндексированы документы
- Минимум 10 фрагментов в базе для генерации
- Чем больше документов, тем разнообразнее вопросы

### Ограничения:

- Максимум 20 вопросов за раз
- Генерация занимает 10-30 секунд (зависит от LLM)
- Требуется подключение к DeepSeek API

## Обработка ошибок

### Пустая база данных:
```json
{
  "error": "Не удалось получить данные из Qdrant. Возможно, база данных пуста."
}
```
**Решение:** Загрузите документы через `/api/documents/`

### Ошибка LLM:
```json
{
  "error": "Не удалось распарсить ответ LLM: ..."
}
```
**Решение:** Повторите запрос или проверьте API ключ

### Таймаут:
Если запрос зависает, увеличьте timeout в настройках клиента.

## Best Practices

1. **Кеширование**: Сохраняйте сгенерированные тесты, не генерируйте заново
2. **Предзагрузка**: Генерируйте тесты заранее для быстрого отображения
3. **Валидация**: Проверяйте корректность индекса `correct` (0 ≤ correct < options.length)
4. **Обработка ошибок**: Всегда обрабатывайте возможные ошибки генерации
5. **UX**: Показывайте индикатор загрузки во время генерации

## Интеграция с тестированием

Используйте сгенерированные тесты для:
- Проверки знаний сотрудников
- Обучающих курсов
- Аттестации по охране труда
- Самопроверки

Статистику можно отслеживать на стороне фронтенда или создать отдельный модуль для сохранения результатов.
