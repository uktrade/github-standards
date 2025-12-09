from src.hooks.run_personal_data_scan import RunPersonalDataScan


class TestRunPersonalDataScan:
    def test_validate_args_returns_true(self):
        assert RunPersonalDataScan().validate_args() is True

    async def test_run_returns_true(self):
        assert (await RunPersonalDataScan().run()) is not None
