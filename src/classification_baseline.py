import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, f1_score

# 1. Завантаження даних
df = pd.read_csv("data/processed_v2.csv")

# 2. Функція для вилучення мітки (0 або 1) з кінця тексту
def extract_label_and_clean(text):
    text = str(text).strip()
    if text and text[-1] in ['0', '1']:
        label = int(text[-1])
        clean_text = text[:-1].strip() # Видаляємо цифру з тексту
        return label, clean_text
    return None, text

# Створюємо нові колонки на основі витягнутих даних
extracted = df['text_v2'].apply(extract_label_and_clean)
df['label'] = [x[0] for x in extracted]
df['text_v2_clean'] = [x[1] for x in extracted]

# 3. Фільтрація: залишаємо тільки рядки, де була мітка (0 або 1)
# Це критично для вашого напряму D, щоб мати дані для навчання
df_labeled = df.dropna(subset=['label']).copy()
df_labeled['label'] = df_labeled['label'].astype(int)

print(f"Знайдено розмічених прикладів: {len(df_labeled)}")
print(f"Розподіл класів:\n{df_labeled['label'].value_counts()}")

# 4. Розподіл на Train/Val/Test
X = df_labeled['text_v2_clean']
y = df_labeled['label']

X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp)

# 5. Векторизація TF-IDF (згідно з рекомендацією 2.1)
tfidf = TfidfVectorizer(
    analyzer="word", 
    ngram_range=(1, 2), 
    sublinear_tf=True
)

X_train_tfidf = tfidf.fit_transform(X_train)
X_val_tfidf = tfidf.transform(X_val)
X_test_tfidf = tfidf.transform(X_test)

# 6. Класифікатор Logistic Regression
baseline_model = LogisticRegression(max_iter=500, random_state=42)
baseline_model.fit(X_train_tfidf, y_train)

# 7. Оцінка
y_pred = baseline_model.predict(X_val_tfidf)
print("\n=== Результати на Validation Set ===")
print(f"Accuracy: {accuracy_score(y_val, y_pred):.4f}")
print(f"Macro-F1: {f1_score(y_val, y_pred, average='macro'):.4f}")
print(classification_report(y_val, y_pred))
