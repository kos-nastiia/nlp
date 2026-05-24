# Extraction Schema Lab 11

## 1. Extraction task
З відгуку про сервіс витягти 8 полів. Корпус: processed_v2.csv (Напрям D).

## 2. Поля

| Поле | Тип | Required | Опис |
|------|-----|---------|------|
| service_name | string|null | yes | Назва компанії або null |
| service_type | enum|null | yes | авіакомпанія/ресторан/кафе/магазин/школа/автосервіс/готель/доставка/медицина/освіта/спорт/інше/null |
| sentiment | enum | yes | positive/negative/mixed/neutral |
| issue_type | enum|null | yes | billing/quality/delivery/support/staff/facility/logistics/null |
| mentioned_price | number|null | yes | Числова сума або null |
| currency | enum|null | yes | UAH/USD/EUR/null |
| key_aspect | string | yes | Головний аспект до 10 слів |
| confidence | enum | yes | high/medium/low |

## 3. JSON schema
Повна schema: src/json_schema.py -> EXTRACTION_SCHEMA (Draft-7, additionalProperties: false).

## 4. Правила null
- service_name: null якщо назва не згадана
- issue_type: null якщо sentiment=positive
- mentioned_price: null якщо сума відсутня
- currency: null якщо mentioned_price=null

## 5. Поля що найчастіше ламаються
1. confidence — пропускається при великій схемі
2. mentioned_price — string замість number
3. sentiment — укр. слово замість eng enum
4. service_type — амбігуерний для загальних відгуків

## 6. Що repair loop виправляє
+ markdown wrap, missing field, wrong enum, wrong type, hallucinated field
- semantic errors, normalization ambiguity