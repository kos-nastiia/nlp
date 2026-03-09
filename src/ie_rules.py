import re

# Словники для нормалізації (можна розширювати)
CURRENCIES = {"грн": "UAH", "UAH": "UAH", "$": "USD", "USD": "USD", "€": "EUR", "EUR": "EUR"}

def extract_dates(text):
    date_pattern = r'\b(\d{1,2})[\./-](\d{1,2})[\./-](\d{2,4})\b'
    text_date_pattern = r'\b(\d{1,2})\s(січня|лютого|березня|квітня|травня|червня|липня|серпня|вересня|жовтня|листопада|грудня)\s?(\d{4})?\b'
    found = []
    t = str(text)
    for m in re.finditer(date_pattern, t):
        found.append({
            "field_type": "DATE", 
            "span_text": m.group(), 
            "start_char": m.start(), 
            "end_char": m.end(), 
            "norm": f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        })
    for m in re.finditer(text_date_pattern, t, re.IGNORECASE):
        found.append({
            "field_type": "DATE", 
            "span_text": m.group(), 
            "start_char": m.start(), 
            "end_char": m.end(), 
            "norm": f"{m.group(3) if m.group(3) else 'None'}-{m.group(2)}-{m.group(1)}"
        })
    return found

def extract_amounts(text):
    pattern = r'(\d+[\s\d,.]*)\s?(\$|€|грн|UAH|USD|EUR|євро|дол)'
    found = []
    t = str(text)
    for m in re.finditer(pattern, t, re.IGNORECASE):
        val = m.group(1).replace(" ", "").replace(",", ".")
        found.append({
            "field_type": "AMOUNT", 
            "span_text": m.group(), 
            "start_char": m.start(), 
            "end_char": m.end(), 
            "norm": f"{val} {m.group(2).upper()}"
        })
    return found

def extract_phones(text):
    pattern = r'(\+?38)?\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}'
    found = []
    t = str(text)
    for m in re.finditer(pattern, t):
        nums = re.sub(r'\D', '', m.group())
        found.append({
            "field_type": "PHONE", 
            "span_text": m.group(), 
            "start_char": m.start(), 
            "end_char": m.end(), 
            "norm": f"+{nums}"
        })
    return found

def extract_all(text):
    """Об'єднує всі результати в один плаский список"""
    return extract_dates(text) + extract_amounts(text) + extract_phones(text)