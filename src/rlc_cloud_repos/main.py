#!env python
"""
RLC Cloud Repo Resolver CLI

This tool detects the cloud provider and region via cloud-init,
selects the appropriate CIQ repository mirror, and writes DNF vars
for optimized regional repo access.
"""

import argparse
import os
import sys
import pytest
from datetime import datetime

from rlc_cloud_repos.cloud_metadata import get_cloud_metadata
from rlc_cloud_repos.dnf_vars import ensure_all_dnf_vars
from rlc_cloud_repos.log_utils import log_and_print, logger, setup_logging
from rlc_cloud_repos.repo_config import (
    DEFAULT_MIRROR_PATH,
    MARKERFILE,
    load_mirror_map,
    select_mirror,
)


def check_touchfile() -> bool:
    """
    Check if the system has already been configured.
    Returns True if marker file exists, indicating configuration should be skipped.

    Returns:
        bool: True if marker file exists, False otherwise
    """
    if os.path.exists(MARKERFILE):
        log_and_print(
            f"Marker file exists ({MARKERFILE}). Skipping repo update.")
        return True
    return False


def write_touchfile() -> None:
    """
    Create a touchfile to indicate configuration was completed.
    Prevents automatic reruns on reboot (cloud-init idempotency).
    """
    os.makedirs(os.path.dirname(MARKERFILE), exist_ok=True)
    with open(MARKERFILE, "w") as f:
        f.write(f"Configured on {datetime.now().isoformat()}\n")


def _configure_repos(mirror_file_path: str) -> None:
    """
    Core logic for detecting metadata, selecting mirrors, and configuring DNF vars.
    """
    # Detect provider + region via cloud-init query
    metadata = get_cloud_metadata()
    provider = metadata["provider"]
    region = metadata["region"]
    log_and_print(
        f"Using cloud metadata: provider={provider}, region={region}")

    # Load mirror map + resolve appropriate URL
    mirror_map = load_mirror_map(mirror_file_path)
    log_and_print(f"Loaded mirror map from {mirror_file_path}")

    primary_url, backup_url = select_mirror(
        {
            "provider": provider,
            "region": region
        }, mirror_map)
    log_and_print(f"Selected mirror URL: {primary_url}")

    # Set DNF vars
    ensure_all_dnf_vars(primary_url, backup_url)
    logger.info("DNF vars set for mirror=%s and backup=%s", primary_url,
                backup_url)

    # Create marker file to prevent future reruns
    write_touchfile()
    log_and_print(f"Marker file written to {MARKERFILE}")


def parse_args(args=None):
    """
    Parse command line arguments

    Args:
        args: Command line arguments (defaults to None, which uses sys.argv[1:])

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="RLC Cloud Repo Resolver",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--mirror-file",
                        help="Override path to mirror map YAML")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reconfiguration (ignore marker file)",
    )
    return parser.parse_args(args)


def main(args=None) -> int:
    """
    Entry point for RLC cloud repo resolver. Handles argument parsing and
    calls the core configuration logic.

    Args:
        args: Command line arguments (defaults to None, which uses sys.argv[1:])

    Returns:
        int: 0 for success, 1 for failure
    """
    setup_logging()

    parsed_args = parse_args(args)

    if not parsed_args.force:
        if check_touchfile():  # Skip configuration if marker file exists
            return 0

    mirror_path = parsed_args.mirror_file or DEFAULT_MIRROR_PATH
    try:
        _configure_repos(mirror_path)
        return 0
    except Exception as e:
        logger.error("Configuration failed: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))  # pragma: no cover.git
    .pytest_cache
    .vscode
    attached_assets
    rpm
    src
    rlc_cloud_repos
    __pycache__
    cloud-config
    20_rlc-cloud-repos.cfg
    data
    ciq-mirrors.yaml
    framework
    __pycache__
    __init__.py
    azure_mirrors.py
    __init__.py
    cloud_metadata.py
    dnf_vars.py
    log_utils.py
    main.py
    repo_config.py
    tests
    __pycache__
    fixtures
    azure.metadata.yaml
    mock-mirrors.yaml
    framework
    __pycache__
    test_azure_mirrors.py
    metadata
    __pycache__
    test_cloud_metadata_suite.py
    conftest.py
    test_main.py
    .coverage
    .envrc
    .gitignore
    .packit.yaml
    Jenkinsfile
    LICENSE
    Makefile
    Manifest.in
    new-ciq-mirrors.yaml
    README.md
    setup.cfg
    setup.py
    Packager files
    .pythonlibs
    .upm
    store.json
    pyproject.toml
    uv.lock
    Config files
    .replit
    run = "pytest --cov --cov-report term-missing"
    modules = ["python-3.8"]
    [nix]
    channel = "stable-24_05"
    packages = ["libyaml", "ack"]

    [workflows]
    runButton = "Run Tests with coverage"

    [[workflows.workflow]]
    name = "Run Tests with coverage"
    mode = "sequential"
    author = 4915123

    [[workflows.workflow.tasks]]
    task = "shell.exec"
    args = "pytest --cov --cov-report term-missing"

    # tests/conftest.py
    import sys
    from pathlib import Path

    import pytest


    @pytest.fixture(autouse=True)
    def mock_get_cloud_metadata(monkeypatch, request):
        if "test_cloud_metadata_suite" not in request.node.nodeid:
            monkeypatch.setattr(
                "rlc_cloud_repos.cloud_metadata.get_cloud_metadata",
                lambda: {"provider": "mock", "region": "mock-region"},
            )


    # Add the src/ directory to the import path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

    [metadata]
    name = rlc-cloud-repos
    version = attr: rlc_cloud_repos.__version__
    description = A cloud-init querying and repository configuration tool for Rocky Linux from CIQ Products (RLC)
    long_description = file: README.md
    author = CIQ Linux Engineering <support@ciq.com>
    license = MIT

    [options]
    packages = find:
    package_dir = src
    python_requires = >=3.6,<3.14
    include_package_data = true
    install_requires =
        PyYAML

    [options.package_data]
    rlc_cloud_repos =
        data/ciq-mirrors.yaml
        cloud-config/20_rlc-cloud-repos.cfg

    [options.packages.find]
    where = src
    include =
        rlc_cloud_repos
        rlc_cloud_repos.*
    exclude =
        rlc_cloud_repos.framework
        rlc_cloud_repos.framework.*

    [options.entry_points]
    console_scripts =
        rlc-cloud-repos = rlc_cloud_repos.main:main

    [options.extras_require]
    dev =
        pytest>=7.0.0
        pytest-cov>=4.0.0
        flake8
        isort
        black
        mypy
        build>=0.10.0
        setuptools>=40.6.0

    framework =
        configargparse>=1.5.3

    [tool:black]
    line-length = 120

    [tool:isort]
    # Directories to be sorted by isort
    src_paths = src, tests
    skip = ./.cache,
    py_version = 36
    Remote Updates
    origin/jtate-ai-test•upstreamlast fetched 18 min ago
    1 commit to push
    Commit
    There are no changes to commit.
    822ms • 2 minutes ago
    Chats
    Archived
    code coverage report analysis
    1 hour ago
    code coverage project python testing
    2 hours ago
    Shell Execution Process Completed
    2 hours ago
    Refactor main function and add tests
    2 hours ago
    python script refactoring for unit testing
    2 hours ago
    Code Repo Type Annotation Fixes
    2 hours ago
    pytest command line argument error
    2 hours ago
    python project dependency pytest module missing
    11 hours ago
    Azure Mirrors Unit Tests and Project Setup
    11 hours ago

    Running the code in my project results in the following:

    s/dnf_vars.py                     24      4    83%   50-51, 60-61
    src/rlc_cloud_repos/framework/__init__.py            0      0   100%
    src/rlc_cloud_repos/framework/azure_mirrors.py      68     28    59%   11-15, 85, 135-178, 190-218, 222
    src/rlc_cloud_repos/log_utils.py                    21     10    52%   25-30, 46-49
    src/rlc_cloud_repos/main.py                         50     16    68%   42-44, 53-76, 125, 132
    src/rlc_cloud_repos/repo_config.py                  43     11    74%   36-37, 42-44, 69, 71, 76-80
    tests/conftest.py                                    3      0   100%
    tests/test_azure_mirrors.py                         47      0   100%
    tests/test_cloud_metadata_suite.py                  63      1    98%   45
    tests/test_main.py                                  60      3    95%   53, 81-82
    ------------------------------------------------------------------------------
    TOTAL                                              394     75    81%

    ============================= short test summary info =============================
    FAILED tests/test_main.py::test_main_with_force_flag - assert 1 == 0
    FAILED tests/test_main.py::test_main_creates_marker_file - assert 1 == 0
    FAILED tests/test_main.py::test_main_with_custom_mirror_file - assert 1 == 0
    FAILED tests/test_main.py::test_configure_repos_writes_touchfile - FileNotFoundError: [Errno 2] No such file or directory: 'cloud-init'
    ========================== 4 failed, 19 passed in 0.52s ===========================

    If applicable, propose a fix immediately.
    JS
    JosephSS
    Assistant1 hour ago

    The test results indicate that there are several test failures in

    . Specifically, the failures include:

        Assertion errors where the expected result does not match the actual result.
        A FileNotFoundError indicating that the file cloud-init could not be found during the execution of one of the tests.

    To address these issues, you can:

        Check Assertions: Review the tests test_main_with_force_flag, test_main_creates_marker_file, and test_main_with_custom_mirror_file to ensure that the logic is correct and that the expected results match the actual output generated by your code.

        Resolve FileNotFoundError: Make sure that the file cloud-init is correctly created or exists in the expected directory before running the tests. You may need to add a setup step in your test that prepares the environment or creates any necessary files.

    Here is an example of how you might modify one of the tests to ensure the cloud-init file is created before running the test:

    import os
    import pytest

    @pytest.fixture(autouse=True)
    def create_files():
        # Setup: Create necessary files for testing
        if not os.path.exists('cloud-init'):
            with open('cloud-init', 'w') as f:
                f.write('')  # Create an empty file or populate it with necessary content

        yield  # This will run the test

        # Teardown: Clean up if necessary
        if os.path.exists('cloud-init'):
            os.remove('cloud-init')

    def test_main_creates_marker_file():
        # Your existing test code...
        assert some_function() == expected_value

    Make sure to adapt the setup to fit the requirements of your tests. After making these changes, re-run your tests to verify if the issues have been resolved.

    I need a fixture that mocks "get_cloud_metadata" in @src/rlc_cloud_repos/cloud_metadata.pyfor the whole test suite except when running the @tests/test_cloud_metadata_suite.py tests.
    JS
    JosephSS
    Assistant1 hour ago

    To create a fixture that mocks the get_cloud_metadata function in
    for the whole test suite except the tests in

    , you can use pytest's fixture mechanism with a conditional check.

    Here's how you can set up a fixture in

    to achieve this:

    # tests/conftest.py
    import pytest
    from unittest.mock import patch

    @pytest.fixture(autouse=True)
    def mock_get_cloud_metadata(request):
        if "test_cloud_metadata_suite" not in request.node.nodeid:
            with patch("rlc_cloud_repos.cloud_metadata.get_cloud_metadata", return_value={"provider": "mock", "region": "mock-region"}):
                yield

    Insert this code into
    to mock the get_cloud_metadata function in the entire test suite by default, except when

    is running.

    I'll make the proposed change to your

    :
    tests/conftest.py
    Checkpoint made
    Add pytest fixture to mock get_cloud_metadata
    1 hour ago
    •

    you imported unittest.mock again instead of using pytest monkeypatch
    JS
    JosephSS
    Assistant1 hour ago

    You are correct. The use of
    can be replaced with pytest's monkeypatch to improve consistency by using the same mocking approach. Here's how you can update the

    to use pytest monkeypatch:

    # tests/conftest.py
    import sys
    from pathlib import Path
    import pytest

    @pytest.fixture(autouse=True)
    def mock_get_cloud_metadata(monkeypatch, request):
        if "test_cloud_metadata_suite" not in request.node.nodeid:
            monkeypatch.setattr("rlc_cloud_repos.cloud_metadata.get_cloud_metadata", lambda: {"provider": "mock", "region": "mock-region"})

    # Add the src/ directory to the import path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

    This update uses pytest's monkeypatch fixture to mock the get_cloud_metadata function. Let me know if you need further assistance.

    How do I invoke isort so that it reads @setup.cfg?
    JS
    JosephSS
    Assistant56 minutes ago

    To invoke isort so that it reads settings from
    , you simply need to run the isort command from the terminal in your project's root directory. isort will automatically detect and read configuration settings from your

    file. Here’s the command you can use:

    isort .

    This command will sort the imports for all Python files within the current directory and its subdirectories, using the configuration specified in your

    .

    Yeah, but isort is trying to run in .pythonlibs
    JS
    JosephSS
    Assistant56 minutes ago

    To prevent isort from running in
    or any other unwanted directories, you need to configure the

    file to explicitly exclude these directories.

    Here's how you can modify your existing
    to exclude

    :

    [tool:isort]
    # Directories to be sorted by isort
    src_paths = src, tests
    # Exclude specific directories
    skip = .pythonlibs

    Ensure that the skip option under [tool:isort] includes
    . Now, isort will ignore the

    directory when it runs.

    If the
    already contains [tool:isort], you can add the skip line directly under it. After updating the configuration, you should be able to run isort . without it attempting to process files in

    .

    Can't I give isort a whitelist of paths to search instead of skpping venv and cache dirs?
    JS
    JosephSS
    Assistant49 minutes ago

    Yes, instead of specifying directories to skip, you can provide isort a whitelist of paths to specifically include using the src_paths option in your

    . That way, isort will only process the directories you specify. Here's how you can set it:

    [tool:isort]
    # Directories to be explicitly sorted by isort
    src_paths = src, tests, specific_folder_to_include

    Replace specific_folder_to_include with any additional directories you want isort to process. This setup will ensure that isort only looks at the directories you have explicitly listed in src_paths.

    No. That's not what src_paths does. src_paths tells isort what imports are first party, vs stdlib and 3rd party.
    JS
    JosephSS
    Assistant48 minutes ago

    I apologize for the oversight. You're right, src_paths in isort configuration designates which imports should be considered first-party.

    To specify paths for isort to process, without scanning directories like

    , you should directly run isort with the paths you want it to process. For example:

    isort src tests

    This command will only sort imports within the src and tests directories, avoiding unintended directories. Meanwhile, ensure your

    correctly identifies first-party imports if needed.

    Can I get isort to read .gitignores? or only work on files tracked by git?
    JS
    JosephSS
    Assistant46 minutes ago

    isort itself does not directly support reading

    files or restricting its operation to files tracked by Git. However, you can achieve this behavior by integrating isort with Git commands.

    To ensure isort only works on files tracked by Git, you can use the following command to list tracked Python files and then pass them to isort:

    # List all Python files tracked by Git and pass them to isort
    git ls-files '*.py' | xargs isort

    This command uses git ls-files to output tracked files matching the '*.py' pattern, and then xargs to pass these files to isort.

    This approach ensures that isort only processes files tracked by your Git repository, effectively respecting your

    settings indirectly.

    My fixture isn't applying to tests in @tests/test_main.py
    JS
    JosephSS
    Assistantjust now

    Looking at the test failures, the issue is that the mock_get_cloud_metadata fixture in
    isn't mocking the actual subprocess call that's failing in

    . Instead of mocking just the function, we should mock the subprocess call itself.

    Let's update the fixture:
    tests/conftest.py
    Update fixtu
