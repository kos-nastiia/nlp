import os
import json
import pandas as pd
import re
from datetime import datetime
from sklearn.model_selection import train_test_split

def extract_label(text):
    """
    Витягує останню цифру (0 або 1) з тексту, ігноруючи пробіли та службові символи.
    """
    if pd.isna(text):
        return None
    # Шукаємо всі цифри 0 або 1 у тексті
    labels = re.findall(r'[01]', str(text))
    # Повертаємо останню знайдену цифру як ціле число
    return int(labels[-1]) if labels else None

def make_splits(df, strategy="Stratified Random Split", seed=42):
    """
    Розділяє дані на train/val/test та повертає словник із результатами.
    """
    # Підготовка колонки для стратифікації
    df = df.copy()
    df['temp_label'] = df['text_v2'].apply(extract_label)
    
    # Видаляємо рядки без міток, якщо такі є
    df = df.dropna(subset=['temp_label'])
    
    # Перший спліт: 80% для навчання, 20% на залишок (валідація + тест)
    train_indices, temp_indices = train_test_split(
        df.index, 
        test_size=0.2, 
        random_state=seed, 
        stratify=df['temp_label']
    )
    
    # Другий спліт: розділяємо залишок 50/50 (отримуємо по 10% від загалу)
    val_indices, test_indices = train_test_split(
        temp_indices, 
        test_size=0.5, 
        random_state=seed, 
        stratify=df.loc[temp_indices, 'temp_label']
    )
    
    splits = {
        "train": train_indices.tolist(),
        "val": val_indices.tolist(),
        "test": test_indices.tolist(),
        "metadata": {
            "strategy": strategy,
            "seed": seed,
            "split_proportions": "80/10/10",
            "sizes": {
                "train": len(train_indices),
                "val": len(val_indices),
                "test": len(test_indices)
            },
            "generation_datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "columns_used_for_stratification": ["temp_label (extracted from text_v2)"],
            "columns_used_for_groups_or_time": "None (Random Split used)"
        }
    }
    return splits

def save_splits(splits, out_dir="data/sample", manifest_path="docs/splits_manifest_lab5.json"):
    """
    Зберігає ID сплітів та маніфест у вказані файли.
    """
    # Створюємо директорії
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    
    # Збереження текстових файлів з індексами
    for name in ["train", "val", "test"]:
        file_path = os.path.join(out_dir, f"splits_{name}_ids.txt")
        with open(file_path, "w") as f:
            f.write("\n".join(map(str, splits[name])))
            
    # Збереження JSON маніфесту
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(splits["metadata"], f, indent=4, ensure_ascii=False)
        
    print(f"--- Результати збережено ---")
    print(f"ID сплітів: {out_dir}/")
    print(f"Маніфест: {manifest_path}")

if __name__ == "__main__":
    DATA_PATH = "data/processed_v2.csv"
    
    if os.path.exists(DATA_PATH):
        # Завантаження даних
        df = pd.read_csv(DATA_PATH)
        
        # Виконання спліту
        split_results = make_splits(df)
        
        # Збереження результатів
        save_splits(split_results)
    else:
        print(f"Помилка: Файл {DATA_PATH} не знайдено.")
