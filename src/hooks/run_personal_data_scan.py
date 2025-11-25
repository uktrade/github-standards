from src.hooks.config import LOGGER
from src.hooks.hooks_base import Hook, HookRunResult

logger = LOGGER


class RunPersonalDataScan(Hook):
    def validate_args(self) -> bool:
        return True

    def _validate_hook_settings(self, dbt_repo_config) -> bool:
        return True

    def run(self) -> HookRunResult:
        return HookRunResult(True)
