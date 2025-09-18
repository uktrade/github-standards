import tempfile

from src.hooks.validate_security_scan import ValidateSecurityScan


class TestValidateSecurityScan:
    def test_none_file_list_returns_false(self):
        assert ValidateSecurityScan(files=None).validate_args() is False

    def test_empty_file_list_returns_false(self):
        assert ValidateSecurityScan(files=[]).validate_args() is False

    def test_file_list_with_more_than_one_item_returns_false(self):
        assert ValidateSecurityScan(files=["a.txt", "b.txt"]).validate_args() is False

    def test_file_list_with_one_item_returns_true(self):
        assert ValidateSecurityScan(files=["a.txt"]).validate_args() is True

    def test_file_with_no_contents_returns_error_code(self):
        with tempfile.NamedTemporaryFile() as tf:
            assert ValidateSecurityScan(files=[tf.name]).run() is False

    def test_file_with_message_has_signed_off_by_trailer_added(self):
        with tempfile.NamedTemporaryFile() as tf:
            tf.write(b"A helpful commit message")
            tf.seek(0)
            assert ValidateSecurityScan(files=[tf.name]).run() is True

            assert tf.read().decode("UTF-8") == f"A helpful commit message\n\n{ValidateSecurityScan.SIGNED_OFF_BY_TRAILER}"

    def test_file_with_existing_signed_off_header_is_replaced(self):
        with tempfile.NamedTemporaryFile() as tf:
            tf.write(b"A helpful commit message\n\Signed-off-by: SOMETHING ELSE")
            tf.seek(0)

            assert ValidateSecurityScan(files=[tf.name]).run() is True

            assert tf.read().decode("UTF-8") == f"A helpful commit message\n\n{ValidateSecurityScan.SIGNED_OFF_BY_TRAILER}"
