import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, f1_score, classification_report,
    confusion_matrix, precision_recall_curve, average_precision_score
)
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['figure.dpi'] = 100


def extract_label_and_clean(text: str):
    """Витягує мітку 0/1 з кінця рядка і повертає (label, clean_text)."""
    text = str(text).strip()
    if text and text[-1] in ['0', '1']:
        return int(text[-1]), text[:-1].strip()
    return None, text


def load_and_prepare(data_path: str) -> pd.DataFrame:
    """Завантажує processed_v2.csv і готує розмічений датасет."""
    df = pd.read_csv(data_path)
    extracted = df['text_v2'].apply(extract_label_and_clean)
    df['label'] = [x[0] for x in extracted]
    df['text_clean'] = [x[1] for x in extracted]
    df = df.dropna(subset=['label']).copy()
    df['label'] = df['label'].astype(int)
    df = df.reset_index(drop=True)
    return df


def build_logreg_baseline(class_weight=None):
    """Референс-baseline з ЛР6: TF-IDF word(1,2) + LogReg."""
    return Pipeline([
        ('tfidf', TfidfVectorizer(
            analyzer='word', ngram_range=(1, 2),
            sublinear_tf=True, min_df=2
        )),
        ('clf', LogisticRegression(
            max_iter=500, random_state=42,
            class_weight=class_weight
        ))
    ])


def build_linear_svc_word(class_weight=None):
    """Варіант 2: TF-IDF word(1,2) + LinearSVC."""
    return Pipeline([
        ('tfidf', TfidfVectorizer(
            analyzer='word', ngram_range=(1, 2),
            sublinear_tf=True, min_df=2
        )),
        ('clf', LinearSVC(
            C=1.0, max_iter=2000, random_state=42,
            class_weight=class_weight
        ))
    ])


def build_linear_svc_char(class_weight=None):
    """Варіант 3: TF-IDF char_wb(3,5) + LinearSVC."""
    return Pipeline([
        ('tfidf', TfidfVectorizer(
            analyzer='char_wb', ngram_range=(3, 5),
            sublinear_tf=True, min_df=3
        )),
        ('clf', LinearSVC(
            C=1.0, max_iter=2000, random_state=42,
            class_weight=class_weight
        ))
    ])


def build_linear_svc_word_char(class_weight=None):
    """Варіант 4 (бонус): word(1,2) + char_wb(3,5) об'єднані через FeatureUnion."""
    word_tfidf = TfidfVectorizer(
        analyzer='word', ngram_range=(1, 2),
        sublinear_tf=True, min_df=2
    )
    char_tfidf = TfidfVectorizer(
        analyzer='char_wb', ngram_range=(3, 5),
        sublinear_tf=True, min_df=3
    )
    return Pipeline([
        ('features', FeatureUnion([
            ('word', word_tfidf),
            ('char', char_tfidf),
        ])),
        ('clf', LinearSVC(
            C=1.0, max_iter=2000, random_state=42,
            class_weight=class_weight
        ))
    ])



def run_logreg_baseline(X_train, y_train, X_eval, y_eval,
                        class_weight=None, label='LogReg word(1,2)'):
    pipe = build_logreg_baseline(class_weight=class_weight)
    pipe.fit(X_train, y_train)
    return evaluate_pipeline(pipe, X_eval, y_eval, label=label)


def run_linear_svc(X_train, y_train, X_eval, y_eval,
                   variant='word', class_weight=None, label=None):
    builders = {
        'word': build_linear_svc_word,
        'char': build_linear_svc_char,
        'word+char': build_linear_svc_word_char,
    }
    pipe = builders[variant](class_weight=class_weight)
    if label is None:
        label = f'LinearSVC {variant}'
    pipe.fit(X_train, y_train)
    return evaluate_pipeline(pipe, X_eval, y_eval, label=label)


def evaluate_pipeline(pipe, X, y, label='model'):
    """Повертає словник з метриками та самим пайплайном."""
    y_pred = pipe.predict(X)
    acc = accuracy_score(y, y_pred)
    f1 = f1_score(y, y_pred, average='macro')
    report = classification_report(y, y_pred, digits=4)
    cm = confusion_matrix(y, y_pred)
    return {
        'label': label,
        'pipe': pipe,
        'y_pred': y_pred,
        'accuracy': acc,
        'macro_f1': f1,
        'report': report,
        'cm': cm,
    }



def plot_confusion_matrix(cm, title='Confusion Matrix',
                          labels=None, ax=None, cmap='Blues'):
    """Малює confusion matrix на переданому ax або новому figure."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(5, 4))
    if labels is None:
        labels = [str(i) for i in range(cm.shape[0])]
    im = ax.imshow(cm, interpolation='nearest', cmap=cmap)
    ax.figure.colorbar(im, ax=ax)
    ax.set(
        xticks=np.arange(cm.shape[1]),
        yticks=np.arange(cm.shape[0]),
        xticklabels=labels, yticklabels=labels,
        title=title, ylabel='True label', xlabel='Predicted label'
    )
    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], 'd'),
                    ha='center', va='center',
                    color='white' if cm[i, j] > thresh else 'black')
    return ax