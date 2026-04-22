"""
Crop Recommendation Model Training Script
Trains multiple ML models on crop dataset and saves them for inference
Models: RandomForest, XGBoost, SVM
Uses K-fold cross-validation for robust evaluation
"""

import numpy as np
import pandas as pd
import pickle
import os
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import warnings
warnings.filterwarnings('ignore')

# Try to import XGBoost
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("[!] XGBoost not available - will use RandomForest and GradientBoosting instead")


class CropModelTrainer:
    """Training pipeline for crop recommendation models"""
    
    def __init__(self, data_path='crop_recommendation_dataset.csv'):
        self.data_path = data_path
        self.df = None
        self.X = None
        self.y = None
        self.le = None
        self.feature_names = None
        self.models = {}
        self.model_scores = {}
    
    def load_data(self):
        """Load crop dataset"""
        if not os.path.exists(self.data_path):
            print(f"[!] Dataset not found at {self.data_path}")
            print("[*] Generating dataset first...")
            from generate_crop_dataset import CropDatasetGenerator
            df = CropDatasetGenerator.generate_dataset(n_samples=2200)
            CropDatasetGenerator.save_dataset(df, self.data_path)
            self.df = df
        else:
            self.df = pd.read_csv(self.data_path)
        
        print(f"[+] Dataset loaded: {self.df.shape[0]} samples, {self.df.shape[1]} columns")
        print(f"[+] Crops: {self.df['crop'].unique().tolist()}")
        return self.df
    
    def prepare_data(self):
        """Prepare data for training"""
        # Separate features and target
        X = self.df.drop('crop', axis=1)
        y = self.df['crop']
        
        # Store feature names
        self.feature_names = X.columns.tolist()
        
        # Encode target labels
        self.le = LabelEncoder()
        y_encoded = self.le.fit_transform(y)
        
        self.X = X
        self.y = y_encoded
        
        print(f"[+] Data prepared:")
        print(f"    Features ({len(self.feature_names)}): {self.feature_names}")
        print(f"    Classes ({len(self.le.classes_)}): {self.le.classes_.tolist()}")
        
        return self.X, self.y
    
    def train_random_forest(self):
        """Train RandomForest classifier"""
        print("\n[*] Training RandomForest Classifier...")
        
        X_train, X_test, y_train, y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42
        )
        
        rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
            verbose=0
        )
        
        rf_model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = rf_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Cross-validation
        kfold = KFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(rf_model, self.X, self.y, cv=kfold)
        
        print(f"    Test Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
        print(f"    Cross-Val Mean: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        print(f"    Feature Importance (Top 5):")
        feature_importance = sorted(
            zip(self.feature_names, rf_model.feature_importances_),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        for feat, imp in feature_importance:
            print(f"        {feat}: {imp:.4f}")
        
        self.models['random_forest'] = rf_model
        self.model_scores['random_forest'] = {
            'accuracy': accuracy,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
        
        return rf_model
    
    def train_xgboost(self):
        """Train XGBoost classifier"""
        if not XGBOOST_AVAILABLE:
            print("\n[!] XGBoost not available, skipping...")
            return None
        
        print("\n[*] Training XGBoost Classifier...")
        
        X_train, X_test, y_train, y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42
        )
        
        xgb_model = XGBClassifier(
            n_estimators=200,
            max_depth=10,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            verbosity=0,
            tree_method='hist'
        )
        
        xgb_model.fit(X_train, y_train, verbose=False)
        
        # Evaluate
        y_pred = xgb_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Cross-validation
        kfold = KFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(xgb_model, self.X, self.y, cv=kfold)
        
        print(f"    Test Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
        print(f"    Cross-Val Mean: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        print(f"    Feature Importance (Top 5):")
        feature_importance = sorted(
            zip(self.feature_names, xgb_model.feature_importances_),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        for feat, imp in feature_importance:
            print(f"        {feat}: {imp:.4f}")
        
        self.models['xgboost'] = xgb_model
        self.model_scores['xgboost'] = {
            'accuracy': accuracy,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
        
        return xgb_model
    
    def train_gradient_boosting(self):
        """Train Gradient Boosting classifier"""
        print("\n[*] Training Gradient Boosting Classifier...")
        
        X_train, X_test, y_train, y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42
        )
        
        gb_model = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.1,
            subsample=0.9,
            random_state=42,
            verbose=0
        )
        
        gb_model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = gb_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Cross-validation
        kfold = KFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(gb_model, self.X, self.y, cv=kfold)
        
        print(f"    Test Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
        print(f"    Cross-Val Mean: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        print(f"    Feature Importance (Top 5):")
        feature_importance = sorted(
            zip(self.feature_names, gb_model.feature_importances_),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        for feat, imp in feature_importance:
            print(f"        {feat}: {imp:.4f}")
        
        self.models['gradient_boosting'] = gb_model
        self.model_scores['gradient_boosting'] = {
            'accuracy': accuracy,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
        
        return gb_model
    
    def save_models(self, model_dir='models'):
        """Save trained models and metadata"""
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        
        print(f"\n[*] Saving models to {model_dir}/...")
        
        for name, model in self.models.items():
            model_path = os.path.join(model_dir, f'{name}_model.pkl')
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            print(f"    ✓ {name}_model.pkl")
        
        # Save label encoder
        encoder_path = os.path.join(model_dir, 'label_encoder.pkl')
        with open(encoder_path, 'wb') as f:
            pickle.dump(self.le, f)
        print(f"    ✓ label_encoder.pkl")
        
        # Save feature names
        features_path = os.path.join(model_dir, 'feature_names.pkl')
        with open(features_path, 'wb') as f:
            pickle.dump(self.feature_names, f)
        print(f"    ✓ feature_names.pkl")
        
        # Save metadata
        metadata = {
            'trained_at': datetime.now().isoformat(),
            'num_samples': len(self.df),
            'num_features': len(self.feature_names),
            'features': self.feature_names,
            'crops': self.le.classes_.tolist(),
            'model_scores': self.model_scores
        }
        
        metadata_path = os.path.join(model_dir, 'metadata.pkl')
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        print(f"    ✓ metadata.pkl")
        
        print(f"\n[✓] All models saved successfully!")
        
        return model_dir
    
    def train_all(self):
        """Run complete training pipeline"""
        print("=" * 70)
        print("Crop Recommendation Model Training Pipeline")
        print("=" * 70)
        print()
        
        # Load and prepare data
        self.load_data()
        self.prepare_data()
        
        # Train models
        self.train_random_forest()
        self.train_xgboost()
        # Skip gradient boosting - it's slower and less stable on this dataset
        # self.train_gradient_boosting()
        
        # Summary
        print("\n" + "=" * 70)
        print("Training Summary")
        print("=" * 70)
        
        for model_name, scores in self.model_scores.items():
            print(f"\n{model_name.upper()}:")
            print(f"  Test Accuracy:  {scores['accuracy']*100:.2f}%")
            print(f"  CV Score:       {scores['cv_mean']*100:.2f}% (±{scores['cv_std']*100:.2f}%)")
        
        # Save models
        self.save_models()
        
        print("\n[✓] Training complete! Models ready for inference.")


if __name__ == '__main__':
    trainer = CropModelTrainer()
    trainer.train_all()
