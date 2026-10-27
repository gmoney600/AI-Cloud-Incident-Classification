"""Offline, reproducible AI incident triage prototype. No AWS credentials required."""
from __future__ import annotations
import json
import time
from pathlib import Path
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

CATEGORIES = ('database', 'network', 'security', 'storage', 'compute')
ROUTES = {'database': 'Database Operations', 'network': 'Network Operations',
          'security': 'Security Operations', 'storage': 'Storage Operations',
          'compute': 'Cloud Infrastructure'}
MODEL_FILE = Path(__file__).resolve().parents[1] / 'results' / 'model.joblib'

def train(records):
    """Train solely on training split; never expose test samples during fitting."""
    model = Pipeline([('tfidf', TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
                      ('classifier', LogisticRegression(max_iter=1500, random_state=42))])
    model.fit([r['message'] for r in records], [r['category'] for r in records])
    return model

def classify(message, model, confidence_threshold=0.30):
    """Advisory-only routing; low-confidence predictions require manual review."""
    if not isinstance(message, str) or not message.strip() or len(message) > 5000:
        raise ValueError('message must be nonempty text of at most 5000 characters')
    started = time.perf_counter()
    probs = model.predict_proba([message])[0]
    idx = probs.argmax()
    category = str(model.classes_[idx])
    confidence = float(probs[idx])
    review = confidence < confidence_threshold
    severity = ('high' if any(w in message.lower() for w in
                ('outage', 'unavailable', 'breach', 'ransomware', 'critical', 'data loss'))
                else 'medium')
    return {'category': category, 'confidence': round(confidence, 4),
            'severity': severity, 'team': 'Human Triage' if review else ROUTES[category],
            'manual_review': review, 'action': 'Review alert and verify root cause; no automated remediation',
            'latency_ms': round((time.perf_counter() - started) * 1000, 3)}

def lambda_handler(event, context):
    """Optional AWS Lambda entry point; package joblib and dependencies in deployment."""
    model = joblib.load(MODEL_FILE)
    try:
        msg = event.get('message', '')
        return {'statusCode': 200, 'body': json.dumps(classify(msg, model))}
    except (ValueError, AttributeError) as exc:
        return {'statusCode': 400, 'body': json.dumps({'error': str(exc)})}
