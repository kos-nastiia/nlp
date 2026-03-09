import numpy as np
import pandas as pd
from gensim.models import Word2Vec, FastText
from sentence_transformers import SentenceTransformer
from typing import List, Union

def train_w2v_model(texts: List[str], vector_size: int = 100, window: int = 5) -> Word2Vec:
    """
    Навчає модель Word2Vec на вашому корпусі текстів.
    """
    tokenized_data = [str(text).split() for text in texts]
    model = Word2Vec(sentences=tokenized_data, vector_size=vector_size, window=window, min_count=1, workers=4)
    return model

def get_w2v_embeddings(texts: List[str], model: Word2Vec) -> np.ndarray:
    """
    Генерує середній вектор для кожного тексту на основі Word2Vec.
    """
    vector_size = model.vector_size
    embeddings = []
    
    for text in texts:
        words = str(text).split()
        vectors = [model.wv[word] for word in words if word in model.wv]
        if vectors:
            embeddings.append(np.mean(vectors, axis=0))
        else:
            embeddings.append(np.zeros(vector_size))
            
    return np.array(embeddings)

def get_sbert_embeddings(texts: List[str], model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2') -> np.ndarray:
    """
    Генерує якісні контекстуальні ембедінги за допомогою Sentence-BERT.
    Модель paraphrase-multilingual рекомендована для української мови.
    """
    model = SentenceTransformer(model_name)
    return model.encode(texts, show_progress_bar=True)

def calculate_cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Обчислює косинусну подібність між двома векторами.
    """
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

if __name__ == "__main__":
    print("--- Запуск тестування модуля embeddings.py ---")
    
    test_data = [
        "це тестовий документ для перевірки",
        "NLP та ембедінги це цікаво",
        "україномовна модель працює добре"
    ]

    try:
        print("\n1. Тестування Word2Vec...")
        w2v = train_w2v_model(test_data, vector_size=50)
        w2v_vecs = get_w2v_embeddings(test_data, w2v)
        print(f"Успішно! Форма матриці W2V: {w2v_vecs.shape}")

        print("\n2. Тестування SBERT (завантаження моделі)...")
        sbert_vecs = get_sbert_embeddings(test_data)
        print(f"Успішно! Форма матриці SBERT: {sbert_vecs.shape}")

        print("\n3. Тестування косинусної схожості...")
        similarity = calculate_cosine_similarity(sbert_vecs[0], sbert_vecs[1])
        print(f"Схожість між реченнями: {similarity:.4f}")

        print("\n✅ Модуль готовий до роботи!")
    except Exception as e:
        print(f"\n❌ Виникла помилка під час тестування: {e}")

