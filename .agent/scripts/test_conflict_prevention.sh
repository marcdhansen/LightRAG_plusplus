#!/bin/bash
# Automated conflict prevention testing framework
# Fail-fast strategy - any test failure stops implementation

set -e  # Exit immediately if any command fails

echo "🧪 Starting Conflict Prevention Test Suite"
echo "================================================"

# Test configuration
TEST_AGENT_1="test-agent-1"
TEST_AGENT_2="test-agent-2"
TEST_TASK_1="test-conflict-1"
TEST_TASK_2="test-conflict-2"
TEST_TASK_3="test-stress-"

# Cleanup function
cleanup_test() {
    echo ""
    echo "🧹 Cleaning up test environment..."

    # End all test sessions
    for agent in $TEST_AGENT_1 $TEST_AGENT_2; do
        for task in $TEST_TASK_1 $TEST_TASK_2; do
            ./.agent/scripts/enhanced_session_locks.sh "$task" "$agent" "cleanup" 2>/dev/null || true
        done
    done

    # Clean up any remaining test locks
    rm -f .agent/session_locks/task_test-*.lock
    rm -f .agent/session_locks/session_test-*.json
    rm -f .agent/session_locks/resources_test-*.json

    # Remove test worktrees
    rm -rf worktrees/test-*

    echo "✅ Test cleanup completed"
}

# Trap to ensure cleanup runs on exit
trap cleanup_test EXIT

# Test 1: Single Agent Baseline
test_single_agent() {
    echo ""
    echo "🔍 Test 1: Single Agent Baseline"
    echo "--------------------------------"

    local start_time=$(date +%s)

    # Test task exclusivity
    if ! ./.agent/scripts/validate_task_exclusivity.sh "$TEST_TASK_1" "$TEST_AGENT_1" "check"; then
        echo "❌ FAIL: Task exclusivity check failed"
        exit 1
    fi

    if ! ./.agent/scripts/validate_task_exclusivity.sh "$TEST_TASK_1" "$TEST_AGENT_1" "claim"; then
        echo "❌ FAIL: Task claim failed"
        exit 1
    fi

    # Test resource allocation
    if ! ./.agent/scripts/allocate_safe_resources.sh "$TEST_TASK_1" "$TEST_AGENT_1"; then
        echo "❌ FAIL: Resource allocation failed"
        exit 1
    fi

    # Test session management
    if ! ./.agent/scripts/enhanced_session_locks.sh "$TEST_TASK_1" "$TEST_AGENT_1" "start"; then
        echo "❌ FAIL: Session start failed"
        exit 1
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo "✅ PASS: Single agent baseline completed in ${duration}s"

    # Check performance target (< 30 seconds)
    if [ $duration -gt 30 ]; then
        echo "⚠️  WARNING: Setup time > 30s (actual: ${duration}s)"
    fi

    # Clean up test 1 before proceeding
    ./.agent/scripts/validate_task_exclusivity.sh "$TEST_TASK_1" "$TEST_AGENT_1" "release"

    return 0
}

# Test 2: Dual Agent Conflict Detection
test_dual_agent_conflicts() {
    echo ""
    echo "🔍 Test 2: Dual Agent Conflict Detection"
    echo "-------------------------------------"

    # Agent 1 claims task
    if ! ./.agent/scripts/validate_task_exclusivity.sh "$TEST_TASK_1" "$TEST_AGENT_1" "claim"; then
        echo "❌ FAIL: Agent 1 task claim failed"
        exit 1
    fi

    # Agent 2 tries to claim same task (should fail)
    if ./.agent/scripts/validate_task_exclusivity.sh "$TEST_TASK_1" "$TEST_AGENT_2" "check" 2>/dev/null; then
        echo "❌ FAIL: Agent 2 should not be able to claim task $TEST_TASK_1"
        exit 1
    fi

    if ./.agent/scripts/validate_task_exclusivity.sh "$TEST_TASK_1" "$TEST_AGENT_2" "claim" 2>/dev/null; then
        echo "❌ FAIL: Agent 2 successfully claimed already-locked task $TEST_TASK_1"
        exit 1
    else
        echo "✅ PASS: Agent 2 correctly blocked from claiming task $TEST_TASK_1"
    fi

    # Release task for next tests
    ./.agent/scripts/validate_task_exclusivity.sh "$TEST_TASK_1" "$TEST_AGENT_1" "release"

    return 0
}

# Test 3: Multi-Agent Stress Testing
test_multi_agent_stress() {
    echo ""
    echo "🔍 Test 3: Multi-Agent Stress Testing"
    echo "------------------------------------"

    local success_count=0
    local total_agents=3

    # Try to allocate resources for 3 agents with different tasks
    for i in 1 2 3; do
        local task="${TEST_TASK_3}${i}"
        if ./.agent/scripts/allocate_safe_resources.sh "$task" "test-agent-$i"; then
            success_count=$((success_count + 1))
            echo "✅ Agent $i: Resource allocation successful"
        else
            echo "❌ Agent $i: Resource allocation failed"
            exit 1
        fi
    done

    echo "✅ PASS: $success_count/$total_agents agents successfully allocated resources"

    if [ $success_count -eq $total_agents ]; then
        echo "✅ PASS: Multi-agent stress test completed successfully"
    else
        echo "❌ FAIL: Not all agents could be allocated resources"
        exit 1
    fi

    return 0
}

# Test 4: Crash Recovery
test_crash_recovery() {
    echo ""
    echo "🔍 Test 4: Crash Recovery"
    echo "--------------------------"

    # Start a session
    if ! ./.agent/scripts/enhanced_session_locks.sh "$TEST_TASK_2" "$TEST_AGENT_1" "start"; then
        echo "❌ FAIL: Cannot start crash recovery test session"
        exit 1
    fi

    # Simulate crash by just ending session abruptly
    if ! ./.agent/scripts/enhanced_session_locks.sh "$TEST_TASK_2" "$TEST_AGENT_1" "end"; then
        echo "❌ FAIL: Cannot end session for crash recovery test"
        exit 1
    fi

    # Try to claim same task again (should succeed after cleanup)
    if ! ./.agent/scripts/validate_task_exclusivity.sh "$TEST_TASK_2" "$TEST_AGENT_2" "claim"; then
        echo "❌ FAIL: Cannot re-claim task after crash recovery"
        exit 1
    fi

    echo "✅ PASS: Crash recovery test completed successfully"
    return 0
}

# Test 5: Branch Naming Enforcement
test_branch_naming() {
    echo ""
    echo "🔍 Test 5: Branch Naming Enforcement"
    echo "-----------------------------------"

    # Test invalid branch names
    local invalid_branches=(
        "main"
        "feature/test"
        "agent/task-test1"
        "agent/agent1/test-task1"  # wrong format
        "agent/agent1/task"         # missing task id
    )

    for branch in "${invalid_branches[@]}"; do
        if ./.agent/scripts/enforce_branch_naming.sh "$branch" "test-agent" "test-task" 2>/dev/null; then
            echo "❌ FAIL: Invalid branch name '$branch' was accepted"
            exit 1
        else
            echo "✅ PASS: Invalid branch name '$branch' correctly rejected"
        fi
    done

    # Test valid branch name
    if ! ./.agent/scripts/enforce_branch_naming.sh "agent/test-agent/task-test1" "test-agent" "test-test1"; then
        echo "❌ FAIL: Valid branch name was rejected"
        exit 1
    else
        echo "✅ PASS: Valid branch name correctly accepted"
    fi

    return 0
}

# Test 6: Git Hooks Integration
test_git_hooks() {
    echo ""
    echo "🔍 Test 6: Git Hooks Integration"
    echo "--------------------------------"

    # Create a test branch with proper naming
    git checkout -b agent/test-agent/test-git-hooks 2>/dev/null || git checkout -b agent/test-agent/test-git-hooks

    # Create a test file
    echo "test content" > test_file.txt

    # Try to commit (should work if task is locked)
    if ./.agent/scripts/validate_task_exclusivity.sh "test-git-hooks" "test-agent" "claim"; then
        git add test_file.txt

        if ! git commit -m "test: test-git-hooks - add test file"; then
            echo "❌ FAIL: Git commit failed unexpectedly"
            exit 1
        else
            echo "✅ PASS: Git commit with proper setup succeeded"
        fi
    else
        echo "❌ FAIL: Cannot lock task for git hook test"
        exit 1
    fi

    # Cleanup
    git checkout main 2>/dev/null || git checkout master 2>/dev/null
    git branch -D agent/test-agent/test-git-hooks
    rm -f test_file.txt

    # Release task lock
    ./.agent/scripts/validate_task_exclusivity.sh "test-git-hooks" "test-agent" "release"

    return 0
}

# Run all tests
echo "Starting test suite..."

test_single_agent
test_dual_agent_conflicts
test_multi_agent_stress
test_crash_recovery
test_branch_naming
test_git_hooks

echo ""
echo "================================================"
echo "🎉 ALL TESTS PASSED! Conflict prevention working correctly."
echo "================================================"

exit 0
