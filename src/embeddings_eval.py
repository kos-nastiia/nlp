import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['figure.dpi'] = 100


def get_neighbors(model, word: str, topn: int = 10) -> list:
    try:
        return [(w, round(float(s), 4)) for w, s in model.wv.most_similar(word, topn=topn)]
    except KeyError:
        return []


def compare_neighbors(w2v_model, ft_model, word: str, topn: int = 8) -> pd.DataFrame:
    w2v_n = get_neighbors(w2v_model, word, topn)
    ft_n  = get_neighbors(ft_model,  word, topn)

    rows = []
    for i in range(max(len(w2v_n), len(ft_n))):
        w2v_word  = w2v_n[i][0] if i < len(w2v_n) else '—'
        w2v_score = w2v_n[i][1] if i < len(w2v_n) else None
        ft_word   = ft_n[i][0]  if i < len(ft_n)  else '—'
        ft_score  = ft_n[i][1]  if i < len(ft_n)  else None
        rows.append({
            'rank':      i + 1,
            'W2V word':  w2v_word,
            'W2V sim':   w2v_score,
            'FT word':   ft_word,
            'FT sim':    ft_score,
        })
    return pd.DataFrame(rows)


def neighbors_table(w2v_model, ft_model, words: list, topn: int = 5,
                    word_types: dict = None) -> pd.DataFrame:
    """
    Зведена таблиця для всіх слів:
    Word | Type | W2V neighbors | FT neighbors | Useful? | Comment
    """
    rows = []
    for word in words:
        w2v_n = [w for w, _ in get_neighbors(w2v_model, word, topn)]
        ft_n  = [w for w, _ in get_neighbors(ft_model,  word, topn)]
        wtype = word_types.get(word, '?') if word_types else '?'
        rows.append({
            'Word':          word,
            'Type':          wtype,
            'W2V neighbors': ', '.join(w2v_n) if w2v_n else 'OOV',
            'FT neighbors':  ', '.join(ft_n)  if ft_n  else 'OOV',
            'Useful?':       '',
            'Comment':       '',
        })
    return pd.DataFrame(rows)

def oov_test(w2v_model, ft_model, test_words: list) -> pd.DataFrame:
    """
    Перевіряє, чи модель знає слово.
    Для FastText — завжди є вектор через subword.
    Для Word2Vec — None якщо OOV.
    """
    rows = []
    for word in test_words:
        in_w2v = word in w2v_model.wv.key_to_index
        try:
            ft_model.wv[word]
            in_ft = True
        except KeyError:
            in_ft = False
        rows.append({'word': word, 'in_W2V': in_w2v, 'in_FT': in_ft})
    return pd.DataFrame(rows)

def cases_table(cases: list) -> pd.DataFrame:
    return pd.DataFrame(cases)


def plot_similarity_bars(model, words: list, title: str = 'Similarity to neighbors',
                         topn: int = 5, figsize: tuple = None):
    n = len(words)
    if figsize is None:
        figsize = (5 * n, 4)
    fig, axes = plt.subplots(1, n, figsize=figsize)
    if n == 1:
        axes = [axes]
    for ax, word in zip(axes, words):
        neighbors = get_neighbors(model, word, topn)
        if not neighbors:
            ax.set_title(f'{word}\n(OOV)')
            continue
        ws  = [w for w, _ in neighbors]
        sim = [s for _, s in neighbors]
        ax.barh(ws[::-1], sim[::-1], color='steelblue')
        ax.set_xlim(0, 1)
        ax.set_title(word, fontsize=11)
        ax.set_xlabel('Cosine similarity')
        ax.grid(axis='x', alpha=0.3)
    fig.suptitle(title, fontsize=13)
    plt.tight_layout()
    return fig


def plot_w2v_vs_ft_neighbors(w2v_model, ft_model, word: str, topn: int = 7):
    w2v_n = get_neighbors(w2v_model, word, topn)
    ft_n  = get_neighbors(ft_model,  word, topn)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    if w2v_n:
        ws, ss = zip(*w2v_n)
        ax1.barh(list(ws)[::-1], list(ss)[::-1], color='steelblue')
        ax1.set_xlim(0, 1)
    ax1.set_title(f'Word2Vec — "{word}"')
    ax1.set_xlabel('Cosine similarity')

    if ft_n:
        ws, ss = zip(*ft_n)
        ax2.barh(list(ws)[::-1], list(ss)[::-1], color='coral')
        ax2.set_xlim(0, 1)
    ax2.set_title(f'FastText — "{word}"')
    ax2.set_xlabel('Cosine similarity')

    plt.tight_layout()
    return fig