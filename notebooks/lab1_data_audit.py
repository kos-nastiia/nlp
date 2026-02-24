import pandas as pd
import re
import os
import csv
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

raw_data_path = os.path.join(project_root, 'data', 'raw.csv')
processed_data_path = os.path.join(project_root, 'data', 'processed.csv')

print(f"--- ЗАПУСК АУДИТУ ---")

try:
    df = pd.read_csv(
        raw_data_path, 
        sep=None,           
        engine='python', 
        encoding='utf-8-sig',
        quoting=csv.QUOTE_NONE,
        on_bad_lines='warn' 
    )
except Exception as e:
    print(f"Критична помилка при читанні: {e}")
    exit()

df.columns = [c.strip('"') for c in df.columns]
text_col = df.columns[0]

print(f"Успішно завантажено. Рядків: {len(df)}")

def clean_text(text):
    if not isinstance(text, str): return ""
    text = text.strip('"')
    text = re.sub(r"['’‘`]", "'", text)
    text = re.sub(r'https?://\S+|www\.\S+', '<URL>', text)
    text = re.sub(r'\S+@\S+', '<EMAIL>', text)
    text = re.sub(r'\+?\d{10,12}', '<PHONE>', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

df['processed_text'] = df[text_col].apply(clean_text)

char_counts = df['processed_text'].str.len()
word_counts = df['processed_text'].str.split().str.len()

avg_chars = char_counts.mean()
med_chars = char_counts.median()
avg_words = word_counts.mean()
med_words = word_counts.median()

duplicates = df.duplicated(subset=['processed_text']).sum()
short_texts = (word_counts < 5).sum()
garbage = df['processed_text'].apply(lambda x: not any(c.isalpha() for c in x)).sum()

print(f"\n--- РЕЗУЛЬТАТИ АУДИТУ ---")
print(f"1. Точні дублікати: {duplicates} ({duplicates/len(df)*100:.1f}%)")
print(f"2. Короткі тексти (<5 слів): {short_texts}")
print(f"3. Сміттєві рядки (без літер): {garbage}")
print(f"4. Середня довжина: {avg_words:.1f} слів ({avg_chars:.1f} симв.)")
print(f"5. Медіанна довжина: {med_words:.0f} слів ({med_chars:.0f} симв.)")

df_final = df.drop_duplicates(subset=['processed_text']).copy()
final_word_counts = df_final['processed_text'].str.split().str.len()
final_garbage_mask = df_final['processed_text'].apply(lambda x: not any(c.isalpha() for c in x))

df_final = df_final[(final_word_counts >= 5) & (~final_garbage_mask)]

os.makedirs(os.path.dirname(processed_data_path), exist_ok=True)
df_final[['processed_text']].to_csv(processed_data_path, index=False, encoding='utf-8-sig')

print(f"\n--- ГОТОВО ---")
print(f"Чисті дані збережено: {processed_data_path}")
print(f"Залишилося рядків: {len(df_final)}")