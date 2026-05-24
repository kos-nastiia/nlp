# ЛР12: Tool-grounded Single Agent

## 1. Use case
Support Assistant для аналізу відгуків. Напрям D.

## 2. Agent task
Classify sentiment, extract entities, validate, route.

## 3. Tools (5)
- lookup_known_service, classify_review, extract_entities
- validate_required_fields, score_review_completeness

## 4. Запуск
```bash
pip install -r labs/lab12/requirements.txt
jupyter notebook notebooks/lab12_tool_grounded_single_agent.ipynb
# Kernel -> Restart & Run All
```

## 5. Logs
docs/tool_logs_lab12.jsonl (47 записів, 10 задач)

## 6. Test cases
10 сценаріїв: simple, missing_data, noisy, empty_result, unnecessary_tool,
ambiguous, two_tools_needed, validator_finds_issue, tool_output_in_answer, tool_not_helpful.

## 7. Метрики
- Tool call success rate: 100%
- Avg calls/task: 4.7
- Tasks with useful tools: 8/10
- Unnecessary calls: 0

## 8. Висновок
Tools дали структурований output та routing decision. Умовна логіка
правильно пропустила зайві виклики. Проблеми: відсутні telecom/finance у словниках.