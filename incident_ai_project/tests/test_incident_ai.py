import csv
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from incident_ai import train, classify

class IncidentAITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / 'data' / 'train.csv').open(newline='', encoding='utf-8') as f:
            cls.model = train(list(csv.DictReader(f)))

    def test_valid_response(self):
        result = classify('Database queries are timing out', self.model)
        self.assertIn(result['category'], {'database', 'network', 'security', 'storage', 'compute'})
        self.assertTrue(0 <= result['confidence'] <= 1)
        self.assertIn('team', result)

    def test_empty_alert_rejected(self):
        with self.assertRaises(ValueError):
            classify('   ', self.model)

    def test_oversized_alert_rejected(self):
        with self.assertRaises(ValueError):
            classify('a' * 5001, self.model)

    def test_human_review_gate(self):
        result = classify('unfamiliar ambiguous alert', self.model, confidence_threshold=1.0)
        self.assertTrue(result['manual_review'])
        self.assertEqual(result['team'], 'Human Triage')

    def test_no_autonomous_remediation(self):
        result = classify('Ransomware breach detected', self.model)
        self.assertIn('no automated remediation', result['action'])
        self.assertEqual(result['severity'], 'high')

if __name__ == '__main__':
    unittest.main()
