from sklearn.base import BaseEstimator, TransformerMixin

class RareCategoryGrouper(BaseEstimator, TransformerMixin):
    def __init__(self, thresholds=None, rare_label="Rare", missing_label="Unknown"):
        self.thresholds = thresholds or {}
        self.rare_label = rare_label
        self.missing_label = missing_label

    def fit(self, X, y=None):
        X = X.copy()
        self.frequent_categories_ = {}

        for col, min_count in self.thresholds.items():
            values = X[col].astype("string").fillna(self.missing_label)
            counts = values.value_counts()
            self.frequent_categories_[col] = set(
                counts[counts >= min_count].index
            )
        return self

    def transform(self, X):
        X = X.copy()
        for col, frequent in self.frequent_categories_.items():
            values = X[col].astype("string").fillna(self.missing_label)
            X[col] = values.where(values.isin(frequent), self.rare_label)
        return X
