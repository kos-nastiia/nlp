import pandas as pd
import os


def load_corpus(data_path: str, min_words: int = 5) -> pd.DataFrame:
    df = pd.read_csv(data_path)

    def extract_clean(text: str) -> str:
        text = str(text).strip()
        if text and text[-1] in ['0', '1']:
            text = text[:-1].strip()
        return text

    df['text_clean'] = df['text_v2'].apply(extract_clean)
    before = len(df)
    df = df[df['text_clean'].str.split().str.len() >= min_words].copy()
    df = df.reset_index(drop=True)
    print(f"Corpus loaded: {before} → {len(df)} docs (filtered < {min_words} words)")
    return df


def tokenize(df: pd.DataFrame, col: str = 'text_clean') -> list:
    sentences = []
    for text in df[col]:
        tokens = [t for t in str(text).split() if t != '|']
        if tokens:
            sentences.append(tokens)
    return sentences


def corpus_stats(sentences: list) -> dict:
    from collections import Counter
    all_tokens = [t for s in sentences for t in s]
    freq = Counter(all_tokens)
    return {
        'n_docs': len(sentences),
        'n_tokens': len(all_tokens),
        'n_unique': len(freq),
        'avg_doc_len': round(len(all_tokens) / len(sentences), 1),
        'top20': freq.most_common(20),
    }


def train_word2vec(sentences: list,
                   vector_size: int = 100,
                   window: int = 5,
                   min_count: int = 3,
                   sg: int = 1,
                   epochs: int = 10,
                   seed: int = 42,
                   workers: int = 2):
    from gensim.models import Word2Vec
    model = Word2Vec(
        sentences=sentences,
        vector_size=vector_size,
        window=window,
        min_count=min_count,
        sg=sg,
        seed=seed,
        workers=workers,
        epochs=epochs,
    )
    print(f"Word2Vec trained | vocab={len(model.wv)} | vector_size={vector_size} | sg={sg}")
    return model


def train_fasttext(sentences: list,
                   vector_size: int = 100,
                   window: int = 5,
                   min_count: int = 3,
                   sg: int = 1,
                   epochs: int = 10,
                   seed: int = 42,
                   workers: int = 2):
    from gensim.models import FastText
    model = FastText(
        sentences=sentences,
        vector_size=vector_size,
        window=window,
        min_count=min_count,
        sg=sg,
        seed=seed,
        workers=workers,
        epochs=epochs,
    )
    print(f"FastText trained | vocab={len(model.wv)} | vector_size={vector_size} | sg={sg}")
    return model


def save_model(model, path: str):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    model.save(path)
    print(f"Saved: {path}")


def load_model_w2v(path: str):
    from gensim.models import Word2Vec
    return Word2Vec.load(path)


def load_model_ft(path: str):
    from gensim.models import FastText
    return FastText.load(path)