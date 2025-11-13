import tempfile
from unittest.mock import patch

from src.actions.compare_versions import main as main_function


def test_project_version_different_to_hook_versions_returns_error():
    valid_toml = b"""
        [project]
        version = "v1.0.0"
        """
    valid_hooks = b"""
        -  id: hook-1
           entry: ghcr.io/uktrade/github-standards:v1.0.0
        -  id: hook-2
           entry: ghcr.io/uktrade/github-standards:v0.0.9
        """
    with (
        tempfile.NamedTemporaryFile() as toml_tf,
        patch("src.actions.compare_versions.PROJECT_TOML_FILE", toml_tf.name),
        tempfile.NamedTemporaryFile() as hooks_tf,
        patch("src.actions.compare_versions.PRE_COMMIT_HOOKS_FILE", hooks_tf.name),
    ):
        toml_tf.write(valid_toml)
        toml_tf.seek(0)

        hooks_tf.write(valid_hooks)
        hooks_tf.seek(0)

        assert main_function() == 1


def test_project_version_matching_all_hook_versions_returns_valid_code():
    valid_toml = b"""
        [project]
        version = "v1.0.0"
        """
    valid_hooks = b"""
        -  id: hook-1
           entry: ghcr.io/uktrade/github-standards:v1.0.0
        -  id: hook-2
           entry: ghcr.io/uktrade/github-standards:v1.0.0
        """
    with (
        tempfile.NamedTemporaryFile() as toml_tf,
        patch("src.actions.compare_versions.PROJECT_TOML_FILE", toml_tf.name),
        tempfile.NamedTemporaryFile() as hooks_tf,
        patch("src.actions.compare_versions.PRE_COMMIT_HOOKS_FILE", hooks_tf.name),
    ):
        toml_tf.write(valid_toml)
        toml_tf.seek(0)

        hooks_tf.write(valid_hooks)
        hooks_tf.seek(0)

        assert main_function() == 0
