import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import (
    precision_recall_curve, average_precision_score,
    precision_score, recall_score, f1_score,
    confusion_matrix
)


def get_decision_scores(pipe, X):
    """
    Повертає decision scores для бінарного класифікатора.
    Для LinearSVC використовує decision_function,
    для LogReg — predict_proba.
    """
    clf = pipe.named_steps.get('clf') or pipe[-1]
    # FeatureUnion pipeline: витягуємо трансформовані фічі
    X_transformed = _transform(pipe, X)
    if hasattr(clf, 'decision_function'):
        scores = clf.decision_function(X_transformed)
    elif hasattr(clf, 'predict_proba'):
        scores = clf.predict_proba(X_transformed)[:, 1]
    else:
        raise ValueError("Класифікатор не підтримує decision_function або predict_proba")
    return scores


def _transform(pipe, X):
    """Трансформує X через всі кроки pipeline, крім останнього (clf)."""
    steps = list(pipe.steps)
    X_t = X
    for name, step in steps[:-1]:
        X_t = step.transform(X_t)
    return X_t


def plot_pr_curve(pipe, X_val, y_val,
                  label='model', ax=None, color='steelblue'):
    """
    Будує PR-curve для бінарної задачі на validation set.
    Повертає (ax, precisions, recalls, thresholds, ap).
    """
    scores = get_decision_scores(pipe, X_val)
    precisions, recalls, thresholds = precision_recall_curve(y_val, scores)
    ap = average_precision_score(y_val, scores)

    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 5))

    ax.plot(recalls, precisions, color=color, lw=2,
            label=f'{label} (AP={ap:.3f})')
    ax.set_xlabel('Recall', fontsize=12)
    ax.set_ylabel('Precision', fontsize=12)
    ax.set_title('Precision-Recall Curve', fontsize=14)
    ax.legend(loc='lower left')
    ax.grid(alpha=0.3)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.05])

    return ax, precisions, recalls, thresholds, ap


def evaluate_thresholds(pipe, X_val, y_val,
                        thresholds_to_check=None):
    """
    Оцінює метрики для набору порогів.
    Повертає DataFrame з precision, recall, f1 для кожного порогу.
    """
    import pandas as pd

    scores = get_decision_scores(pipe, X_val)
    precisions, recalls, thresholds = precision_recall_curve(y_val, scores)

    if thresholds_to_check is None:
        thresholds_to_check = np.linspace(scores.min(), scores.max(), 20)

    rows = []
    for t in thresholds_to_check:
        y_pred_t = (scores >= t).astype(int)
        rows.append({
            'threshold': round(float(t), 4),
            'precision': round(precision_score(y_val, y_pred_t, zero_division=0), 4),
            'recall':    round(recall_score(y_val, y_pred_t, zero_division=0), 4),
            'f1':        round(f1_score(y_val, y_pred_t, zero_division=0), 4),
            'predicted_positive': int(y_pred_t.sum()),
        })

    return pd.DataFrame(rows)


def apply_threshold(pipe, X, threshold: float):
    """Повертає бінарні передбачення при заданому порозі."""
    scores = get_decision_scores(pipe, X)
    return (scores >= threshold).astype(int)


def find_best_threshold_f1(pipe, X_val, y_val):
    """Знаходить поріг з максимальним F1 на validation set."""
    scores = get_decision_scores(pipe, X_val)
    precisions, recalls, thresholds = precision_recall_curve(y_val, scores)
    f1_scores = 2 * precisions[:-1] * recalls[:-1] / (
        precisions[:-1] + recalls[:-1] + 1e-9
    )
    best_idx = np.argmax(f1_scores)
    return float(thresholds[best_idx]), float(f1_scores[best_idx])


def find_best_threshold_recall(pipe, X_val, y_val, min_precision: float = 0.75):
    """
    Знаходить поріг з максимальним recall при precision >= min_precision.
    Корисно, коли FN дорогі (recall-first логіка).
    """
    scores = get_decision_scores(pipe, X_val)
    precisions, recalls, thresholds = precision_recall_curve(y_val, scores)
    mask = precisions[:-1] >= min_precision
    if not mask.any():
        best_idx = np.argmin(np.abs(precisions[:-1] - min_precision))
    else:
        best_idx = np.where(mask)[0][np.argmax(recalls[:-1][mask])]
    return float(thresholds[best_idx])


def plot_threshold_metrics(pipe, X_val, y_val,
                           thresholds_to_check=None, ax=None):
    """
    Малює графік precision / recall / F1 залежно від порогу.
    """
    df = evaluate_thresholds(pipe, X_val, y_val, thresholds_to_check)

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(df['threshold'], df['precision'], label='Precision', color='steelblue', lw=2)
    ax.plot(df['threshold'], df['recall'],    label='Recall',    color='coral',     lw=2)
    ax.plot(df['threshold'], df['f1'],        label='F1',        color='green',     lw=2, linestyle='--')
    ax.set_xlabel('Threshold', fontsize=12)
    ax.set_ylabel('Score', fontsize=12)
    ax.set_title('Precision / Recall / F1 vs Threshold (Validation Set)', fontsize=13)
    ax.legend()
    ax.grid(alpha=0.3)

    return ax, df