"""
ml_analysis.py
======================
Gelişmiş ML analiz modülü:
 - data/ klasöründeki tüm .csv dosyalarını otomatik okur
 - hem anomaly detection hem regression modellerini uygular
 - tüm metrikleri hesaplayıp detaylı bir rapor üretir
 - gereksiz .pkl kaydı yapmaz
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest, RandomForestRegressor, RandomForestClassifier
from sklearn.neighbors import LocalOutlierFactor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.svm import SVR, SVC
from sklearn.metrics import (
    r2_score, mean_squared_error, accuracy_score,
    precision_score, recall_score, f1_score
)
from datetime import datetime

class MLProjectAnalyzer:
    def __init__(self, data_dir="data", report_dir="reports"):
        self.data_dir = data_dir
        self.report_dir = report_dir
        os.makedirs(report_dir, exist_ok=True)
        self.results = []

    def load_datafiles(self):
        csv_files = [f for f in os.listdir(self.data_dir) if f.endswith(".csv")]
        datasets = []
        for f in csv_files:
            path = os.path.join(self.data_dir, f)
            try:
                df = pd.read_csv(path)
                df = df.select_dtypes(include=[np.number]).dropna()
                if len(df.columns) >= 2:
                    datasets.append((f, df))
            except Exception as e:
                print(f"[WARN] {f} okunamadı: {e}")
        return datasets

    def detect_anomalies(self, df, dataset_name):
        results = []
        models = {
            "IsolationForest": IsolationForest(contamination=0.05, random_state=42),
            "LocalOutlierFactor": LocalOutlierFactor(n_neighbors=20, contamination=0.05)
        }

        for name, model in models.items():
            try:
                if name == "LocalOutlierFactor":
                    preds = model.fit_predict(df)
                    scores = -model.negative_outlier_factor_
                else:
                    model.fit(df)
                    preds = model.predict(df)
                    scores = model.decision_function(df)

                anomalies = (preds == -1).sum()
                anomaly_ratio = anomalies / len(df)
                threshold = np.percentile(scores, 5)

                results.append({
                    "dataset": dataset_name,
                    "type": "Anomaly Detection",
                    "model": name,
                    "threshold": round(float(threshold), 6),
                    "anomaly_count": int(anomalies),
                    "anomaly_ratio": round(float(anomaly_ratio), 4),
                })
            except Exception as e:
                print(f"[ERROR] {dataset_name} - {name} hata: {e}")
        return results

    def regression_models(self, df, dataset_name):
        results = []
        target_col = df.columns[-1]
        X = df.drop(columns=[target_col])
        y = df[target_col]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        models = {
            "LinearRegression": LinearRegression(),
            "RandomForestRegressor": RandomForestRegressor(n_estimators=100, random_state=42),
            "SVR": SVR(kernel="rbf", C=1.0, gamma="scale")
        }

        for name, model in models.items():
            try:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)

                r2 = r2_score(y_test, y_pred)
                mse = mean_squared_error(y_test, y_pred)

                results.append({
                    "dataset": dataset_name,
                    "type": "Regression",
                    "model": name,
                    "R2_Score": round(float(r2), 4),
                    "MSE": round(float(mse), 6)
                })
            except Exception as e:
                print(f"[ERROR] {dataset_name} - {name}: {e}")
        return results

    def classification_models(self, df, dataset_name):
        results = []
        target_col = df.columns[-1]
        X = df.drop(columns=[target_col])
        y = df[target_col]

        # Hedef binary değilse, basitleştir
        if len(np.unique(y)) > 5:
            y = (y > np.median(y)).astype(int)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        models = {
            "LogisticRegression": LogisticRegression(max_iter=1000),
            "RandomForestClassifier": RandomForestClassifier(n_estimators=100, random_state=42),
            "SVM_Classifier": SVC(kernel="rbf", C=1.0, gamma="scale")
        }

        for name, model in models.items():
            try:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)

                acc = accuracy_score(y_test, y_pred)
                prec = precision_score(y_test, y_pred, zero_division=0)
                rec = recall_score(y_test, y_pred, zero_division=0)
                f1 = f1_score(y_test, y_pred, zero_division=0)

                results.append({
                    "dataset": dataset_name,
                    "type": "Classification",
                    "model": name,
                    "Accuracy": round(float(acc), 4),
                    "Precision": round(float(prec), 4),
                    "Recall": round(float(rec), 4),
                    "F1_Score": round(float(f1), 4)
                })
            except Exception as e:
                print(f"[ERROR] {dataset_name} - {name}: {e}")
        return results

    def run(self):
        datasets = self.load_datafiles()
        if not datasets:
            print("[ERROR] Hiç veri bulunamadı.")
            return

        for name, df in datasets:
            print(f"\n[INFO] {name} analizi başlatılıyor...")
            self.results.extend(self.detect_anomalies(df, name))
            self.results.extend(self.regression_models(df, name))
            self.results.extend(self.classification_models(df, name))

        df_results = pd.DataFrame(self.results)

        # En iyi model seçimi (her dataset için ayrı)
        best_by_dataset = (
            df_results.sort_values(by=["dataset", "type"], ascending=True)
            .groupby(["dataset", "type"])
            .first()
            .reset_index()
        )

        report_path = os.path.join(self.report_dir, f"ML_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
        df_results.to_csv(report_path, index=False)

        print("\n=== 📊 MODEL ANALİZ RAPORU ===")
        print(df_results.head(20).to_string(index=False))
        print("\n=== 🥇 EN İYİ MODELLER ===")
        print(best_by_dataset.to_string(index=False))
        print(f"\n[INFO] Rapor kaydedildi: {report_path}")

if __name__ == "__main__":
    analyzer = MLProjectAnalyzer()
    analyzer.run()
