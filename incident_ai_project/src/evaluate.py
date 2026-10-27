"""Train, evaluate on held-out synthetic incidents, and save reproducible metrics."""
import csv
import json
from pathlib import Path
import joblib
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from incident_ai import CATEGORIES, MODEL_FILE, classify, train

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    with (ROOT / 'data' / name).open(newline='', encoding='utf-8') as fh:
        return list(csv.DictReader(fh))

def baseline(message):
    """Naive keyword rules as a comparison, not an AI model."""
    rules = {'security': ('malware', 'unauthorized', 'ransomware', 'breach'),
             'network': ('packet', 'dns', 'latency', 'connection'),
             'storage': ('disk', 'volume', 'capacity', 'storage'),
             'database': ('database', 'sql', 'query', 'replica'),
             'compute': ('cpu', 'memory', 'instance', 'container')}
    lower = message.lower()
    for category, keywords in rules.items():
        if any(word in lower for word in keywords):
            return category
    return 'compute'

def main():
    training, testing = load('train.csv'), load('test.csv')
    assert not ({r['message'] for r in training} & {r['message'] for r in testing}), 'data leakage'
    model = train(training)
    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_FILE)
    actual = [r['category'] for r in testing]
    outputs = [classify(r['message'], model) for r in testing]
    predicted = [r['category'] for r in outputs]
    base = [baseline(r['message']) for r in testing]
    metrics = {
        'dataset': 'synthetic, author-created; not real patient or production incident data',
        'train_count': len(training), 'test_count': len(testing),
        'accuracy': accuracy_score(actual, predicted),
        'macro_f1': f1_score(actual, predicted, average='macro', zero_division=0),
        'baseline_accuracy': accuracy_score(actual, base),
        'baseline_macro_f1': f1_score(actual, base, average='macro', zero_division=0),
        'median_latency_ms': float(np.median([r['latency_ms'] for r in outputs])),
        'manual_review_count': sum(r['manual_review'] for r in outputs),
        'classification_report': classification_report(actual, predicted, labels=list(CATEGORIES), output_dict=True, zero_division=0),
        'confusion_matrix_labels': list(CATEGORIES),
        'confusion_matrix': confusion_matrix(actual, predicted, labels=list(CATEGORIES)).tolist(),
    }
    (ROOT / 'results' / 'metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    with (ROOT / 'results' / 'predictions.csv').open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['message', 'actual', 'predicted', 'confidence', 'manual_review', 'latency_ms'])
        writer.writeheader()
        for sample, result in zip(testing, outputs):
            writer.writerow({'message': sample['message'], 'actual': sample['category'],
                             'predicted': result['category'], 'confidence': result['confidence'],
                             'manual_review': result['manual_review'], 'latency_ms': result['latency_ms']})
    print(json.dumps({k: v for k, v in metrics.items() if k not in ('classification_report', 'confusion_matrix')}, indent=2))
if __name__ == '__main__':
    main()
