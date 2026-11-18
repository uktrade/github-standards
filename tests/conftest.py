import logging
import subprocess
import sys

import pytest


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


@pytest.fixture
def modules_loaded_by_importing():
    # Runs in a fresh interpreter because the test session has already imported most modules
    def _modules_loaded_by_importing(*modules: str) -> set[str]:
        code = f"import sys, {', '.join(modules)}; print('\\n'.join(sys.modules))"
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
        return set(result.stdout.split())

    return _modules_loaded_by_importing
