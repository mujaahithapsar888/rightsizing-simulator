"""
predictor.py
─────────────────
Predictive modeling service using Scikit-Learn Random Forest Regression.

Provides model training, evaluation (MAE, RMSE, R² score), persistence (pickle),
retraining API hooks, and prediction results for rightsizing simulator.
"""
from __future__ import annotations

import os
import pickle
import uuid
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from app.core.config import settings

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml_models")
os.makedirs(MODEL_DIR, exist_ok=True)

class RightsizingPredictor:
    """Manages training and prediction of target performance metrics."""

    def __init__(self, dataset_id: str):
        self.dataset_id = dataset_id
        self.model_path = os.path.join(MODEL_DIR, f"rf_predictor_{dataset_id}.pkl")
        self.models: Dict[str, RandomForestRegressor] = {}
        self.metrics: Dict[str, Dict[str, float]] = {}
        self.is_trained = False
        self.load_models()

    def load_models(self) -> bool:
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, "rb") as f:
                    data = pickle.load(f)
                    self.models = data.get("models", {})
                    self.metrics = data.get("metrics", {})
                    self.is_trained = True
                return True
            except Exception:
                pass
        return False

    def save_models(self):
        with open(self.model_path, "wb") as f:
            pickle.dump({
                "models": self.models,
                "metrics": self.metrics
            }, f)

    def train(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Trains Random Forest Regressors for CPU, Memory, Latency, and Availability.
        Uses 80/20 train/test split. Returns evaluation metrics.
        """
        if len(records) < 10:
            raise ValueError("Insufficient data points to train models. Minimum 10 records required.")

        df = pd.DataFrame(records)
        
        # Preprocess features
        # We engineer simple features: hour of day, day of week, and instance characteristics if present
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["hour"] = df["timestamp"].dt.hour
        df["dayofweek"] = df["timestamp"].dt.dayofweek
        
        # Instance sizing mapping
        instance_vcpu_map = {"c5.xlarge": 4, "c5.2xlarge": 8, "c5.4xlarge": 16, "c5.9xlarge": 36}
        instance_mem_map = {"c5.xlarge": 8.0, "c5.2xlarge": 16.0, "c5.4xlarge": 32.0, "c5.9xlarge": 72.0}
        
        df["vcpu"] = df["instance_type"].map(instance_vcpu_map).fillna(8)
        df["memory_gb"] = df["instance_type"].map(instance_mem_map).fillna(16.0)
        
        # Input features: vcpu, memory_gb, hour, dayofweek
        X = df[["vcpu", "memory_gb", "hour", "dayofweek"]].fillna(0)
        
        targets = {
            "cpu_utilization": "cpu_utilization",
            "memory_utilization": "memory_utilization",
            "latency": "latency_ms",
            "availability": "availability"
        }
        
        self.metrics = {}
        self.models = {}

        for key, target_col in targets.items():
            if target_col not in df.columns or df[target_col].isna().all():
                # Fallback to defaults if column missing
                continue
                
            y = df[target_col].fillna(df[target_col].mean())
            
            # Train test split (80/20)
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train Random Forest Regressor
            model = RandomForestRegressor(n_estimators=50, random_state=42)
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test)
            mae = float(mean_absolute_error(y_test, y_pred))
            rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
            r2 = float(r2_score(y_test, y_pred))
            
            self.models[key] = model
            self.metrics[key] = {
                "mae": round(mae, 4),
                "rmse": round(rmse, 4),
                "r2_score": round(r2, 4)
            }

        self.is_trained = True
        self.save_models()
        return self.metrics

    def predict(self, target_instance_type: str, hour: int, dayofweek: int) -> Dict[str, float]:
        """Predicts CPU, Memory, Latency, and Availability for a target instance spec."""
        if not self.is_trained:
            raise ValueError("Predictor is not trained yet.")
            
        instance_vcpu_map = {"c5.xlarge": 4, "c5.2xlarge": 8, "c5.4xlarge": 16, "c5.9xlarge": 36}
        instance_mem_map = {"c5.xlarge": 8.0, "c5.2xlarge": 16.0, "c5.4xlarge": 32.0, "c5.9xlarge": 72.0}
        
        vcpu = instance_vcpu_map.get(target_instance_type, 8)
        mem = instance_mem_map.get(target_instance_type, 16.0)
        
        features = np.array([[vcpu, mem, hour, dayofweek]])
        
        predictions = {}
        for key, model in self.models.items():
            pred_val = float(model.predict(features)[0])
            predictions[key] = round(pred_val, 2)
            
        return predictions
