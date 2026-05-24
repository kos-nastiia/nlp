import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['figure.dpi'] = 100
import pandas as pd
from topic_modeling import get_top_words, get_top_docs


def print_topics(model, feature_names, topic_names=None, n_top=10):
    """Виводить топ-слова для кожної теми з назвою."""
    topics = get_top_words(model, feature_names, n_top)
    for t in topics:
        name = topic_names[t['topic']] if topic_names else f"Topic {t['topic']}"
        print(f"\n{'='*60}")
        print(f"Topic {t['topic']:2d} | {name}")
        print(f"  Words: {', '.join(t['words'])}")


def print_top_docs(model_name, topic_idx, topic_name, doc_topic_matrix, texts, n_docs=2):
    """Виводить топ-документи для заданої теми."""
    docs = get_top_docs(doc_topic_matrix, texts, topic_idx, n_docs)
    print(f"\n--- {model_name} | Topic {topic_idx}: {topic_name} | Top docs ---")
    for d in docs:
        print(f"  [doc_id={d['doc_id']}, score={d['score']:.4f}]")
        print(f"  {d['text'][:160]}...")
        print()


def plot_topic_word_weights(model, feature_names, topic_idx,
                             topic_name='', n_top=12, ax=None):
    """Горизонтальний bar chart ваг слів для однієї теми."""
    comp = model.components_[topic_idx]
    top_idx = np.abs(comp).argsort()[::-1][:n_top]
    words = [feature_names[i] for i in top_idx]
    weights = [comp[i] for i in top_idx]

    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 4))
    colors = ['steelblue' if w >= 0 else 'coral' for w in weights]
    ax.barh(words[::-1], weights[::-1], color=colors[::-1])
    ax.set_title(f'Topic {topic_idx}: {topic_name}', fontsize=12)
    ax.set_xlabel('Weight')
    ax.axvline(0, color='black', linewidth=0.8)
    return ax


def plot_all_topics_heatmap(model, feature_names, topic_names=None,
                             n_top=8, title='Topic-Word Heatmap'):
    """Теплова карта: теми × топ-слова."""
    n_topics = model.components_.shape[0]
    # Збираємо топ слова з усіх тем
    all_words_set = []
    for comp in model.components_:
        top_idx = np.abs(comp).argsort()[::-1][:n_top]
        for i in top_idx:
            if feature_names[i] not in all_words_set:
                all_words_set.append(feature_names[i])

    matrix = np.zeros((n_topics, len(all_words_set)))
    fn_list = list(feature_names)
    for t_idx, comp in enumerate(model.components_):
        for w_idx, word in enumerate(all_words_set):
            if word in fn_list:
                matrix[t_idx, fn_list.index(word)] = comp[fn_list.index(word)]

    # Нормалізуємо по рядках
    row_max = np.abs(matrix).max(axis=1, keepdims=True)
    row_max[row_max == 0] = 1
    matrix_norm = matrix / row_max

    fig, ax = plt.subplots(figsize=(max(12, len(all_words_set) * 0.5), n_topics * 0.7 + 1))
    im = ax.imshow(matrix_norm, cmap='RdBu_r', aspect='auto', vmin=-1, vmax=1)
    plt.colorbar(im, ax=ax, fraction=0.02)

    ax.set_xticks(range(len(all_words_set)))
    ax.set_xticklabels(all_words_set, rotation=45, ha='right', fontsize=8)
    ax.set_yticks(range(n_topics))
    ylabels = topic_names if topic_names else [f'T{i}' for i in range(n_topics)]
    ax.set_yticklabels(ylabels, fontsize=9)
    ax.set_title(title, fontsize=13)
    plt.tight_layout()
    return fig, ax


def compare_models_table(lsa_topics, lda_topics, lsa_names=None, lda_names=None):
    """DataFrame для порівняння тем LSA та LDA поруч."""
    rows = []
    n = max(len(lsa_topics), len(lda_topics))
    for i in range(n):
        lsa_words = ', '.join(lsa_topics[i]['words']) if i < len(lsa_topics) else ''
        lda_words = ', '.join(lda_topics[i]['words']) if i < len(lda_topics) else ''
        lsa_name = lsa_names[i] if lsa_names and i < len(lsa_names) else f'LSA-T{i}'
        lda_name = lda_names[i] if lda_names and i < len(lda_names) else f'LDA-T{i}'
        rows.append({
            'LSA назва': lsa_name,
            'LSA top words': lsa_words,
            'LDA назва': lda_name,
            'LDA top words': lda_words,
        })
    return pd.DataFrame(rows)