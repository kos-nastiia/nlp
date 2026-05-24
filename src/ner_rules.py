import re
import spacy
from spacy.language import Language
from spacy.tokens import Span


KNOWN_ORGS = [
    "скайфлай", "skyfly",
    "інгліш хаб", "english hub",
    "нова пошта", "новапошта",
    "укрпошта",
    "приватбанк", "privatbank",
    "монобанк", "monobank",
    "міська рада",
    "shimano",
    "монтессорі",
]

KNOWN_PRODUCTS = [
    "shimano deore",
    "wh-1000xm4", "wh1000xm4",
    "shimano xt",
]

MONEY_PATTERN = re.compile(
    r'\b\d+(?:[–\-]\d+)?\s*(?:грн|гривень|гривні|\$|євро|uah|usd|%)\b',
    re.IGNORECASE
)

DATE_PATTERN = re.compile(
    r'\b(?:\d{1,2}[./]\d{1,2}[./]\d{2,4}|\d{4}\s*(?:рок[иу]?|р\.?))\b',
    re.IGNORECASE
)

ORDER_PATTERN = re.compile(
    r'(?:№|#)\s*\d{5,}|\b[A-Z]{2}\d{8,}[A-Z]{2}\b'
)

def apply_rules(doc):
    existing_spans = list(doc.ents)
    covered = set()
    for ent in existing_spans:
        for i in range(ent.start_char, ent.end_char):
            covered.add(i)

    new_ents = []

    def add_span(start, end, label):
        """Додає span якщо не перекривається з існуючими."""
        if any(i in covered for i in range(start, end)):
            return
        span = doc.char_span(start, end, label=label, alignment_mode="expand")
        if span is not None:
            new_ents.append(span)
            for i in range(start, end):
                covered.add(i)

    text = doc.text

    for m in MONEY_PATTERN.finditer(text):
        add_span(m.start(), m.end(), "MONEY")

    for m in DATE_PATTERN.finditer(text):
        add_span(m.start(), m.end(), "DATE")

    for m in ORDER_PATTERN.finditer(text):
        add_span(m.start(), m.end(), "ORDER_ID")

    text_lower = text.lower()
    for org in KNOWN_ORGS:
        start = 0
        while True:
            idx = text_lower.find(org.lower(), start)
            if idx == -1:
                break
            add_span(idx, idx + len(org), "ORG")
            start = idx + 1

    for prod in KNOWN_PRODUCTS:
        start = 0
        while True:
            idx = text_lower.find(prod.lower(), start)
            if idx == -1:
                break
            add_span(idx, idx + len(prod), "PRODUCT")
            start = idx + 1

    # Об'єднуємо з baseline spans
    all_spans = spacy.util.filter_spans(existing_spans + new_ents)
    doc.ents = all_spans
    return doc


def run_hybrid_ner(nlp, texts: list) -> list:
    results = []
    for text in texts:
        doc = nlp(text)
        doc = apply_rules(doc)
        entities = [
            {
                "text":   ent.text,
                "label":  ent.label_,
                "start":  ent.start_char,
                "end":    ent.end_char,
                "source": "rule" if ent.label_ in
                          {"MONEY", "DATE", "ORDER_ID", "PRODUCT"} or
                          any(org in ent.text.lower() for org in KNOWN_ORGS)
                          else "model",
            }
            for ent in doc.ents
        ]
        results.append({"text": text, "entities": entities})
    return results

def diff_results(baseline: list, hybrid: list) -> list:
    diffs = []
    for b, h in zip(baseline, hybrid):
        b_ents = {(e["text"], e["label"]) for e in b["entities"]}
        h_ents = {(e["text"], e["label"]) for e in h["entities"]}
        added   = h_ents - b_ents
        removed = b_ents - h_ents
        if added or removed:
            diffs.append({
                "text":    b["text"][:100],
                "added":   list(added),
                "removed": list(removed),
            })
    return diffs