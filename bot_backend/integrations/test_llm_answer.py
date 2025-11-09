from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI
import dotenv


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


embedder = SentenceTransformer("intfloat/multilingual-e5-large")
vector_size = embedder.get_sentence_embedding_dimension()

client = QdrantClient("localhost", port=6333)

collection_name = "rag_collection"

question = "Максимальное давление в баллоне"

vectors = embedder.encode([question]).tolist()
results = client.query_points(
    collection_name=collection_name,
    query=vectors[0],
    limit=15
).points

messages = []
messages.append({'role': 'system', 'content': SYSTEM_PROMPT})
for i, result in enumerate(sorted(results, key=lambda x: x.score, reverse=True)):
    messages.append({'role': 'system', 'content': f"[{i}] {result.payload['text']}"})

TOKEN = dotenv.get_key(dotenv.find_dotenv(), "LLM_API_KEY")
llm = OpenAI(api_key=TOKEN, base_url="https://api.deepseek.com/v1")

response = llm.chat.completions.create(
    model="deepseek-chat",
    messages=messages + [
        {'role': 'user', 'content': question}
    ],
    temperature=0.01
)

print("LLM Response:")
print(response.choices[0].message.content.strip())
