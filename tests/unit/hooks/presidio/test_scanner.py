import pickle
from presidio_analyzer import RecognizerResult
import pytest
import tempfile


from src.hooks.presidio.scanner import PersonalDataDetection, PresidioScanner, PathScanResult
from unittest.mock import ANY, AsyncMock, MagicMock, call, patch


class TestPresidioScanner:
    @pytest.mark.parametrize("file_extension", [".csv"])
    async def test_scan_path_scans_line_by_line_for_file_extensions_with_expected_results(self, file_extension):
        with (
            patch.object(PresidioScanner, "_scan_content") as mock_scan_content,
            tempfile.NamedTemporaryFile(suffix=f"file1{file_extension}", mode="w+t") as tf,
        ):
            tf.write("Has Email\nNo data\nHas phone")
            tf.seek(0)

            found_email = PersonalDataDetection(RecognizerResult("EMAIL", 0, 10, 1), text_value="A")
            found_phone = PersonalDataDetection(RecognizerResult("PHONE", 0, 10, 1), text_value="B")

            expected_scan_result = PathScanResult(tf.name, [found_email, found_phone])
            mock_scan_content.side_effect = [
                [found_email],
                [],
                [found_phone],
            ]

            result = await PresidioScanner()._scan_path(MagicMock(), [], tf.name)
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
        with (
            patch.object(PresidioScanner, "_scan_content") as mock_scan_content,
            tempfile.NamedTemporaryFile(suffix=f"file1{file_extension}", mode="w+t") as tf,
        ):
            contents = "Has Email\nNo data"
            tf.write(contents)
            tf.seek(0)

            found_email = PersonalDataDetection(RecognizerResult("EMAIL", 0, 10, 1), text_value="A")

            expected_scan_result = PathScanResult(tf.name, [found_email])
            mock_scan_content.return_value = [found_email]

            result = await PresidioScanner()._scan_path(MagicMock(), [], tf.name)

            mock_scan_content.assert_called_once_with(ANY, ANY, contents)
            assert pickle.dumps(result) == pickle.dumps(expected_scan_result)

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

    async def test_scan_with_no_paths_returns_empty_detections_list(self):
        with patch("src.hooks.presidio.scanner.PathFilter") as mock_path_filter:
            mock_path_filter.return_value.get_paths_to_scan.return_value = AsyncMock(return_value=[])

            result = await PresidioScanner().scan()
            assert result.invalid_path_scans == []
            assert result.valid_path_scans == []

    async def test_scan_calls_scan_path_for_every_path_returned_from_get_paths_to_scan(self):
        with (
            patch("src.hooks.presidio.scanner.PathFilter") as mock_path_filter,
            patch.object(PresidioScanner, "_scan_path") as mock_scan_path,
        ):
            mock_path_filter.return_value.get_paths_to_scan.return_value.__aiter__.return_value = ["file1.txt", "file3.csv"]
            mock_scan_path.side_effect = [PathScanResult("file1.txt", results=[]), PathScanResult("file3.csv", results=[])]

            result = await PresidioScanner(paths=["file1.txt", "file2.txt", "file3.csv"]).scan()
            assert len(result.invalid_path_scans) == 0
            assert len(result.valid_path_scans) == 2

            mock_scan_path.assert_has_calls([call(ANY, ANY, "file1.txt"), call(ANY, ANY, "file3.csv")], any_order=True)
