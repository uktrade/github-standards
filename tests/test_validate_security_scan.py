import tempfile
import pytest
import sys

from unittest import mock
from hooks.validate_security_scan import SIGNED_OFF_BY_TRAILER, main as validate_security_scan
from logging import DEBUG, INFO


class TestValidateSecurityScanTests:
    @pytest.mark.parametrize("log_level", ["-v", "--verbose"])
    def test_log_set_to_correct_level_when_verbose_log_type_is_provided(self, log_level):
        testargs = ["validate-security-scan", log_level, ".git/COMMIT_EDITMSG"]
        with (
            mock.patch.object(sys, "argv", testargs),
            mock.patch("hooks.validate_security_scan.LOG") as mockLogger,
        ):
            validate_security_scan()
            mockLogger.setLevel.assert_called_once_with(DEBUG)

    def test_log_set_to_default_level_when_verbose_is_not_provided(self):
        testargs = ["validate-security-scan", ".git/COMMIT_EDITMSG"]

        with (
            mock.patch.object(sys, "argv", testargs),
            mock.patch("hooks.validate_security_scan.LOG") as mockLogger,
        ):
            validate_security_scan()
            mockLogger.setLevel.assert_called_once_with(INFO)

    def test_empty_filename_returns_error_code(self):
        testargs = ["validate-security-scan", ""]

        with (
            mock.patch.object(sys, "argv", testargs),
        ):
            assert validate_security_scan() == 1

    def test_file_with_no_contents_returns_error_code(self):
        with tempfile.NamedTemporaryFile() as tf:
            testargs = ["validate-security-scan", tf.name]
            with (
                mock.patch.object(sys, "argv", testargs),
            ):
                assert validate_security_scan() == 1

    def test_file_with_message_has_signed_off_by_trailer_added(self):
        with tempfile.NamedTemporaryFile() as tf:
            tf.write(b"A helpful commit message")
            tf.seek(0)
            testargs = ["validate-security-scan", "-v", tf.name]
            with (
                mock.patch.object(sys, "argv", testargs),
            ):
                assert validate_security_scan() == 0
                assert (
                    tf.read().decode("UTF-8")
                    == f"A helpful commit message\n\n{SIGNED_OFF_BY_TRAILER}"
                )

    def test_file_with_existing_signed_off_header_is_replaced(self):
        with tempfile.NamedTemporaryFile() as tf:
            tf.write(b"A helpful commit message\n\Signed-off-by: SOMETHING ELSE")
            tf.seek(0)
            testargs = ["validate-security-scan", "-v", tf.name]
            with (
                mock.patch.object(sys, "argv", testargs),
            ):
                assert validate_security_scan() == 0
                assert (
                    tf.read().decode("UTF-8")
                    == f"A helpful commit message\n\n{SIGNED_OFF_BY_TRAILER}"
                )
