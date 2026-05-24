import re
import pandas as pd
from typing import Optional



def load_spacy_pipeline(model_name: str = "uk_core_news_sm"):
    import spacy
    try:
        nlp = spacy.load(model_name)
        print(f"Loaded: {model_name}")
        print(f"Pipeline components: {nlp.pipe_names}")
        labels = nlp.get_pipe("ner").labels if "ner" in nlp.pipe_names else []
        print(f"NER labels: {labels}")
        return nlp
    except OSError:
        print(f"Model '{model_name}' not found.")
        print(f"Install: python -m spacy download {model_name}")
        return None


def load_stanza_pipeline(lang: str = "uk"):
    """
    Завантажує Stanza pipeline для укр. мови (альтернатива spaCy).
    """
    try:
        import stanza
        stanza.download(lang, verbose=False)
        nlp = stanza.Pipeline(lang=lang, processors='tokenize,ner', verbose=False)
        print(f"Stanza '{lang}' pipeline loaded.")
        return nlp
    except ImportError:
        print("Stanza not installed. Run: pip install stanza")
        return None


def run_spacy_ner(nlp, texts: list) -> list:
    results = []
    for text in texts:
        doc = nlp(text)
        entities = [
            {
                "text":  ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end":   ent.end_char,
            }
            for ent in doc.ents
        ]
        results.append({"text": text, "entities": entities})
    return results


def run_stanza_ner(nlp, texts: list) -> list:
    results = []
    for text in texts:
        doc = nlp(text)
        entities = []
        for sent in doc.sentences:
            for ent in sent.ents:
                entities.append({
                    "text":  ent.text,
                    "label": ent.type,
                    "start": ent.start_char,
                    "end":   ent.end_char,
                })
        results.append({"text": text, "entities": entities})
    return results

def format_ner_output(results: list, expected: list = None) -> pd.DataFrame:
    rows = []
    for i, res in enumerate(results):
        pred_ents = "; ".join(
            f"{e['text']} [{e['label']}]" for e in res["entities"]
        ) or "—"

        exp_ents = "—"
        if expected and i < len(expected):
            exp = expected[i].get("entities", [])
            exp_ents = "; ".join(
                f"{e['text']} [{e['label']}]" for e in exp
            ) or "—"

        rows.append({
            "text":     res["text"][:100],
            "predicted": pred_ents,
            "expected":  exp_ents,
        })
    return pd.DataFrame(rows)

def load_eval_texts(data_path: str, n: int = 30, seed: int = 42) -> list:
    df = pd.read_csv(data_path)

    def clean(text):
        text = str(text).strip()
        if text and text[-1] in ['0', '1']:
            text = text[:-1].strip()
        return text

    df['text_clean'] = df['text_v2'].apply(clean)
    df = df[df['text_clean'].str.split().str.len() >= 5].reset_index(drop=True)
    sample = df['text_clean'].sample(n=n, random_state=seed).tolist()
    return sample