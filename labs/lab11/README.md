# ЛР11: LLM extraction (schema-first)

## 1. Extraction кейс
8 полів з відгуків про сервіси. Корпус: processed_v2.csv.

## 2. Schema
JSON schema Draft-7, 8 required полів. src/json_schema.py.

## 3. Baseline prompt
Schema-first system prompt. src/llm_extract.py.

## 4. Validator
JSON parse + jsonschema. src/validator.py.

## 5. Repair loop
Max 2 спроби. src/repair_loop.py.

## 6. Valid JSON rate
Raw: ~70% | Post-repair: ~95%

## 7. Проблеми що залишаються
Semantic errors, normalization ambiguity, service_type ambiguity.

## Файли
notebooks/lab11_llm_extraction_schema_first.ipynb
src/json_schema.py, src/llm_extract.py, src/validator.py, src/repair_loop.py
docs/audit_summary_lab11.md, docs/extraction_schema_lab11.md