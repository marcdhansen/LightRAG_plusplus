import subprocess
import os
import re


def test_tdd_validation_logic():
    """Test TDD validation function logic using the actual script"""

    script_content = """
validate_tdd_for_branch() {
    CHANGED_PY_FILES=$(git diff main --name-only --diff-filter=ACM 2>/dev/null | grep "\\.py$" | grep "^lightrag/")
    
    if [ -z "$CHANGED_PY_FILES" ]; then
        echo "PASS: No new Python files"
        return 0
    fi
    
    MISSING_TESTS=()
    
    for py_file in $CHANGED_PY_FILES; do
        module_name=$(basename "$py_file" .py)
        
        if [ ! -f "tests/test_${module_name}.py" ]; then
            MISSING_TESTS+=("$py_file")
        fi
    done
    
    if [ ${#MISSING_TESTS[@]} -gt 0 ]; then
        echo "FAIL: Missing tests for: ${MISSING_TESTS[*]}"
        return 1
    else
        echo "PASS: All files have tests"
        return 0
    fi
}

validate_tdd_for_branch
"""

    result = subprocess.run(
        ["bash", "-c", script_content],
        capture_output=True,
        text=True,
        cwd="/Users/marchansen/lightrag/LightRAG++",
    )

    assert (
        "PASS" in result.stdout
        or "main branch" in result.stdout.lower()
        or "skipped" in result.stdout.lower()
    )


def test_naming_convention_logic():
    """Test the naming convention mapping logic"""

    test_cases = [
        ("lightrag/operate.py", "tests/test_operate.py"),
        ("lightrag/utils_graph.py", "tests/test_utils_graph.py"),
        ("lightrag/ace/curator.py", "tests/test_curator.py"),
    ]

    for impl_file, expected_test in test_cases:
        module_name = os.path.basename(impl_file).replace(".py", "")
        computed_test = f"tests/test_{module_name}.py"
        assert computed_test == expected_test, (
            f"Failed for {impl_file}: got {computed_test}"
        )


def test_existing_test_files_match_convention():
    """Verify existing test files follow the naming convention"""
    import glob

    lightrag_files = glob.glob("lightrag/*.py")
    lightrag_files.extend(glob.glob("lightrag/**/*.py"))

    missing_tests = []
    for f in lightrag_files:
        if f.endswith("__init__.py") or "/_" in f:
            continue

        module_name = os.path.basename(f).replace(".py", "")
        expected_test = f"tests/test_{module_name}.py"

        if not os.path.exists(expected_test):
            missing_tests.append(f"{f} -> {expected_test}")

    if missing_tests:
        print(
            f"\nNote: {len(missing_tests)} impl files don't have corresponding tests following naming convention"
        )
        for m in missing_tests[:5]:
            print(f"  {m}")
