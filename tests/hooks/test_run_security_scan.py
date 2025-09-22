from src.hooks.run_security_scan import RunSecurityScan


class TestRunSecurityScan:
    def test_validate_args_returns_true(self):
        assert RunSecurityScan().validate_args() is True

    def test_run_returns_true(self):
        assert RunSecurityScan().run() is True
