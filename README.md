# Аналіз відповідей з українських опитувань

> **NLP Курсовий проєкт · Напрям D — Кластеризація та класифікація**
>
> Датасет: [Kaggle «Answers to the survey in Ukrainian»](https://www.kaggle.com/datasets/annzhukova340/data-set-for-detailed-questions-from-surveys) · Ann Zhukova, 2023

---

## Зміст

- [Про проєкт](#про-проєкт)
- [Структура репозиторію](#структура-репозиторію)
- [Датасет](#датасет)
- [Огляд лабораторних](#огляд-лабораторних)
- [Ключові результати](#ключові-результати)
- [Як запускати](#як-запускати)
- [Залежності](#залежності)

---

## Про проєкт

Щороку в Україні збирають тисячі відповідей на відкриті питання опитувань — про сервіси, освіту, міську інфраструктуру, громаду. Ці тексти короткі, розмовні, неструктуровані й практично не аналізуються автоматично.

**Мета проєкту** — побудувати повний NLP-pipeline для автоматичного аналізу таких текстів:

1. Класифікація тональності (позитив / негатив)
2. Виявлення тематичних кластерів без ручної розмітки
3. Витяг іменованих сутностей (NER)
4. Надійний structured extraction через LLM із schema-first підходом
5. Інтелектуальний agent/flow pipeline із аудитом та validation

---

## Структура репозиторію

```
.
├── data/
│   ├── raw/                        # Вихідний CSV (не змінюється)
│   ├── processed_v2.csv            # Очищений корпус (основний)
│   └── sample/                     # Малий зразок для Colab/GitHub
│
├── docs/
│   ├── dataset_card.md             # Опис датасету, ризики, оновлення
│   ├── preprocess_policy.md        # Правила нормалізації
│   ├── ie_policy.md                # Правила rule-based extraction
│   ├── leakage_risk_report_lab5.md # Звіт про leakage та дублікати
│   ├── audit_summary_lab2.md       # Підсумок ЛР2
│   ├── audit_summary_lab3.md       # Підсумок ЛР3
│   ├── audit_summary_lab4.md       # Підсумок ЛР4
│   ├── audit_summary_lab5.md       # Підсумок ЛР5
│   ├── audit_summary_lab6.md       # Підсумок ЛР6
│   ├── audit_summary_lab7.md       # Підсумок ЛР7
│   ├── audit_summary_lab8.md       # Підсумок ЛР8
│   ├── audit_summary_lab9.md       # Підсумок ЛР9
│   ├── audit_summary_lab10.md      # Підсумок ЛР10
│   ├── audit_summary_lab11.md      # Підсумок ЛР11
│   ├── audit_summary_lab12.md      # Підсумок ЛР12
│   ├── audit_summary_lab13.md      # Підсумок ЛР13
│   ├── audit_summary_lab14.md      # Підсумок ЛР14
│   ├── topic_notes_lab8.md         # Ручна інтерпретація тем LDA
│   ├── embedding_notes_lab9.md     # Аналіз Word2Vec vs FastText
│   ├── ner_notes_lab10.md          # NER pipeline нотатки
│   ├── extraction_schema_lab11.md  # JSON schema для LLM extraction
│   ├── agent_notes_lab12.md        # Single-agent нотатки
│   ├── crew_notes_lab13.md         # Multi-agent crew нотатки
│   ├── flow_notes_lab14.md         # Flow orchestration нотатки
│   ├── memory_policy_lab14.md      # Memory/state policy
│   ├── tool_logs_lab12.jsonl       # Логи tool calls (ЛР12)
│   ├── crew_logs_lab13.jsonl       # Логи crew pipeline (ЛР13)
│   └── flow_logs_lab14.jsonl       # Логи stateful flow (ЛР14)
│
├── notebooks/
│   ├── lab2_preprocessing.ipynb
│   ├── lab3_ling_features.ipynb
│   ├── lab4_ie_rules.ipynb
│   ├── lab5_splits_leakage.ipynb
│   ├── lab6_tfidf_logistic_baseline.ipynb
│   ├── lab7_linear_svm_char_ngrams.ipynb
│   ├── lab8_topic_modeling_lsa_lda.ipynb
│   ├── lab9_word_embeddings_fasttext_word2vec.ipynb
│   ├── lab10_ner_pipeline_hybrid_rules.ipynb
│   ├── lab11_llm_extraction_schema_first.ipynb
│   ├── lab12_tool_grounded_single_agent.ipynb
│   ├── lab13_multi_agent_crew_triager_extractor_reviewer.ipynb
│   └── lab14_flow_orchestration_crewai_flows.ipynb
│
├── src/
│   ├── preprocess.py               # Нормалізація тексту (ЛР2)
│   ├── ling_features.py            # Лематизація та POS (ЛР3)
│   ├── ie_rules.py                 # Rule-based extraction (ЛР4)
│   ├── split.py                    # Стратифікований split (ЛР5)
│   ├── classification_baseline.py  # TF-IDF + LogReg (ЛР6)
│   ├── svm_experiments.py          # LinearSVC experiments (ЛР7)
│   ├── threshold_eval.py           # PR-curve та threshold (ЛР7)
│   ├── topic_modeling.py           # LSA / LDA (ЛР8)
│   ├── topic_utils.py              # Візуалізація тем (ЛР8)
│   ├── embeddings_train.py         # Word2Vec / FastText (ЛР9)
│   ├── embeddings_eval.py          # Nearest neighbors (ЛР9)
│   ├── ner_pipeline.py             # spaCy NER inference (ЛР10)
│   ├── ner_rules.py                # Hybrid rules layer (ЛР10)
│   ├── ner_eval.py                 # NER evaluation set (ЛР10)
│   ├── json_schema.py              # JSON schema для extraction (ЛР11)
│   ├── llm_extract.py              # Промпти та API call (ЛР11)
│   ├── validator.py                # JSON parse + schema validation (ЛР11, ЛР14)
│   ├── repair_loop.py              # Repair loop (ЛР11)
│   ├── tools.py                    # Tool-функції для агента (ЛР12)
│   ├── tool_logger.py              # Логування tool calls (ЛР12)
│   ├── agent.py                    # Single-agent controller (ЛР12)
│   ├── eval_agent.py               # Test cases + metrics (ЛР12)
│   ├── agents.py                   # Triager / Extractor / Reviewer (ЛР13)
│   ├── fallback.py                 # FallbackAgent (ЛР13, ЛР14)
│   ├── crew_workflow.py            # Crew orchestrator (ЛР13)
│   ├── eval_crew.py                # Crew test cases (ЛР13)
│   ├── flow_state.py               # FlowState dataclass (ЛР14)
│   ├── flow.py                     # Flow orchestrator (ЛР14)
│   ├── router.py                   # Route step (ЛР14)
│   ├── executor.py                 # Execute step (ЛР14)
│   ├── exporter.py                 # Export step (ЛР14)
│   └── eval_flow.py                # Flow test cases (ЛР14)
│
├── labs/
│   ├── lab02/  lab03/  lab04/
│   ├── lab05/  lab06/  lab07/
│   ├── lab08/  lab09/  lab10/
│   ├── lab11/  lab12/  lab13/
│   └── lab14/                      # Кожна: README.md + requirements.txt
│
└── tests/
    ├── edge_cases.jsonl
    ├── ie_edge_cases.jsonl
    └── ling_edge_cases.jsonl
```

---

## Датасет

| Параметр | Значення |
|---|---|
| Джерело | Kaggle · Ann Zhukova, 2023 |
| Початковий розмір | 18 310 рядків |
| Після фільтрації | 9 522 унікальних тексти |
| Розмічено вручну | 4 387 прикладів (46%) |
| Клас 0 (негатив) | 1 902 (43.4%) |
| Клас 1 (позитив) | 2 485 (56.6%) |
| Середня довжина | 12.5 слів |
| Мова | Українська |
| Домени | Сервіс, освіта, ціни, логістика, техніка, громада |

**Splits** (seed=42, stratified):

| Split | Розмір |
|---|---|
| Train | 3 070 |
| Val | 658 |
| Test | 659 |

Точних дублів між train ↔ test: **0**

---

## Огляд лабораторних

### ЛР1 — Постановка задачі
Вибір датасету, напряму D, визначення задачі кластеризації та класифікації.

### ЛР2 — Нормалізація тексту
`src/preprocess.py` · Pipeline: lowercase → видалення пунктуації → PII masking (`<URL>`, `<EMAIL>`, `<PHONE>`) → sentence segmentation (`|`). Результат: `data/processed_v2.csv`.

### ЛР3 — Лінгвістичні ознаки
`src/ling_features.py` · Stanza (uk): лематизація → `lemma_text`, POS-теги → `pos_seq`. Приріст від лемем: Accuracy +2.35%, Macro-F1 +2.75%.

### ЛР4 — Rule-based Information Extraction
`src/ie_rules.py` · Regex-правила: AMOUNT (P=0.93), DATE (P=0.80), PHONE (P=1.0), EMAIL (P=1.0). Evaluation на 50 вручну анотованих реченнях.

### ЛР5 — Splits та Leakage
`src/split.py` · Stratified 70/15/15, seed=42. Аудит точних дублів (exact match) та near-дублів (cosine > 0.95) між train↔val↔test. Звіт: `docs/leakage_risk_report_lab5.md`.

### ЛР6 — TF-IDF + Logistic Regression baseline
`src/classification_baseline.py` · Baseline 1 (unigrams): Accuracy 0.8528, F1 0.8445. Baseline 2 (bigrams + balanced): Accuracy 0.8968, F1 0.8944. Використано `sklearn.Pipeline` — TF-IDF fit тільки на train.

### ЛР7 — Linear SVM + char-ngrams
`src/svm_experiments.py` · LinearSVC word(1,2) + char_wb(3,5) + balanced: Accuracy ~0.91, Macro-F1 ~0.90. PR-curve та threshold analysis (`src/threshold_eval.py`). Recall-first логіка для моніторингу скарг.

### ЛР8 — Topic Modeling: LSA / LDA
`src/topic_modeling.py` · LSA (TF-IDF + TruncatedSVD) та LDA (CountVectorizer + LatentDirichletAllocation). k=5 та k=8 для обох. LDA k=8 переміг: 5/8 тем чіткі та підтверджені документами. Теми: Ціни/якість, Сервіс, Освіта, Доставка, Асортимент.

### ЛР9 — Word Embeddings: Word2Vec / FastText
`src/embeddings_train.py` · sg=1, vector_size=100, window=5, min_count=3, seed=42. Корпус ~119K токенів. FastText > Word2Vec для морфологічно багатої укр. мови. Аналіз 10 слів + 5 доменних термінів + 5 кейсів «корисно/некорисно».

### ЛР10 — NER Pipeline + Hybrid Rules
`src/ner_pipeline.py`, `src/ner_rules.py` · spaCy `uk_core_news_sm` + 4 гібридні правила: MONEY regex, ORG-словник (9 записів: Скайфлай, Інгліш Хаб, Shimano…), PRODUCT-словник, DATE regex. Evaluation set: 25 вручну анотованих речень. Результат: +8 ORG, +2 MONEY, +2 PRODUCT.

### ЛР11 — LLM Extraction (schema-first)
`src/json_schema.py`, `src/llm_extract.py`, `src/validator.py`, `src/repair_loop.py` · 8 required полів, JSON schema Draft-7, `additionalProperties: false`. Repair loop (max 2 спроби). Valid JSON rate: ~70% → ~95% після repair. Evaluation set: 20 прикладів з gold-мітками.

### ЛР12 — Tool-grounded Single-Agent
`src/tools.py`, `src/tool_logger.py`, `src/agent.py` · 5 tool-функцій: `lookup_known_service`, `classify_review`, `extract_entities`, `validate_required_fields`, `score_review_completeness`. Tool call success rate: 100% (47/47). Avg 4.7 calls/task. Умовна логіка: `extract_entities` викликається тільки при потребі.

### ЛР13 — Multi-agent Crew
`src/agents.py`, `src/crew_workflow.py`, `src/fallback.py` · 4 агенти: Triager (route selection) → Extractor (JSON extraction) → Reviewer (consistency + hallucination check) → FallbackAgent (rule repair → partial → manual review). Valid final: 90%. Avg 2.2 agents/case.

### ЛР14 — Stateful Flow Orchestration
`src/flow_state.py`, `src/flow.py`, `src/router.py`, `src/executor.py`, `src/validator.py`, `src/exporter.py`, `src/fallback.py` · Pipeline: ingest → route → execute → validate → [fallback] → export. `FlowState` dataclass — єдиний mutable state. Flow completion: 100%. Export valid: 100% (structured output навіть при safe_failure). Memory policy: `docs/memory_policy_lab14.md`.

---

## Ключові результати

| Задача | Метод | Результат |
|---|---|---|
| Класифікація тональності | LinearSVC + char-ngrams | Accuracy ~91%, Macro-F1 ~90% |
| Тематична структура | LDA k=8 | 5/8 тем чіткі, 6 доменів виявлено |
| Word embeddings | FastText (subword) | Перевершує W2V на морфології укр. мови |
| NER hybrid | spaCy + 4 правила | +12 нових entities (ORG, MONEY, PRODUCT) |
| LLM extraction | Schema-first + repair | Valid JSON: 70% → 95% після repair loop |
| Single-agent | 5 tools | Tool success 100%, Avg 4.7 calls/task |
| Multi-agent crew | 4 agents | Valid final 90%, structured audit logs |
| Stateful flow | 5-step pipeline | Completion 100%, Export valid 100% |

**Найкраща модель класифікації:** LinearSVC word(1,2) + char_wb(3,5) + `class_weight='balanced'`

**Чому char-ngrams допомогли:** захоплюють заперечення («не_плутається»), морфологічні варіанти та специфічний лексикон скарг у коротких реченнях.

---

## Як запускати

### Локально

```bash
# Клонувати репозиторій
git clone <repo-url>
cd <repo>

# Встановити залежності для конкретної лаби
pip install -r labs/lab6/requirements.txt

# Запустити ноутбук
jupyter notebook notebooks/lab6_tfidf_logistic_baseline.ipynb
```

### Google Colab

Кожен ноутбук містить стандартний блок на початку:

```python
# 1. Встановити залежності
# !pip install -r labs/labXX/requirements.txt

# 2. Підключити Google Drive
# from google.colab import drive
# drive.mount('/content/drive')
# DATA_PATH = '/content/drive/MyDrive/<шлях>/data/processed_v2.csv'

# 3. Додати src/ до sys.path
import sys, os
SRC_PATH = os.path.abspath('../src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
```

Після цього: `Runtime → Restart and Run All`.

### Важливо для VS Code

Якщо ноутбуки ЛР12–14 дають `ImportError` через конфлікт імен модулів (наприклад, `tools.py` є в кількох папках), додайте на початку Cell 2:

```python
# Очистити старі шляхи
sys.path = [p for p in sys.path if not any(
    f'lab{n}' in p for n in ['12','13','14','10','11']
)]
sys.path.insert(0, os.path.abspath('../src'))
```

---

## Залежності

Основні пакети (повний список у `labs/labXX/requirements.txt`):

| Пакет | Версія | Використання |
|---|---|---|
| `pandas` | ≥1.5 | Обробка даних |
| `scikit-learn` | ≥1.2 | Класифікація, TF-IDF, LDA |
| `spacy` | ≥3.6 | NER pipeline |
| `stanza` | ≥1.5 | Лематизація (uk) |
| `gensim` | ≥4.3 | Word2Vec, FastText |
| `matplotlib` | ≥3.6 | Візуалізація |
| `jsonschema` | ≥4.17 | Валідація JSON schema |
| `requests` | ≥2.28 | Anthropic API calls (ЛР11) |

Встановлення моделі spaCy:
```bash
python -m spacy download uk_core_news_sm
```

---

## Відтворюваність

- Усі splits фіксовані: `seed=42`, stratified
- TF-IDF fit **тільки на train** (через `sklearn.Pipeline`)
- Word2Vec / FastText: `seed=42`, однакові параметри для чесного порівняння
- Flow / Agent: детерміновані rule-based функції, не залежать від API при симуляції
- Логи: `docs/tool_logs_lab12.jsonl`, `docs/crew_logs_lab13.jsonl`, `docs/flow_logs_lab14.jsonl`

---

## Обмеження та відкриті питання

- **Малий корпус** (~119K токенів) — недостатньо для стабільних власних embeddings; рекомендується pretrained FastText (lang-uk / facebook/fasttext-uk)
- **Змішані домени** — 6 тематичних доменів в одному корпусі ускладнюють чіткий поділ на теми при малому k
- **Mixed-sentiment detection** — рівна кількість pos/neg keywords → neutral; потребує кращої логіки
- **Телеком/веб домени** — не покриті NER словниками та SERVICE_TYPE_KW
- **Відносні дати** («торік», «минулого місяця») — не витягуються regex-правилами

**Наступний крок:** fine-tuned mBERT / XLM-RoBERTa + більший корпус + entity linking для повного NLU pipeline.

---

*Проєкт розроблено в рамках курсу NLP. Всі дані — відкриті (Kaggle CC0). Репозиторій містить тільки `data/sample/` — повний датасет завантажується окремо за посиланням вище.*