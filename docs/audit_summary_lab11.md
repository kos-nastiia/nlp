# Audit Summary Lab 11 - LLM extraction schema-first

## 1. Task
Structured extraction з відгуків про сервіси (8 полів).

## 2. Eval set
20 прикладів з gold-мітками.

## 3. Raw valid JSON rate
Parse: 19/20 (95.0%) | Schema: 15/20 (75.0%)

## 4. Post-repair valid JSON rate
Schema OK: 20/20 (100.0%) | Improvement: +5

## 5. Поля що ламались
confidence (пропуск), mentioned_price (string vs number), sentiment (ukr enum)

## 6. Типи помилок
1. missing field 2. wrong type 3. wrong enum 4. not JSON 5. hallucinated field

## 7. Висновок
Valid JSON rate: 75.0% -> 100.0% після repair. Schema-first pipeline стабільний.