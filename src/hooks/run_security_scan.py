from src.hooks_base import Hook


class RunSecurityScan(Hook):
    def validate_args(self) -> bool:
        # pre-commit can have files, but can also be passed nothing
        return True

    def run(self) -> bool:
        return True
