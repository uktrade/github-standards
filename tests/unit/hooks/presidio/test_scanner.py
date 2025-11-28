import pickle
from presidio_analyzer import RecognizerResult
import pytest
import tempfile


from src.hooks.presidio.scanner import PersonalDataDetection, PresidioScanner
from unittest.mock import ANY, MagicMock, call, patch


class TestPresidioScanner:
    @pytest.mark.parametrize("file_extension", [".csv"])
    def test_scan_path_scans_line_by_line_for_file_extensions(self, file_extension):
        with patch.object(PresidioScanner, "_scan_line_by_line") as mock_scan_line_by_line:
            list(PresidioScanner()._scan_path(MagicMock(), [], f"file1{file_extension}"))
            mock_scan_line_by_line.assert_called()

    @pytest.mark.parametrize("file_extension", [".txt", ".yaml"])
    def test_scan_path_scans_file_contents_for_file_extensions(self, file_extension):
        with patch.object(PresidioScanner, "_scan_file_contents") as mock__scan_file_contents:
            list(PresidioScanner()._scan_path(MagicMock(), [], f"file1{file_extension}"))
            mock__scan_file_contents.assert_called()

    def test_scan_line_by_line_returns_detections_list_when_path_has_personal_data(self):
        with (
            tempfile.NamedTemporaryFile(suffix=".txt", mode="w+t") as tf,
        ):
            contents = "I have personal data"
            tf.write(contents)
            tf.seek(0)

            recognizer_results = [RecognizerResult("EMAIL", 0, 100, 1.0), RecognizerResult("PERSON", 0, 100, 0.9)]
            expected_scan_results = [PersonalDataDetection(tf.name, f, contents) for f in recognizer_results]

            mock_analyzer = MagicMock()
            mock_analyzer.analyze.return_value = recognizer_results

            detections = list(PresidioScanner()._scan_line_by_line(mock_analyzer, [], tf.name))

            assert pickle.dumps(detections) == pickle.dumps(expected_scan_results)

    def test_scan_file_contents_returns_detections_list_when_path_has_personal_data(self):
        with (
            tempfile.NamedTemporaryFile(suffix=".txt", mode="w+t") as tf,
        ):
            contents = "I have personal data"
            tf.write(contents)
            tf.seek(0)

            recognizer_results = [RecognizerResult("EMAIL", 0, 100, 1.0), RecognizerResult("PERSON", 0, 100, 0.9)]
            expected_scan_results = [PersonalDataDetection(tf.name, f, contents) for f in recognizer_results]

            mock_analyzer = MagicMock()
            mock_analyzer.analyze.return_value = recognizer_results

            detections = list(PresidioScanner()._scan_file_contents(mock_analyzer, [], tf.name))

            assert pickle.dumps(detections) == pickle.dumps(expected_scan_results)

    def test_scan_with_no_paths_returns_empty_detections_list(self):
        with patch("src.hooks.presidio.scanner.PathFilter") as mock_path_filter:
            mock_path_filter.return_value.get_paths_to_scan.return_value = []
            assert list(PresidioScanner().scan()) == []

    def test_scan_calls_scan_path_for_every_path_returned_from_get_paths_to_scan(self):
        with (
            patch("src.hooks.presidio.scanner.PathFilter") as mock_path_filter,
            patch.object(PresidioScanner, "_scan_path") as mock_scan_path,
        ):
            mock_path_filter.return_value.get_paths_to_scan.return_value = ["file1.txt", "file3.csv"]
            list(PresidioScanner(paths=["file1.txt", "file2.txt", "file3.csv"]).scan())
            mock_scan_path.assert_has_calls([call(ANY, ANY, "file1.txt"), call(ANY, ANY, "file3.csv")], any_order=True)
