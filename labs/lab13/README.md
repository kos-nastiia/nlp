# ЛР13: Multi-agent Crew (Triager → Extractor → Reviewer)

## 1. Use case
Support Assistant Crew для structured аналізу відгуків. Напрям D.

## 2. Agents
Triager, Extractor, Reviewer, FallbackAgent.

## 3. Workflow
Triager → Extractor → Reviewer → (FallbackAgent → re-Reviewer → max 2 attempts)

## 4. Delegation rules
1. Triager завжди перший (route selection)
2. Extractor за schema від Triager
3. Reviewer завжди перевіряє
4. accept → finalize
5. repair_needed → FallbackAgent → re-review
6. Max 2 repair attempts → manual_review

## 5. Reviewer checks
Schema (required fields), consistency (sentiment vs signals), hallucination (price/name in text), issue_type logic.

## 6. Fallback
Rule-based repair → partial output → manual_review flag.

## 7. Запуск
```bash
pip install -r labs/lab13/requirements.txt
jupyter notebook notebooks/lab13_multi_agent_crew_triager_extractor_reviewer.ipynb
# Kernel → Restart & Run All
```

## 8. Logs
docs/crew_logs_lab13.jsonl (10 рядків, 1 case = 1 рядок)

## 9. Метрики
- Valid final rate: 90%
- Fallback activation: 10%
- Manual review: 10%
- Avg agents/case: 2.2

## 10. Висновок
Crew дає validated structured output + audit trail. Overhead виправданий для ambiguous/complex кейсів. Для простих відгуків — Reviewer приймає без fallback.