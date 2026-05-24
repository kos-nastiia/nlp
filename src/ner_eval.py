"""
ner_eval.py — ЛР10: оцінка NER pipeline та структурований error analysis.
"""

import pandas as pd
from collections import defaultdict, Counter

EVAL_SET = [
    {
        "id": 1,
        "text": "гідравлічні гальма shimano працюють чітко і плавно",
        "entities": [{"text": "shimano", "label": "ORG"}],
        "notes": "Shimano — бренд/компанія"
    },
    {
        "id": 2,
        "text": "трансмісія shimano deore оптимальне поєднання ціни і якості | 12 швидкостей вистачає для будьяких схилів",
        "entities": [
            {"text": "shimano deore", "label": "PRODUCT"},
            {"text": "shimano", "label": "ORG"},
        ],
        "notes": "Shimano ORG + Deore — product line"
    },
    {
        "id": 3,
        "text": "авіакомпанія скайфлай це відмінний вибір для подорожей | нові літаки",
        "entities": [{"text": "скайфлай", "label": "ORG"}],
        "notes": "Скайфлай — авіакомпанія"
    },
    {
        "id": 4,
        "text": "багаж на рейсах скайфлай часто губиться або пошкоджується",
        "entities": [{"text": "скайфлай", "label": "ORG"}],
        "notes": "Скайфлай — авіакомпанія"
    },
    {
        "id": 5,
        "text": "служба підтримки скайфлай працює жахливо | дозвонитись до оператора майже неможливо",
        "entities": [{"text": "скайфлай", "label": "ORG"}],
        "notes": "Скайфлай — авіакомпанія"
    },
    {
        "id": 6,
        "text": "інгліш хаб це чудова можливість вивчити англійську не виходячи з дому | зручний графік занять",
        "entities": [{"text": "інгліш хаб", "label": "ORG"}],
        "notes": "Інгліш Хаб — школа англійської"
    },
    {
        "id": 7,
        "text": "ціни на навчання в інгліш хаб цілком доступні",
        "entities": [{"text": "інгліш хаб", "label": "ORG"}],
        "notes": "Інгліш Хаб — школа"
    },
    {
        "id": 8,
        "text": "інгліш хаб піклується про своїх учнів навіть поза класом | регулярні розсилки з корисними порадами",
        "entities": [{"text": "інгліш хаб", "label": "ORG"}],
        "notes": "Інгліш Хаб — школа"
    },
    {
        "id": 9,
        "text": "ціни в кавярні не відповідають якості | за таку посередню каву та нудні десерти платити майже 100 грн за порцію це занадто",
        "entities": [{"text": "100 грн", "label": "MONEY"}],
        "notes": "Ціна — MONEY"
    },
    {
        "id": 10,
        "text": "ціни в барі клубу шокують | за один смузі чи протеїновий батончик можна легко викласти 200300 грн | простіше з собою брати",
        "entities": [{"text": "200300 грн", "label": "MONEY"}],
        "notes": "Ціна — MONEY"
    },
    {
        "id": 11,
        "text": "мене тішить високий професіоналізм викладацького складу у наших школах та університетах",
        "entities": [],
        "notes": "Немає конкретних сутностей — загальна фраза"
    },
    {
        "id": 12,
        "text": "торік було відкрито центр надання адмінпослуг",
        "entities": [{"text": "торік", "label": "DATE"}],
        "notes": "DATE — відносна дата"
    },
    {
        "id": 13,
        "text": "програма лояльності скайфлай дозволяє накопичувати милі за кожен переліт та обмінювати їх на знижки",
        "entities": [{"text": "скайфлай", "label": "ORG"}],
        "notes": "Скайфлай — ORG"
    },
    {
        "id": 14,
        "text": "це найгірша школа іноземних мов",
        "entities": [],
        "notes": "Немає конкретних NE — анонімна"
    },
    {
        "id": 15,
        "text": "у моєму районі регулярно проводяться різні культурні заходи за підтримки муніципалітету",
        "entities": [],
        "notes": "Немає конкретних NE"
    },
    {
        "id": 16,
        "text": "ціни на окуляри та послуги салонів оптики завищені та не відповідають якості продукції",
        "entities": [],
        "notes": "Немає конкретних NE — ціна без суми"
    },
    {
        "id": 17,
        "text": "дизайн wh1000xm4 дуже стильний та ергономічний | навушники зручно сидять на голові",
        "entities": [{"text": "wh1000xm4", "label": "PRODUCT"}],
        "notes": "Модель навушників Sony — PRODUCT"
    },
    {
        "id": 18,
        "text": "місцева влада не дбає про благоустрій | парки та сквери занедбані",
        "entities": [],
        "notes": "Немає конкретних NE"
    },
    {
        "id": 19,
        "text": "заборона пластикових пакетів незручна для споживачів | не завжди є можливість носити з собою багаторазову сумку",
        "entities": [],
        "notes": "Немає NE"
    },
    {
        "id": 20,
        "text": "акумулятора вистачає на 2025 хвилин безперервної роботи",
        "entities": [],
        "notes": "2025 — число хвилин, не рік (ambiguous)"
    },
    {
        "id": 21,
        "text": "рейси авіакомпанії скайфлай часто затримуються або скасовуються",
        "entities": [{"text": "скайфлай", "label": "ORG"}],
        "notes": "Скайфлай — ORG"
    },
    {
        "id": 22,
        "text": "місця в літаках скайфлай дуже тісні та незручні | коліна впираються в передню спинку",
        "entities": [{"text": "скайфлай", "label": "ORG"}],
        "notes": "Скайфлай — ORG"
    },
    {
        "id": 23,
        "text": "квитки на рейси скайфлай часто можна купити зі знижками або за акційними цінами",
        "entities": [{"text": "скайфлай", "label": "ORG"}],
        "notes": "Скайфлай — ORG"
    },
    {
        "id": 24,
        "text": "персонал скайфлай дуже професійний та уважний | стюардеси завжди готові допомогти з багажем",
        "entities": [{"text": "скайфлай", "label": "ORG"}],
        "notes": "Скайфлай — ORG"
    },
    {
        "id": 25,
        "text": "в процесі виготовлення альбому дизайнер допустив кілька помилок у підписах та датах",
        "entities": [],
        "notes": "Немає NE — загальний текст"
    },
]

def rough_eval(predicted: list, gold: list) -> dict:
    """
    Підраховує correct / missed / false_positive по типах сутностей.
    predicted і gold — списки результатів NER (той самий формат).
    """
    stats = defaultdict(lambda: {"correct": 0, "missed": 0, "fp": 0})
    total = {"correct": 0, "missed": 0, "fp": 0}

    for pred, gld in zip(predicted, gold):
        pred_ents = {(e["text"].lower(), e["label"]) for e in pred["entities"]}
        gold_ents = {(e["text"].lower(), e["label"]) for e in gld["entities"]}

        for ent in gold_ents:
            if ent in pred_ents:
                stats[ent[1]]["correct"] += 1
                total["correct"] += 1
            else:
                stats[ent[1]]["missed"] += 1
                total["missed"] += 1

        for ent in pred_ents:
            if ent not in gold_ents:
                stats[ent[1]]["fp"] += 1
                total["fp"] += 1

    return {"by_label": dict(stats), "total": total}


def print_eval(eval_result: dict):
    rows = []
    for label, v in eval_result["by_label"].items():
        tp = v["correct"]
        fp = v["fp"]
        fn = v["missed"]
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec  = tp / (tp + fn) if (tp + fn) > 0 else 0
        rows.append({
            "Label":     label,
            "Correct":   tp,
            "Missed(FN)": fn,
            "FP":        fp,
            "Precision": round(prec, 3),
            "Recall":    round(rec, 3),
        })
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    t = eval_result["total"]
    print(f"\nTotal — Correct: {t['correct']} | Missed: {t['missed']} | FP: {t['fp']}")

# Категорії помилок:
ERROR_CATEGORIES = [
    "boundary error",        
    "type error",          
    "missed domain entity", 
    "false positive",     
    "tokenization issue",
    "ambiguous case",     
    "normalization issue", 
]

MANUAL_ERRORS = [
    {
        "id": 1,
        "text": "трансмісія shimano deore оптимальне поєднання ціни і якості",
        "expected": "shimano deore [PRODUCT]",
        "predicted": "shimano [ORG]",
        "category": "boundary error",
        "explanation": "Baseline знайшов 'shimano' як ORG, але не захопив 'deore'. "
                       "Span неповний — потрібно захоплювати 'shimano deore' цілком.",
    },
    {
        "id": 2,
        "text": "авіакомпанія скайфлай це відмінний вибір",
        "expected": "скайфлай [ORG]",
        "predicted": "—",
        "category": "missed domain entity",
        "explanation": "uk_core_news_sm не знає 'Скайфлай' — вигаданий бренд. "
                       "Baseline пропустив, словниковий EntityRuler виправив.",
    },
    {
        "id": 3,
        "text": "інгліш хаб це чудова можливість вивчити англійську",
        "expected": "інгліш хаб [ORG]",
        "predicted": "—",
        "category": "missed domain entity",
        "explanation": "Двослівна назва школи. Baseline розбиває або ігнорує. "
                       "PhraseMatcher/словник покриває цей клас помилок.",
    },
    {
        "id": 4,
        "text": "платити майже 100 грн за порцію це занадто",
        "expected": "100 грн [MONEY]",
        "predicted": "—",
        "category": "missed domain entity",
        "explanation": "Стандартний uk_core_news_sm не розпізнає гривні без спец. "
                       "тренування. Regex-правило MONEY виправив.",
    },
    {
        "id": 5,
        "text": "за один смузі можна легко викласти 200300 грн",
        "expected": "200300 грн [MONEY]",
        "predicted": "—",
        "category": "missed domain entity",
        "explanation": "Нестандартний запис діапазону без пробілу. "
                       "Regex охоплює паттерн \\d+\\d+ грн.",
    },
    {
        "id": 6,
        "text": "дизайн wh1000xm4 дуже стильний",
        "expected": "wh1000xm4 [PRODUCT]",
        "predicted": "—",
        "category": "missed domain entity",
        "explanation": "Технічна назва продукту — суто алфанумерична. "
                       "Жоден загальний NER не знає цей бренд без словника.",
    },
    {
        "id": 7,
        "text": "акумулятора вистачає на 2025 хвилин безперервної роботи",
        "expected": "— (2025 = кількість хвилин, не дата)",
        "predicted": "2025 [DATE]",
        "category": "false positive",
        "explanation": "Regex DATE ловить '2025' як рік, але тут це число хвилин. "
                       "Ambiguous: потрібен контекстний аналіз ('хвилин' поруч).",
    },
    {
        "id": 8,
        "text": "мене тішить високий рівень освіти у наших університетах",
        "expected": "— (загальна фраза, без конкретного NE)",
        "predicted": "університетах [ORG]",
        "category": "false positive",
        "explanation": "Baseline класифікував загальне слово як ORG. "
                       "Відсутній конкретний референт — false positive.",
    },
    {
        "id": 9,
        "text": "у нашому місті функціонують державні та приватні клініки",
        "expected": "—",
        "predicted": "клініки [ORG]",
        "category": "false positive",
        "explanation": "Загальна назва типу установи, не конкретна організація. "
                       "Baseline помилково відносить до ORG.",
    },
    {
        "id": 10,
        "text": "розклад рейсів скайфлай дуже зручний",
        "expected": "скайфлай [ORG]",
        "predicted": "—",
        "category": "missed domain entity",
        "explanation": "Словниково-невідомий бренд. Покривається правилом ORG-словника.",
    },
    {
        "id": 11,
        "text": "персонал скайфлай дуже професійний",
        "expected": "скайфлай [ORG]",
        "predicted": "персонал скайфлай [ORG]",
        "category": "boundary error",
        "explanation": "Baseline захопив 'персонал скайфлай' — занадто широко. "
                       "Правильна межа: тільки 'скайфлай'.",
    },
    {
        "id": 12,
        "text": "програма лояльності скайфлай дозволяє накопичувати милі",
        "expected": "скайфлай [ORG]",
        "predicted": "програма лояльності скайфлай [ORG]",
        "category": "boundary error",
        "explanation": "Те саме — baseline розширив span на попередній контекст.",
    },
    {
        "id": 13,
        "text": "торік було відкрито центр надання адмінпослуг",
        "expected": "торік [DATE]",
        "predicted": "—",
        "category": "missed domain entity",
        "explanation": "Відносна дата 'торік' — не покрита regex-правилом (числові дати). "
                       "Потрібне додаткове правило для відносних часових виразів.",
    },
    {
        "id": 14,
        "text": "гідравлічні гальма shimano працюють чітко і плавно",
        "expected": "shimano [ORG]",
        "predicted": "shimano [ORG]",
        "category": "— (correct)",
        "explanation": "Правило ORG-словника правильно знайшло shimano. "
                       "Цей кейс — приклад успішної роботи гібридного шару.",
    },
    {
        "id": 15,
        "text": "обіцяний розмовний клуб в інгліш хаб виявився профанацією",
        "expected": "інгліш хаб [ORG]",
        "predicted": "—",
        "category": "missed domain entity",
        "explanation": "Той самий тип що id=3. Підтверджує системність проблеми "
                       "з двослівними назвами-незнайомками для baseline.",
    },
    {
        "id": 16,
        "text": "у нашому місті відкрили новий центр",
        "expected": "—",
        "predicted": "центр [ORG]",
        "category": "false positive",
        "explanation": "Загальне слово 'центр' без власної назви — не NE. "
                       "Baseline надто агресивний на загальних ORG-словах.",
    },
]

def error_analysis_df(errors: list = None) -> pd.DataFrame:
    if errors is None:
        errors = MANUAL_ERRORS
    rows = []
    for e in errors:
        rows.append({
            "id":          e["id"],
            "text":        e["text"][:80],
            "expected":    e["expected"],
            "predicted":   e["predicted"],
            "category":    e["category"],
            "explanation": e["explanation"][:120],
        })
    return pd.DataFrame(rows)

def error_summary(errors: list = None) -> pd.DataFrame:
    if errors is None:
        errors = MANUAL_ERRORS
    cats = [e["category"] for e in errors if e["category"] != "— (correct)"]
    cnt = Counter(cats)
    df = pd.DataFrame(
        [{"category": k, "count": v} for k, v in cnt.most_common()]
    )
    return df