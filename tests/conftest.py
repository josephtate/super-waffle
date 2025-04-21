# tests/conftest.py
import sys
from pathlib import Path
import pytest
import shutil


@pytest.fixture
def dnf_vars_dir(tmp_path, monkeypatch):
    """Fixture to mock DNF_VARS_DIR to use a temp directory."""
    dnf_path = tmp_path / "dnf" / "vars"
    dnf_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("rlc_cloud_repos.main.DNF_VARS_DIR", dnf_path)
    return dnf_path


@pytest.fixture
def marker(tmp_path, monkeypatch):
    """Fixture to mock MARKERFILE to use a temp file."""
    marker_path = tmp_path / ".configured"
    monkeypatch.setattr("rlc_cloud_repos.main.MARKERFILE", str(marker_path))
    yield marker_path


@pytest.fixture
def mirrors_file(tmp_path, monkeypatch):
    """Fixture to create a temporary mirrors file."""
    mirrors_path = tmp_path / "mirrors.yaml"

    # Copy the content from fixtures/mock-mirrors.yaml to mirrors.yaml
    source_path = Path(__file__).parent / 'fixtures/mock-mirrors.yaml'
    shutil.copy(source_path, mirrors_path)

    monkeypatch.setattr("rlc_cloud_repos.main.DEFAULT_MIRROR_PATH",
                        mirrors_path)
    yield mirrors_path


# Add the src/ directory to the import path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
