import json
import os
import pickle
from pathlib import Path

from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

ARTIFACTS_DIR = Path("artifacts")
ARTIFACTS_DIR.mkdir(exist_ok=True)

# Версия модели может быть задана через переменную окружения (в CI - через GitHub Secret)
MODEL_VERSION = os.environ.get("MODEL_VERSION", "v1.0.0")

# Гиперпараметры собраны в один dict, чтобы их можно было сохранить целиком
hyperparameters = {
    "n_estimators": 100,
    "random_state": 42,
    "test_size": 0.2,
}

# 1. Загрузка данных
iris = load_iris()
X, y = iris.data, iris.target
target_names = iris.target_names.tolist()

# 2. Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=hyperparameters["test_size"],
    random_state=hyperparameters["random_state"],
)

# 3. Обучение
model = RandomForestClassifier(
    n_estimators=hyperparameters["n_estimators"],
    random_state=hyperparameters["random_state"],
)
model.fit(X_train, y_train)

# 4. Оценка
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred, target_names=target_names, output_dict=True)

# 5. Сохранение артефактов - это и есть "Make pipeline reproducible"
with open(ARTIFACTS_DIR / "model.pkl", "wb") as f:
    pickle.dump(model, f)

with open(ARTIFACTS_DIR / "hyperparameters.json", "w") as f:
    json.dump(hyperparameters, f, indent=2)

metrics = {
    "model_version": MODEL_VERSION,
    "accuracy": accuracy,
    "n_features": X.shape[1],
    "n_classes": len(target_names),
    "target_names": target_names,
    "n_samples_train": len(X_train),
    "n_samples_test": len(X_test),
    "classification_report": report,
}
with open(ARTIFACTS_DIR / "metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

print("=" * 50)
print(f"ML Pipeline finished")
print(f"Model version: {MODEL_VERSION}")
print(f"Accuracy:      {accuracy:.4f}")
print(f"Artifacts:     {ARTIFACTS_DIR.resolve()}")
print(f"  - model.pkl ({(ARTIFACTS_DIR / 'model.pkl').stat().st_size} bytes)")
print(f"  - hyperparameters.json")
print(f"  - metrics.json")
print("=" * 50)