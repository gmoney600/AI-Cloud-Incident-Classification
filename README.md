# AI-Assisted Cloud Incident Classification



## Quick start

Python 3.10+ recommended. In a terminal at the repository root:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python src/evaluate.py
python -m unittest discover -s tests -v
```

Results appear in `results/metrics.json`, `results/predictions.csv`, and `results/test_output.txt` (the included files were produced by a real local execution). The model artifact is `results/model.joblib`. The metrics are specific to the included small synthetic dataset and should not be generalized to operational incidents.

## Design

Synthetic alert text -> Python handler -> TF-IDF (unigrams/bigrams) -> logistic regression -> predicted incident class -> confidence-based human review gate -> advisory routing recommendation. Severity is a separate **heuristic**, not an AI prediction. No infrastructure changes are performed.

Categories: database, network, security, storage, compute. Training and testing use separate sentences (35 train, 15 test), with no identical messages in both splits. Both sets are synthetic, manually authored; this is a small feasibility demonstration, not a validated operational model.

## Files

- `src/incident_ai.py`: training, prediction, validation, and optional Lambda handler.
- `src/evaluate.py`: baseline comparison, holdout evaluation, metrics and CSV outputs.
- `data/train.csv`, `data/test.csv`: labeled synthetic examples.
- `tests/test_incident_ai.py`: five functional and safety tests.
- `results/`: measured output, model and test logs.
- `deploy/`: sample events and AWS integration guidance.

## Deployment concept

1. Create an AWS Lambda Python function in a suitable region and role with minimum required permissions.
2. Package `src/incident_ai.py`, the trusted serialized model, scikit-learn, numpy, scipy and joblib in a Lambda-compatible container image (recommended due to native libraries).
3. Set the model path appropriately in the container image, or adapt `MODEL_FILE` to the image's mounted path. Do not load untrusted joblib files.
4. Connect an EventBridge rule for selected CloudWatch alarm state changes, with a transformation that maps `detail.state.reason` into the `message` field. The sample raw CloudWatch event is **not** directly compatible with the simple handler without this mapping.
5. Route outputs to a logging or ticketing system after redaction, add access controls, monitoring, and dead-letter handling. Do not enable autonomous remediation.
6. Test with nonproduction events, verify CloudWatch Logs, and obtain approval before using production alert data.

These steps describe a possible cloud deployment; the submission only validates local execution.

## Safety and limitations

Confidence is not calibrated. At the default 0.30 threshold, 14 of 15 held-out samples were flagged for manual review. The model achieved 10/15 accuracy, tied with a naive keyword baseline. The synthetic dataset is too small for robust claims. Severity uses keyword matching and can miss real emergencies. No protected health information should be included in alerts. Never use the classifier alone for high-impact decisions.

## Reproducibility

Training uses `random_state=42`, and the CSV splits are checked for exact text overlap. Runtime timing depends on hardware and library versions. Run evaluation again to regenerate metrics. The included `results/model.joblib` should only be loaded if you trust this package; joblib deserialization is unsafe for untrusted inputs.

## Repository publishing

Create an empty GitHub repository, then from this folder run:

```bash
git init
git add .
git commit -m "Add AI incident triage prototype and evaluation"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```


