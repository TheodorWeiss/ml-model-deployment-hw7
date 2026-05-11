import json
import logging
import os
import pickle
from pathlib import Path

from flask import Flask, jsonify, request
from prometheus_client import Counter
from prometheus_flask_exporter import PrometheusMetrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ml-service")

MODEL_VERSION = os.environ.get("MODEL_VERSION", "v1.0.0")
MODEL_PATH = os.environ.get("MODEL_PATH", "artifacts/model.pkl")
METRICS_PATH = os.environ.get("METRICS_PATH", "artifacts/metrics.json")

app = Flask(__name__)

# Prometheus инструментация. Автоматически добавляет /metrics endpoint
# и трекает все HTTP-запросы: количество, латентность, статусы.
prom_metrics = PrometheusMetrics(app)
prom_metrics.info("app_info", "ML service info", version=MODEL_VERSION)

# Кастомный счётчик предсказаний с разбивкой по классам.
# Метка version будет добавлена самим Prometheus через scrape config.
predictions_counter = Counter(
    "predictions",
    "Total predictions made, by predicted class",
    ["class_name"],
)


def load_model():
    path = Path(MODEL_PATH)
    if not path.exists():
        raise FileNotFoundError(
            f"Model not found at {path.resolve()}. "
            "Run ml_pipeline.py first to train and save the model."
        )
    with open(path, "rb") as f:
        return pickle.load(f)


def load_metrics():
    path = Path(METRICS_PATH)
    if not path.exists():
        logger.warning(f"Metrics file not found at {path}, using defaults")
        return {}
    with open(path) as f:
        return json.load(f)


model = load_model()
metrics = load_metrics()
target_names = metrics.get("target_names", ["class_0", "class_1", "class_2"])
expected_n_features = metrics.get("n_features", 4)

logger.info(
    f"Model loaded. version={MODEL_VERSION}, "
    f"accuracy={metrics.get('accuracy', 'unknown')}, "
    f"expected_features={expected_n_features}"
)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "version": MODEL_VERSION,
    }), 200


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({
                "status": "error",
                "message": "Request body must be valid JSON",
            }), 400

        x = data.get("x")
        if x is None:
            return jsonify({
                "status": "error",
                "message": "JSON must contain key 'x' with a list of features",
            }), 400

        if not isinstance(x, list):
            return jsonify({
                "status": "error",
                "message": f"'x' must be a list, got {type(x).__name__}",
            }), 400

        if len(x) != expected_n_features:
            return jsonify({
                "status": "error",
                "message": (
                    f"'x' must have {expected_n_features} features, "
                    f"got {len(x)}"
                ),
            }), 400

        prediction = int(model.predict([x])[0])
        class_name = (
            target_names[prediction]
            if prediction < len(target_names)
            else str(prediction)
        )

        # Инкрементируем счётчик предсказаний для Prometheus
        predictions_counter.labels(class_name=class_name).inc()

        return jsonify({
            "status": "ok",
            "version": MODEL_VERSION,
            "prediction": prediction,
            "class_name": class_name,
        }), 200

    except Exception as e:
        logger.exception(f"Prediction failed: {e}")
        return jsonify({
            "status": "error",
            "message": "Internal server error",
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    logger.info(f"Starting Flask dev server on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)