# AWS integration plan (not deployed)

Architecture: CloudWatch alarm -> EventBridge rule/input transformer -> Lambda (model + inference code) -> log/ticket integration -> human reviewer. Use least-privilege IAM, no network egress unless needed, encryption, log retention, and alarms for errors and throttles. Map the raw alarm event's `detail.state.reason` to `message`. Prefer a Lambda container image built for the chosen Python runtime and CPU architecture to include scikit-learn native dependencies. Include `results/model.joblib` at a known image path and modify MODEL_FILE accordingly. No cloud resources were created for this project.

Verification plan: invoke with `deploy/lambda_event.json`; assert HTTP 200, valid category, and human review routing on low confidence; invoke invalid payload and assert HTTP 400; confirm no write permissions or remediation calls exist. Obtain instructor approval before connecting production alerts.
