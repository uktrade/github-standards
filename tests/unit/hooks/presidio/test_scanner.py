import pickle
import pytest

from anyio import NamedTemporaryFile
from presidio_analyzer import RecognizerResult

from src.hooks.presidio.path_filter import PathFilter, PathScanStatus
from src.hooks.presidio.scanner import PersonalDataDetection, PresidioScanResult, PresidioScanner, PathScanResult
from unittest.mock import ANY, MagicMock, call, patch


class TestPresidioScanResult:
    @pytest.mark.parametrize(
        "status,attr_name",
        [
            (PathScanStatus.EXCLUDED, "paths_excluded"),
            (PathScanStatus.FAILED, "paths_containing_personal_data"),
            (PathScanStatus.PASSED, "paths_without_personal_data"),
            (PathScanStatus.SKIPPED, "paths_skipped"),
            (PathScanStatus.ERRORED, "paths_errored"),
        ],
    )
    def test_add_path_scan_result_adds_result_to_expected_paths_list(self, status, attr_name):
        result = PresidioScanResult()

        assert len(getattr(result, attr_name)) == 0
        result.add_path_scan_result(PathScanResult("a.txt", status))
        assert len(getattr(result, attr_name)) == 1

    def test_str_output_for_error(self):
        result = PresidioScanResult()
        result.add_path_scan_result(PathScanResult("a.txt", PathScanStatus.ERRORED, additional_detail="Additional details"))
        assert str(result) == ""


class TestPresidioScanner:
    async def test_scan_path_returns_when_invalid_path(self):
        with (
            patch.object(PathFilter, "_check_is_path_invalid") as mock_check_is_path_invalid,
        ):
            mock_check_is_path_invalid.return_value = PathScanStatus.EXCLUDED
            result = await PresidioScanner()._scan_path(MagicMock(), [], "a", [])

            assert result.status == PathScanStatus.EXCLUDED

    @pytest.mark.parametrize("file_extension", [".csv"])
    async def test_scan_path_scans_line_by_line_for_file_extensions_with_expected_results(self, file_extension):
        async with NamedTemporaryFile(suffix=f"file1{file_extension}", mode="w+t") as tf:
            with patch.object(PresidioScanner, "_scan_content") as mock_scan_content:
                await tf.write("Has Email\nNo data\nHas phone")
                await tf.seek(0)

                found_email = PersonalDataDetection(RecognizerResult("EMAIL", 0, 10, 1), text_value="A")
                found_phone = PersonalDataDetection(RecognizerResult("PHONE", 0, 10, 1), text_value="B")

                expected_scan_result = PathScanResult(tf.name, PathScanStatus.FAILED, [found_email, found_phone])
                mock_scan_content.side_effect = [
                    [found_email],
                    [],
                    [found_phone],
                ]

                result = await PresidioScanner()._scan_path(MagicMock(), [], tf.name, [])
                mock_scan_content.assert_has_calls(
                    [
                        call(ANY, ANY, "Has Email"),
                        call(ANY, ANY, "No data"),
                        call(ANY, ANY, "Has phone"),
                    ],
                    any_order=True,
                )
                assert pickle.dumps(result) == pickle.dumps(expected_scan_result)

    @pytest.mark.parametrize("file_extension", [".txt", ".yaml"])
    async def test_scan_path_scans_file_contents_for_file_extensions_with_expected_results(self, file_extension):
        async with NamedTemporaryFile(suffix=f"file1{file_extension}", mode="w+t") as tf:
            with patch.object(PresidioScanner, "_scan_content") as mock_scan_content:
                contents = "Has Email\nNo data"
                await tf.write(contents)
                await tf.seek(0)

                found_email = PersonalDataDetection(RecognizerResult("EMAIL", 0, 10, 1), text_value="A")

                expected_scan_result = PathScanResult(tf.name, PathScanStatus.FAILED, [found_email])
                mock_scan_content.return_value = [found_email]

                result = await PresidioScanner()._scan_path(MagicMock(), [], tf.name, [])

                mock_scan_content.assert_called_once_with(ANY, ANY, contents)
                assert pickle.dumps(result) == pickle.dumps(expected_scan_result)

    async def test_scan_path_handles_exception(self):
        async with NamedTemporaryFile(suffix="file1.csv", mode="w+t") as tf:
            with patch.object(PresidioScanner, "_scan_content") as mock_scan_content:
                mock_scan_content.side_effect = Exception("An exception message")
                contents = "Error reading this file"
                await tf.write(contents)
                await tf.seek(0)

                result = await PresidioScanner()._scan_path(MagicMock(), [], tf.name, [])
                assert result.status == PathScanStatus.ERRORED
                assert result.additional_detail == "An exception message"

    def test_scan_content_returns_detections_list_when_path_has_personal_data(self):
        contents = "I have personal data"

        recognizer_results = [RecognizerResult("EMAIL", 0, 100, 1.0), RecognizerResult("PERSON", 0, 100, 0.9)]
        expected_scan_results = [PersonalDataDetection(f, contents) for f in recognizer_results]

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = recognizer_results

        detections = list(PresidioScanner()._scan_content(mock_analyzer, [], contents))

        assert pickle.dumps(detections) == pickle.dumps(expected_scan_results)

    def test_scan_content_returns_no_detections_when_path_has_no_personal_data(self):
        contents = "I have no personal data"

        recognizer_results = []
        expected_scan_results = []

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = recognizer_results

        detections = list(PresidioScanner()._scan_content(mock_analyzer, [], contents))

        assert pickle.dumps(detections) == pickle.dumps(expected_scan_results)

    async def test_scan_with_no_paths_returns_result_with_empty_paths(self):
        with patch.object(PathFilter, "_get_exclusions") as mock_path_filter:
            mock_path_filter.return_value = []

            result = await PresidioScanner().scan()
            assert result.paths_containing_personal_data == []
            assert result.paths_without_personal_data == []

    async def test_scan_calls_scan_path_for_every_path(self):
        with (
            patch.object(PathFilter, "_get_exclusions") as mock_path_filter,
            patch.object(PresidioScanner, "_scan_path") as mock_scan_path,
        ):
            mock_path_filter.return_value = []
            test_paths = ["a.txt", "b.yml", "c.py"]

            await PresidioScanner(paths=test_paths).scan()

            mock_scan_path.assert_has_calls([call(ANY, ANY, path, []) for path in test_paths])
