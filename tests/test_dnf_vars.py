import pytest

from rlc.cloud_repos.dnf_vars import BACKUP_SUFFIX, _write_dnf_var, ensure_all_dnf_vars


@pytest.fixture
def dnf_dir(tmp_path):
    """Create a temporary DNF vars directory"""
    vars_dir = tmp_path / "dnf" / "vars"
    vars_dir.mkdir(parents=True)
    yield vars_dir


def test_write_dnf_var_new_file(dnf_dir):
    """Test writing a DNF var to a new file"""
    _write_dnf_var(dnf_dir, "test", "value")
    path = dnf_dir / "test"
    assert path.exists()
    assert path.read_text().strip() == "value"


def test_write_dnf_var_existing_same_value(dnf_dir):
    """Test writing a DNF var when file exists with same value"""
    path = dnf_dir / "test"
    path.write_text("value\n")

    _write_dnf_var(dnf_dir, "test", "value")
    assert path.exists()
    assert not (path.parent / f"test{BACKUP_SUFFIX}").exists()
    assert path.read_text().strip() == "value"


def test_write_dnf_var_existing_different_value(dnf_dir):
    """Test writing a DNF var when file exists with different value"""
    path = dnf_dir / "test"
    path.write_text("old_value\n")

    _write_dnf_var(dnf_dir, "test", "new_value")
    assert path.exists()
    assert (path.parent / f"test{BACKUP_SUFFIX}").exists()
    assert path.read_text().strip() == "new_value"
    assert (path.parent / f"test{BACKUP_SUFFIX}").read_text().strip() == "old_value"


def test_ensure_all_dnf_vars(dnf_dir):
    """Test ensuring all DNF vars are set"""
    primary = "https://primary.mirror"
    backup = "https://backup.mirror"

    ensure_all_dnf_vars(dnf_dir, primary, backup)

    assert (dnf_dir / "baseurl1").read_text().strip() == primary
    assert (dnf_dir / "baseurl2").read_text().strip() == backup


def test_ensure_all_dnf_vars_idempotent(dnf_dir):
    """Test ensuring all DNF vars doesn't create backups if values unchanged"""
    primary = "https://primary.mirror"
    backup = "https://backup.mirror"

    # First call
    ensure_all_dnf_vars(dnf_dir, primary, backup)
    # Second call
    ensure_all_dnf_vars(dnf_dir, primary, backup)

    assert not (dnf_dir / f"baseurl1{BACKUP_SUFFIX}").exists()
    assert not (dnf_dir / f"baseurl2{BACKUP_SUFFIX}").exists()


def test_ensure_all_dnf_vars_changes(dnf_dir):
    """Test ensuring all DNF vars creates backups when values change"""
    # First call
    ensure_all_dnf_vars(dnf_dir, "old_primary", "old_backup")
    # Second call with different values
    ensure_all_dnf_vars(dnf_dir, "new_primary", "new_backup")

    assert (dnf_dir / f"baseurl1{BACKUP_SUFFIX}").exists()
    assert (dnf_dir / f"baseurl2{BACKUP_SUFFIX}").exists()
    assert (dnf_dir / f"baseurl1{BACKUP_SUFFIX}").read_text().strip() == "old_primary"
    assert (dnf_dir / f"baseurl2{BACKUP_SUFFIX}").read_text().strip() == "old_backup"


def test_write_dnf_var_non_writable_dir_non_existent_file(dnf_dir, caplog):
    """Test writing DNF var to a non-writable directory."""
    # Make directory read-only
    dnf_dir.chmod(0o555)

    _write_dnf_var(dnf_dir, "test", "value")

    # Verify error was logged
    assert "Cannot write to DNF var 'test'" in caplog.text
    assert "Permission denied" in caplog.text

    # Restore permissions for cleanup
    dnf_dir.chmod(0o755)


def test_write_dnf_var_non_writable_dir_pre_existing_file(dnf_dir, caplog):
    """Test writing DNF var to a non-writable directory."""
    # Make directory read-only
    _write_dnf_var(dnf_dir, "test", "pre-value")
    dnf_dir.chmod(0o555)

    _write_dnf_var(dnf_dir, "test", "value")

    # Verify error was logged
    assert "Cannot backup DNF var 'test'" in caplog.text
    assert "Permission denied" in caplog.text

    # Restore permissions for cleanup
    dnf_dir.chmod(0o755)
