import pandas as pd
import json
import re
import os
import subprocess
import sys

# --- КРОК 0: НАЛАШТУВАННЯ ШЛЯХІВ ---
# Отримуємо шлях до папки 'notebooks', де лежить цей файл
current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()

# Визначаємо корінь (на рівень вище), де лежать папки docs, data та файли csv/jsonl
root_dir = os.path.abspath(os.path.join(current_dir, ".."))

GOLD_DATA_PATH = os.path.join(root_dir, 'data','sample', 'lab4_gold_ie.jsonl')
AUDIT_REPORT_PATH = os.path.join(root_dir, 'docs', 'audit_summary_lab4.md')

print(f"Шукаю дані в: {root_dir}")

# Перевірка та встановлення tabulate для гарних таблиць
try:
    import tabulate
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tabulate"])

# --- КРОК 1: РЕАЛІЗАЦІЯ ПРАВИЛ (IE ENGINE) ---
def extract_dates(text):
    date_pattern = r'\b(\d{1,2})[\./-](\d{1,2})[\./-](\d{2,4})\b'
    text_date_pattern = r'\b(\d{1,2})\s(січня|лютого|березня|квітня|травня|червня|липня|серпня|вересня|жовтня|листопада|грудня)\s?(\d{4})?\b'
    found = []
    t = str(text)
    for m in re.finditer(date_pattern, t):
        found.append({"field_type": "DATE", "span_text": m.group(), "start_char": m.start(), "end_char": m.end(), "norm": f"{m.group(3)}-{m.group(2)}-{m.group(1)}"})
    for m in re.finditer(text_date_pattern, t, re.IGNORECASE):
        found.append({"field_type": "DATE", "span_text": m.group(), "start_char": m.start(), "end_char": m.end(), "norm": f"{m.group(3) if m.group(3) else 'None'}-{m.group(2)}-{m.group(1)}"})
    return found

def extract_amounts(text):
    pattern = r'(\d+[\s\d,.]*)\s?(\$|€|грн|UAH|USD|EUR|євро|дол)'
    found = []
    t = str(text)
    for m in re.finditer(pattern, t, re.IGNORECASE):
        val = m.group(1).replace(" ", "").replace(",", ".")
        found.append({"field_type": "AMOUNT", "span_text": m.group(), "start_char": m.start(), "end_char": m.end(), "norm": f"{val} {m.group(2).upper()}"})
    return found

def extract_phones(text):
    pattern = r'(\+?38)?\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}'
    found = []
    t = str(text)
    for m in re.finditer(pattern, t):
        nums = re.sub(r'\D', '', m.group())
        found.append({"field_type": "PHONE", "span_text": m.group(), "start_char": m.start(), "end_char": m.end(), "norm": f"+{nums}"})
    return found

def extract_all(text):
    return extract_dates(text) + extract_amounts(text) + extract_phones(text)

# --- КРОК 3: ОЦІНКА PRECISION ---
print("\n--- Оцінка на Gold Standard ---")
if os.path.exists(GOLD_DATA_PATH):
    with open(GOLD_DATA_PATH, 'r', encoding='utf-8') as f:
        gold = [json.loads(line) for line in f]
    eval_res = []
    for item in gold:
        ext = extract_all(item['text'])
        match = any(e['field_type'] == item['field_type'] and abs(e['start_char'] - item['start_char']) <= 3 for e in ext)
        eval_res.append({"type": item['field_type'], "correct": match})
    report = pd.DataFrame(eval_res).groupby('type')['correct'].mean().reset_index()
    report.columns = ['Field Type', 'Precision']
    print(report.to_string(index=False))
else:
    print(f"ПОМИЛКА: Файл не знайдено за шляхом: {GOLD_DATA_PATH}")
    report = pd.DataFrame([["DATE", 0.0], ["AMOUNT", 0.0], ["PHONE", 0.0]], columns=['Field Type', 'Precision'])

# --- КРОК 4: РЕАЛЬНИЙ АНАЛІЗ ПОМИЛОК (FALSE POSITIVES) ---
print("\n--- Крок 3: Пошук реальних помилок (False Positives) ---")

real_errors = []

if os.path.exists(GOLD_DATA_PATH):
    for item in gold:
        # 1. Що знайшов код
        extracted = extract_all(item['text'])
        
        # 2. Шукаємо те, що код знайшов "зайвого" або "неправильного"
        for e in extracted:
            # Перевіряємо, чи є цей витяг у нашому Gold Standard
            is_correct = (e['field_type'] == item['field_type'] and 
                          abs(e['start_char'] - item['start_char']) <= 3)
            
            if not is_correct:
                real_errors.append({
                    "Текст": item['text'][:50] + "...", # Обрізаємо для таблиці
                    "Витягнуто": f"{e['field_type']} ({e['span_text']})",
                    "Причина": "False Positive (невідповідність еталону)"
                })

# Перетворюємо в DataFrame та беремо перші 10 штук (якщо їх менше — беремо всі)
if real_errors:
    df_err = pd.DataFrame(real_errors).head(10)
else:
    # Якщо код ідеальний (що навряд чи), створюємо пусту таблицю з поясненням
    df_err = pd.DataFrame([["Дані збігаються", "Нічого", "Помилок не знайдено"]], 
                          columns=["Текст", "Витягнуто", "Причина"])

print(f"Знайдено реальних помилок: {len(real_errors)}")

# --- КРОК 5: ЗБЕРЕЖЕННЯ ЗВІТУ ---
print(f"Оновлення звіту: {AUDIT_REPORT_PATH}")
with open(AUDIT_REPORT_PATH, 'w', encoding='utf-8') as f:
    f.write("# Audit Summary - Lab 4\n\n## Precision Metrics\n")
    f.write(report.to_markdown(index=False))
    f.write("\n\n## Real Error Analysis (Top 10 False Positives)\n")
    f.write(df_err.to_markdown(index=False))