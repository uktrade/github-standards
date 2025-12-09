from src.hooks.config import LOGGER
from src.hooks.hooks_base import Hook, HookRunResult

logger = LOGGER


class RunPersonalDataScanResult(HookRunResult):
    def run_success(self) -> bool:
        return True

    def run_summary(self) -> str | None:
        return None


class RunPersonalDataScan(Hook):
    def validate_args(self) -> bool:
        return True

    def _validate_hook_settings(self, dbt_repo_config) -> bool:
        return True

    async def run(self) -> RunPersonalDataScanResult:
        return RunPersonalDataScanResult()
