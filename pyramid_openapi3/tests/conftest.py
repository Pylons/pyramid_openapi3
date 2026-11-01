"""Shared pytest fixtures."""

from pathlib import Path

import pytest
import typing as t


@pytest.fixture
def write_spec(tmp_path: Path) -> t.Callable[..., str]:
    """Return a function that writes a spec file under tmp_path and returns its path.

    Pass a `name` with a subdirectory (e.g. "split/openapi.yaml") to keep a
    multi-file spec apart from other specs in the same test. Writing the same
    name twice raises FileExistsError instead of replacing the first spec.
    """

    def write(content: bytes, name: str = "openapi.yaml") -> str:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as f:
            f.write(content)
        return str(path)

    return write
