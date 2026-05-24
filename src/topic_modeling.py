import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import TruncatedSVD, LatentDirichletAllocation

# Стоп-слова для українського корпусу
UA_STOP_WORDS = [
    'та', 'на', 'до', 'від', 'за', 'або', 'що', 'це', 'але', 'який', 'яка',
    'яке', 'які', 'він', 'вона', 'вони', 'мені', 'мене', 'про', 'під', 'при',
    'між', 'через', 'після', 'перед', 'над', 'без', 'для', 'із', 'зі', 'по',
    'не', 'ні', 'так', 'вже', 'ще', 'навіть', 'дуже', 'було', 'буде', 'бути',
    'можна', 'може', 'можуть', 'мають', 'час', 'був', 'цей', 'ця', 'цього',
    'цьому', 'цих', 'його', 'її', 'їх', 'нас', 'нам', 'нами', 'тут', 'там',
    'коли', 'якщо', 'щоб', 'тому', 'також', 'лише', 'тільки', 'саме', 'більш',
    'менш', 'більше', 'менше', 'свою', 'свої', 'свого', 'своє', 'свій',
    'мій', 'моя', 'моє', 'мої', 'всі', 'все', 'весь', 'вся', 'де', 'як',
    'ми', 'ви', 'вас', 'вам', 'ним', 'них', 'цим', 'тим', 'то', 'зо',
    'чи', 'цього', 'таких', 'такий', 'така', 'таке', 'деякі', 'завжди',
    'просто', 'часто', 'вашому', 'ваш', 'вашій', 'нашому', 'наш',
]


def build_tfidf_vectorizer(ngram_range=(1, 1), min_df=5, max_df=0.80, extra_stops=None):
    stops = list(UA_STOP_WORDS) + (extra_stops or [])
    return TfidfVectorizer(analyzer='word', ngram_range=ngram_range,
                           min_df=min_df, max_df=max_df,
                           stop_words=stops, sublinear_tf=True)


def build_count_vectorizer(ngram_range=(1, 1), min_df=5, max_df=0.80, extra_stops=None):
    stops = list(UA_STOP_WORDS) + (extra_stops or [])
    return CountVectorizer(analyzer='word', ngram_range=ngram_range,
                           min_df=min_df, max_df=max_df, stop_words=stops)


def fit_lsa(texts, n_topics=8, ngram_range=(1, 2), min_df=5, max_df=0.80,
            extra_stops=None, random_state=42):
    vec = build_tfidf_vectorizer(ngram_range, min_df, max_df, extra_stops)
    X = vec.fit_transform(texts)
    svd = TruncatedSVD(n_components=n_topics, random_state=random_state)
    doc_topics = svd.fit_transform(X)
    return vec, svd, doc_topics, vec.get_feature_names_out()


def fit_lda(texts, n_topics=8, ngram_range=(1, 1), min_df=5, max_df=0.80,
            extra_stops=None, max_iter=20, random_state=42):
    vec = build_count_vectorizer(ngram_range, min_df, max_df, extra_stops)
    X = vec.fit_transform(texts)
    lda = LatentDirichletAllocation(n_components=n_topics, max_iter=max_iter,
                                    random_state=random_state,
                                    learning_method='online')
    doc_topics = lda.fit_transform(X)
    return vec, lda, doc_topics, vec.get_feature_names_out()


def get_top_words(model, feature_names, n_top=10):
    results = []
    for topic_idx, comp in enumerate(model.components_):
        top_indices = np.abs(comp).argsort()[::-1][:n_top]
        results.append({'topic': topic_idx, 'words': [feature_names[i] for i in top_indices]})
    return results


def get_top_docs(doc_topic_matrix, texts, topic_idx, n_docs=3):
    scores = doc_topic_matrix[:, topic_idx]
    top_indices = scores.argsort()[::-1][:n_docs]
    result = []
    for i in top_indices:
        t = texts.iloc[i] if hasattr(texts, 'iloc') else texts[i]
        result.append({'doc_id': int(i), 'score': float(scores[i]), 'text': str(t)[:200]})
    return result


def topics_summary_df(model, feature_names, n_top=10):
    rows = [{'topic': t['topic'], 'top_words': ', '.join(t['words'])}
            for t in get_top_words(model, feature_names, n_top)]
    return pd.DataFrame(rows)