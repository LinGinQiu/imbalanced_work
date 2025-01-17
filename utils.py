import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from imblearn.over_sampling import *
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_curve, auc
from aeon.classification.interval_based import TimeSeriesForestClassifier
from aeon.classification.hybrid import HIVECOTEV2
from aeon.classification.convolution_based import MultiRocketHydraClassifier
from aeon.classification.sklearn import RotationForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.base import BaseEstimator, TransformerMixin

sns.set_context("paper")
from config import Config


def plot_decision_function(X, y, clf, ax, title=None):
    plot_step = 0.02
    x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
    y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
    xx, yy = np.meshgrid(
        np.arange(x_min, x_max, plot_step), np.arange(y_min, y_max, plot_step)
    )
    Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)
    ax.contourf(xx, yy, Z, alpha=0.4)
    ax.scatter(X[:, 0], X[:, 1], alpha=0.8, c=y, edgecolor="k")
    if title is not None:
        ax.set_title(title)


def metric_factors(y_true, y_pred, y_pred_proba, positive_class=1, verbose=True):
    # 1. Accuracy
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, pos_label=positive_class, zero_division=0)
    recall = recall_score(y_true, y_pred, pos_label=positive_class, zero_division=0)

    # 2. F1 Score
    f1 = f1_score(y_true, y_pred)

    # 3. ROC Curve
    fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba[:, 1])

    # 4. AUC
    roc_auc_value = auc(fpr, tpr)

    # Plot ROC Curve
    if verbose:
        print(f"Accuracy: {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1 Score: {f1:.4f}")
        print(f"AUC: {roc_auc_value:.4f}")
        plt.figure(figsize=(10, 6))
        plt.plot(fpr, tpr, color='blue', label=f'ROC curve (area = {roc_auc_value:.2f})')
        plt.plot([0, 1], [0, 1], color='red', linestyle='--')  # Diagonal line (random classifier)
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.0])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver Operating Characteristic (ROC) Curve')
        plt.legend(loc='lower right')
        plt.grid()
        plt.show()

    return accuracy, precision, recall, f1, roc_auc_value, fpr, tpr


class None_sampler:
    def __init__(self):
        pass

    def fit_resample(self, X, y):
        return X, y




class SqueezeTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self  # 无需拟合，直接返回

    def transform(self, X):
        return np.squeeze(X)  # 压缩数组中的维度


class OverSamplingMethods:
    """
    over-sampling methods include 'ADASYN', 'RandomOverSampler', 'KMeansSMOTE', 'SMOTE',
    'BorderlineSMOTE', 'SVMSMOTE', 'SMOTENC', 'SMOTEN'
    """

    def __init__(self):
        self.config = Config()

    def none_sampling(self):
        return None_sampler()

    def ros(self):
        return RandomOverSampler(random_state=self.config.seed)

    def rose(self):
        return RandomOverSampler(random_state=self.config.seed, shrinkage={1: 2.})

    def adasyn(self):
        return ADASYN(random_state=self.config.seed, n_neighbors=5)

    def smote(self):
        return SMOTE(random_state=self.config.seed, k_neighbors=5)


class ClassificationMetrics:
    """
    over-sampling methods include 'ADASYN', 'RandomOverSampler', 'KMeansSMOTE', 'SMOTE',
    'BorderlineSMOTE', 'SVMSMOTE', 'SMOTENC', 'SMOTEN'
    """

    def __init__(self):
        self.config = Config()

    def tsf_classifier(self):
        return TimeSeriesForestClassifier(n_estimators=50, random_state=self.config.seed)

    def hc2(self):
        return HIVECOTEV2(random_state=self.config.seed)

    def multi_rocket_hydra(self):
        return MultiRocketHydraClassifier(random_state=self.config.seed)

    def rotation_forest(self):
        from sklearn.pipeline import Pipeline
        pipeline = Pipeline([
            ('squeeze', SqueezeTransformer()),
            ('classifier', RotationForestClassifier(random_state=self.config.seed))
        ])
        return pipeline

    def logistic_regression(self):
        from sklearn.pipeline import Pipeline
        pipeline = Pipeline([
            ('squeeze', SqueezeTransformer()),
            ('classifier', LogisticRegression(random_state=self.config.seed))
        ])
        return pipeline
