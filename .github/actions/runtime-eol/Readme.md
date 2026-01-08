# Runtime EOL Check Action

This composite GitHub Action validates whether the language runtime used in a workflow is **end‑of‑life (EOL)** or below the minimum supported version.

## Usage

```yaml
on:
  pull_request:
    branches: [ main ]

# ...

permissions:
  id-token: write
  contents: read
  issues: write
  pull-requests: write

jobs:
  Vulnerability-Checks:
    runs-on: ubuntu-latest
    steps:
      - name: "Git clone the repository"
        uses: actions/checkout@v6

      - name: Python Runtime End of Life check
        if: github.event_name == 'pull_request'
        uses: uktrade/actions/runtime-eol/python@latest
        continue-on-error: true
        with:
          python-version: ${{ vars.PY_VERSION }}

  # ...
```

## Output

The action produces:

- `PY_VERSION` — the detected Python major.minor version
- `PYTHON_TOO_OLD` — a boolean flag (`true` or `false`) exported to the workflow environment for downstream steps when needed

Furthermore, more information for the action message is produced:

- `docs-url` Link to official lifecycle/EOL documentation
- `min-version` Minimum supported version

### Behaviour

- If the detected version is **below** the configured `min-version`:
  - A warning PR comment is created
  - `PYTHON_TOO_OLD=true` is set
  - Downstream steps can skip audits or send a PR comment

- If the version is **supported**:
  - `PYTHON_TOO_OLD=false` remains set
  - Any workflow continues normally

## Inputs

| Name             | Required | Default | Description |
|------------------|----------|---------|-------------|
| `min-version`    | No       | `3.10`  | Minimum supported Python version as of Jan 2026. |
| `python-version` | Yes      | —       | `actions/setup-python` will try to resolve the runtime version based on `python-version`, `python-version-file`, or a `.python-version` file. If no inputs are provided, it will default to the minimum available version. |

## How It Works

- The action extracts the Python version using `sys.version_info`
- It normalises the version to `major.minor` (e.g., `3.9`)
- It compares versions using semantic sorting (`sort -V`)
- It sets `PYTHON_TOO_OLD=true` only when the version is below the minimum
- It does **not** post comments itself — this is delegated to `notify/runtime-eol`

## When to Use This Action

Use this action when you want to:

- Prevent audits from running on unsupported Python versions
- Enforce organisation‑wide minimum runtime standards
- Avoid false positives in vulnerability scans caused by EOL interpreters
