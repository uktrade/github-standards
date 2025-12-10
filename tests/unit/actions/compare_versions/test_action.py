import tempfile
from unittest.mock import patch

from src.actions.compare_versions.action import main_async


async def test_project_version_different_to_hook_versions_returns_error():
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
        patch("src.actions.compare_versions.action.PROJECT_TOML_FILE", toml_tf.name),
        tempfile.NamedTemporaryFile() as hooks_tf,
        patch("src.actions.compare_versions.action.PRE_COMMIT_HOOKS_FILE", hooks_tf.name),
    ):
        toml_tf.write(valid_toml)
        toml_tf.seek(0)

        hooks_tf.write(valid_hooks)
        hooks_tf.seek(0)

        assert await main_async() == 1


async def test_project_version_matching_all_hook_versions_returns_valid_code():
    valid_toml = b"""
        [project]
        version = "v1.0.0"
        """
    valid_hooks = b"""
        -  id: hook-1
           entry: ghcr.io/uktrade/github-standards:v1.0.0
        -  id: hook-2
           entry: ghcr.io/uktrade/github-standards:v1.0.0
        -  id: hook-3-development
           entry: ghcr.io/uktrade/github-standards:development
        """
    with (
        tempfile.NamedTemporaryFile() as toml_tf,
        patch("src.actions.compare_versions.action.PROJECT_TOML_FILE", toml_tf.name),
        tempfile.NamedTemporaryFile() as hooks_tf,
        patch("src.actions.compare_versions.action.PRE_COMMIT_HOOKS_FILE", hooks_tf.name),
    ):
        toml_tf.write(valid_toml)
        toml_tf.seek(0)

        hooks_tf.write(valid_hooks)
        hooks_tf.seek(0)

        assert await main_async() == 0
