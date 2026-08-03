# anykeep

A lightweight tool for parsing Google Keep notes and preparing them for Anytype export.

## Setup

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Google Keep API access

Real Google Keep API calls require Google Cloud credentials and the Keep API enabled.

The recommended flow is:

1. Create a Google Cloud project.
2. Enable the Google Keep API.
3. Configure Application Default Credentials (ADC):

```bash
gcloud auth application-default login
```

4. Run the parser against a real account:

```bash
python - <<'PY'
from src.keep_parser import KeepParser

parser = KeepParser()
notes = parser.list_notes()
print(notes[:3])
PY
```

## Testing

Run unit tests:

```bash
python -m pytest -q
```
