import os
import pytest
import subprocess

from pathlib import Path
from unittest.mock import MagicMock, patch

from anyio import NamedTemporaryFile

from src.hooks.config import SIGNED_OFF_BY_TRAILER as TRAILER
from src.hooks.validate_security_scan import ValidateSecurityScan, ValidateSecurityScanResult


@pytest.fixture(autouse=True)
def isolated_git_config(tmp_path, monkeypatch):
    # Run git outside any repository and without the developer's own git config so results don't depend on either
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.chdir(tmp_path)


def pr_check_finds_trailer(message: str) -> bool:
    # The check in .github/workflows/org.common-ci.yml: git log --format=%B | git interpret-trailers --parse | grep
    parsed = subprocess.run(["git", "interpret-trailers", "--parse"], input=message, capture_output=True, text=True)
    return TRAILER in parsed.stdout.splitlines()


def write_commit_msg(tmp_path, message: bytes) -> Path:
    commit_msg = tmp_path / "COMMIT_EDITMSG"
    commit_msg.write_bytes(message)
    return commit_msg


async def run_on_message(tmp_path, message: bytes) -> tuple[ValidateSecurityScanResult, str]:
    commit_msg = write_commit_msg(tmp_path, message)
    result = await ValidateSecurityScan(paths=[str(commit_msg)]).run()
    # git --in-place replaces the file atomically so reopen by path rather than reading an open file handle
    new_message = commit_msg.read_text()
    if result.success:
        assert pr_check_finds_trailer(new_message)
    return result, new_message


class TestValidateSecurityScan:
    def test_validate_args_none_path_list_returns_false(self):
        assert ValidateSecurityScan(paths=None).validate_args() is False

    def test_validate_args_empty_path_list_returns_false(self):
        assert ValidateSecurityScan(paths=[]).validate_args() is False

    def test_validate_args_path_list_with_more_than_one_item_returns_false(self):
        assert ValidateSecurityScan(paths=["a.txt", "b.txt"]).validate_args() is False

    def test_validate_args_path_list_with_one_item_returns_true(self):
        assert ValidateSecurityScan(paths=["a.txt"]).validate_args() is True

    async def test_validate_hook_settings_with_bist_hooks_repo_present_without_hooks_element_in_pre_commit_file_returns_false(
        self,
    ):
        with (
            patch.object(ValidateSecurityScan, "_enforce_settings_checks", return_value=True),
        ):
            repo = {"repo": "https://github.com/uktrade/github-standards", "rev": "v1"}

            assert await ValidateSecurityScan()._validate_hook_settings(repo) is False

    async def test_validate_hook_settings_with_bist_hooks_repo_present_without_ids_element_in_pre_commit_file_returns_false(
        self,
    ):
        with (
            patch.object(ValidateSecurityScan, "_enforce_settings_checks", return_value=True),
        ):
            repo = {"repo": "https://github.com/uktrade/github-standards", "rev": "v1", "hooks": ["version"]}

            assert await ValidateSecurityScan()._validate_hook_settings(repo) is False

    async def test_validate_hook_settings_with_bist_hooks_repo_present_without_mandatory_is_in_pre_commit_file_returns_false(
        self,
    ):
        with (
            patch.object(ValidateSecurityScan, "_enforce_settings_checks", return_value=True),
        ):
            repo = {"repo": "https://github.com/uktrade/github-standards", "rev": "v1", "hooks": [{"id": "something"}]}
            assert await ValidateSecurityScan()._validate_hook_settings(repo) is False

    async def test_validate_hook_settings_with_repo_and_hooks_present_in_pre_commit_file_returns_true(self):
        with (
            patch.object(ValidateSecurityScan, "_enforce_settings_checks", return_value=True),
        ):
            repo = {
                "repo": "https://github.com/uktrade/github-standards",
                "rev": "v1",
                "hooks": [{"id": "validate-security-scan"}, {"id": "run-security-scan"}, {"id": "run-personal-data-scan"}],
            }
            assert await ValidateSecurityScan()._validate_hook_settings(repo) is True

    async def test_run_with_file_with_no_contents_returns_error_code(self):
        async with NamedTemporaryFile() as tf:
            result = await ValidateSecurityScan(paths=[tf.name]).run()
            assert result.success is False

    @pytest.mark.parametrize(
        "message,expected",
        [
            (b"A helpful commit message", f"A helpful commit message\n\n{TRAILER}\n"),
            (b"A\nhelpful\ncommit\n message\n", f"A\nhelpful\ncommit\n message\n\n{TRAILER}\n"),
        ],
    )
    async def test_run_adds_signed_off_by_trailer_in_its_own_paragraph(self, tmp_path, message, expected):
        result, new_message = await run_on_message(tmp_path, message)

        assert result.success is True
        assert new_message == expected

    async def test_run_keeps_other_sign_offs(self, tmp_path):
        result, new_message = await run_on_message(
            tmp_path, b"A helpful commit message\n\nSigned-off-by: Jane Doe <jane@example.com>\n"
        )

        assert result.success is True
        assert new_message == f"A helpful commit message\n\nSigned-off-by: Jane Doe <jane@example.com>\n{TRAILER}\n"

    async def test_run_keeps_body_lines_that_start_with_signed_off_by(self, tmp_path):
        result, new_message = await run_on_message(tmp_path, b"Fix\n\nSigned-off-by trailers are now checked in CI.\n")

        assert result.success is True
        assert new_message == f"Fix\n\nSigned-off-by trailers are now checked in CI.\n\n{TRAILER}\n"

    async def test_run_adds_trailer_to_an_existing_trailer_block(self, tmp_path):
        result, new_message = await run_on_message(tmp_path, b"Fix\n\nBody.\n\nCo-authored-by: Bob <bob@example.com>\n")

        assert result.success is True
        assert new_message == f"Fix\n\nBody.\n\nCo-authored-by: Bob <bob@example.com>\n{TRAILER}\n"

    @pytest.mark.parametrize(
        "message",
        [
            b"A helpful commit message",
            b"A helpful commit message\n\nSigned-off-by: Jane Doe <jane@example.com>\n",
            b"Fix\n\nBody.\n\nCo-authored-by: Bob <bob@example.com>\n",
        ],
    )
    async def test_run_twice_adds_the_trailer_once(self, tmp_path, message):
        commit_msg = write_commit_msg(tmp_path, message)
        await ValidateSecurityScan(paths=[str(commit_msg)]).run()
        message_after_one_run = commit_msg.read_text()

        result = await ValidateSecurityScan(paths=[str(commit_msg)]).run()

        assert result.success is True
        assert commit_msg.read_text() == message_after_one_run

    async def test_run_with_a_divider_line_adds_trailer_above_it(self, tmp_path):
        result, new_message = await run_on_message(tmp_path, b"Fix\n\nBody\n\n---\n\nNotes\n")

        assert result.success is True
        assert new_message == f"Fix\n\nBody\n\n{TRAILER}\n\n---\n\nNotes\n"

    async def test_run_with_a_trailer_line_in_the_subject_paragraph_adds_a_trailer_the_pr_check_finds(self, tmp_path):
        # The previous version of this hook could write this, and git doesn't read the line as a trailer
        result, new_message = await run_on_message(tmp_path, f"A helpful commit message\n{TRAILER}\n".encode())

        assert result.success is True
        assert new_message == f"A helpful commit message\n{TRAILER}\n\n{TRAILER}\n"

    async def test_run_ignores_trailer_settings_in_git_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
        monkeypatch.setenv("GIT_CONFIG_KEY_0", "trailer.ifmissing")
        monkeypatch.setenv("GIT_CONFIG_VALUE_0", "doNothing")

        result, new_message = await run_on_message(
            tmp_path, b"A helpful commit message\n\nSigned-off-by: Jane Doe <jane@example.com>\n"
        )

        assert result.success is True
        assert new_message == f"A helpful commit message\n\nSigned-off-by: Jane Doe <jane@example.com>\n{TRAILER}\n"

    async def test_run_with_commit_verbose_adds_trailer_above_the_scissors_line(self, tmp_path):
        result, new_message = await run_on_message(
            tmp_path,
            b"A helpful commit message\n"
            b"# ------------------------ >8 ------------------------\n"
            b"# Do not modify or remove the line above.\n"
            b"# Everything below it will be ignored.\n",
        )

        assert result.success is True
        assert new_message == (
            f"A helpful commit message\n\n{TRAILER}\n"
            "# ------------------------ >8 ------------------------\n"
            "# Do not modify or remove the line above.\n"
            "# Everything below it will be ignored.\n"
        )

    async def test_run_with_commit_verbose_and_custom_comment_character_adds_trailer_above_the_scissors_line(self, tmp_path):
        # No git config sets the comment character (like the hook's container)
        commit_msg = write_commit_msg(
            tmp_path,
            b"Fix\n\n"
            b"; ------------------------ >8 ------------------------\n"
            b"; Do not modify or remove the line above.\n"
            b"diff --git a/f b/f\n",
        )

        result = await ValidateSecurityScan(paths=[str(commit_msg)]).run()

        assert result.success is True
        assert commit_msg.read_text() == (
            f"Fix\n\n{TRAILER}\n\n"
            "; ------------------------ >8 ------------------------\n"
            "; Do not modify or remove the line above.\n"
            "diff --git a/f b/f\n"
        )

    async def test_run_when_git_fails_returns_error_code(self, tmp_path):
        failed_git = MagicMock(returncode=128, stderr=b"fatal: something went wrong")
        with patch("src.hooks.validate_security_scan.run_process", return_value=failed_git):
            result, _ = await run_on_message(tmp_path, b"A helpful commit message\n")

        assert result.success is False
        assert "fatal: something went wrong" in result.message
