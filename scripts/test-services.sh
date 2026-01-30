#!/usr/bin/env zsh

# 🧪 Service Integration Test Suite
# Purpose: Comprehensive testing of Automem and Langfuse integration

set -e  # Exit on any error

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
API_TOKEN="${AUTOMEM_API_TOKEN:-test-token}"
ADMIN_TOKEN="${ADMIN_API_TOKEN:-test-admin-token}"
AUTOMEM_URL="http://localhost:8001"
LANGFUSE_URL="http://localhost:3000"
TEST_RESULTS=()
TEST_NAMES=()

# Utility functions
log_test() {
    local test_name=$1
    local status=$2
    local message=$3

    TEST_NAMES+=("$test_name")
    TEST_RESULTS+=("$status")

    if [[ "$status" == "PASS" ]]; then
        echo -e "  ✅ ${GREEN}$test_name${NC}"
    elif [[ "$status" == "FAIL" ]]; then
        echo -e "  ❌ ${RED}$test_name${NC}"
        [[ -n "$message" ]] && echo -e "     $message"
    else
        echo -e "  ⚠️  ${YELLOW}$test_name${NC}"
        [[ -n "$message" ]] && echo -e "     $message"
    fi
}

# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

test_automem_health() {
    echo -e "\n${BLUE}🧠 Testing Automem Health Checks${NC}"

    # Test basic health endpoint
    local response=$(curl -s --max-time 10 "$AUTOMEM_URL/health" 2>/dev/null)
    if echo "$response" | grep -q '"status":\s*"healthy"'; then
        log_test "Automem Health Endpoint" "PASS"
    else
        log_test "Automem Health Endpoint" "FAIL" "Response: $response"
        return 1
    fi

    # Test service connectivity details
    if echo "$response" | grep -q '"falkordb":\s*"connected"'; then
        log_test "FalkorDB Connectivity" "PASS"
    else
        log_test "FalkorDB Connectivity" "FAIL" "FalkorDB not connected"
    fi

    if echo "$response" | grep -q '"qdrant":\s*"connected"'; then
        log_test "Qdrant Connectivity" "PASS"
    else
        log_test "Qdrant Connectivity" "FAIL" "Qdrant not connected"
    fi

    # Test data synchronization
    if echo "$response" | grep -q '"sync_status":\s*"synced"'; then
        log_test "Data Synchronization" "PASS"
    else
        log_test "Data Synchronization" "WARN" "Sync status: $(echo "$response" | grep -o '"sync_status":"[^"]*"')"
    fi
}

test_langfuse_health() {
    echo -e "\n${BLUE}🔭 Testing Langfuse Health Checks${NC}"

    # Test API health endpoint
    local response=$(curl -s --max-time 10 "$LANGFUSE_URL/api/public/health" 2>/dev/null)
    if echo "$response" | grep -q '"status":\s*"OK"'; then
        log_test "Langfuse Health Endpoint" "PASS"
    else
        log_test "Langfuse Health Endpoint" "FAIL" "Response: $response"
        return 1
    fi

    # Test web UI accessibility
    local web_response=$(curl -s --max-time 5 -I "$LANGFUSE_URL" 2>/dev/null | head -1)
    if echo "$web_response" | grep -q "200 OK"; then
        log_test "Langfuse Web UI Access" "PASS"
    else
        log_test "Langfuse Web UI Access" "FAIL" "HTTP Status: $web_response"
    fi
}

# ============================================================================
# AUTOMEM FUNCTIONALITY TESTS
# ============================================================================

test_automem_memory_operations() {
    echo -e "\n${BLUE}🧠 Testing Automem Memory Operations${NC}"

    # Test memory storage
    local test_content="Integration test memory at $(date '+%Y-%m-%d %H:%M:%S')"
    local store_response=$(curl -s -X POST \
        -H "Authorization: Bearer $API_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"content\": \"$test_content\", \"tags\": [\"integration-test\"]}" \
        "$AUTOMEM_URL/memory" 2>/dev/null)

    if echo "$store_response" | grep -E '"status":\s*"success"'; then
        log_test "Memory Storage" "PASS"

        # Extract memory ID for retrieval test
        local memory_id=$(echo "$store_response" | grep -o '"id":\s*"[^"]*"' | cut -d'"' -f4)

        if [[ -n "$memory_id" ]]; then
            echo -e "    📝 Stored memory ID: $memory_id"

            # Test memory retrieval
            local recall_response=$(curl -s -G \
                -H "Authorization: Bearer $API_TOKEN" \
                -d "query=integration test" \
                "$AUTOMEM_URL/recall" 2>/dev/null)

            if echo "$recall_response" | grep -E '"status":\s*"success"'; then
                if echo "$recall_response" | grep -q "$memory_id"; then
                    log_test "Memory Retrieval" "PASS"
                else
                    log_test "Memory Retrieval" "FAIL" "Stored memory not found in recall"
                fi

                # Test memory update
                local update_response=$(curl -s -X PATCH \
                    -H "Authorization: Bearer $API_TOKEN" \
                    -H "Content-Type: application/json" \
                    -d "{\"content\": \"$test_content [UPDATED]\"}" \
                    "$AUTOMEM_URL/memory/$memory_id" 2>/dev/null)

                if echo "$update_response" | grep -E '"status":\s*"success"'; then
                    log_test "Memory Update" "PASS"
                else
                    log_test "Memory Update" "FAIL" "Update failed"
                fi

                # Test memory deletion (cleanup)
                local delete_response=$(curl -s -X DELETE \
                    -H "Authorization: Bearer $API_TOKEN" \
                    "$AUTOMEM_URL/memory/$memory_id" 2>/dev/null)

                if echo "$delete_response" | grep -E '"status":\s*"success"'; then
                    log_test "Memory Deletion" "PASS"
                else
                    log_test "Memory Deletion" "FAIL" "Cleanup failed"
                fi

            else
                log_test "Memory Retrieval" "FAIL" "Recall request failed"
            fi
        else
            log_test "Memory ID Extraction" "FAIL" "Could not extract memory ID"
        fi
    else
        log_test "Memory Storage" "FAIL" "Storage response: $store_response"
    fi
}

test_automem_authentication() {
    echo -e "\n${BLUE}🔐 Testing Automem Authentication${NC}"

    # Test with valid token
    local valid_response=$(curl -s -H "Authorization: Bearer $API_TOKEN" \
                           -X GET \
                           "$AUTOMEM_URL/memory/by-tag?tags=test" 2>/dev/null)

    if echo "$valid_response" | grep -E '"status":\s*"success"'; then
        log_test "Valid Authentication" "PASS"
    else
        log_test "Valid Authentication" "FAIL" "Valid token rejected"
    fi

    # Test with invalid token
    local invalid_response=$(curl -s -H "Authorization: Bearer invalid-token" \
                             -X GET \
                             "$AUTOMEM_URL/memory/by-tag?tags=test" 2>/dev/null)

    if echo "$invalid_response" | grep -E '"status":\s*"error"'; then
        log_test "Invalid Authentication Rejection" "PASS"
    else
        log_test "Invalid Authentication Rejection" "FAIL" "Invalid token accepted"
    fi

    # Test without token
    local no_token_response=$(curl -s -X GET \
                                "$AUTOMEM_URL/memory/by-tag?tags=test" 2>/dev/null)

    if echo "$no_token_response" | grep -E '"status":\s*"error"'; then
        log_test "Missing Authentication Rejection" "PASS"
    else
        log_test "Missing Authentication Rejection" "FAIL" "Missing token accepted"
    fi
}

# ============================================================================
# LANGFUSE FUNCTIONALITY TESTS
# ============================================================================

test_langfuse_tracing() {
    echo -e "\n${BLUE}📊 Testing Langfuse Tracing${NC}"

    # Create a memory to generate a trace
    local trace_test_content="Langfuse tracing test at $(date '+%Y-%m-%d %H:%M:%S')"
    curl -s -X POST \
        -H "Authorization: Bearer $API_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"content\": \"$trace_test_content\", \"tags\": [\"langfuse-test\"]}" \
        "$AUTOMEM_URL/memory" >/dev/null

    # Wait a moment for trace to be processed
    sleep 3

    # Check if trace appears in Langfuse (basic check - just verify web access)
    local trace_check_response=$(curl -s --max-time 5 \
        -H "Authorization: Bearer sk-lf-lightrag" \
        "$LANGFUSE_URL/api/public/traces?limit=1" 2>/dev/null)

    if [[ -n "$trace_check_response" ]]; then
        log_test "Langfuse Trace API Access" "PASS"
    else
        log_test "Langfuse Trace API Access" "WARN" "Trace API not accessible (may need configuration)"
    fi
}

# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

test_performance_basic() {
    echo -e "\n${BLUE}⚡ Testing Basic Performance${NC}"

    # Test Automem response time
    local start_time=$(date +%s%3N)
    curl -s --max-time 10 "$AUTOMEM_URL/health" >/dev/null
    local end_time=$(date +%s%3N)
    local automem_response_time=$((end_time - start_time))

    if [[ $automem_response_time -lt 1000 ]]; then  # Less than 1 second
        log_test "Automem Response Time" "PASS" "${automem_response_time}ms"
    else
        log_test "Automem Response Time" "WARN" "${automem_response_time}ms (slow)"
    fi

    # Test Langfuse response time
    start_time=$(date +%s%3N)
    curl -s --max-time 10 "$LANGFUSE_URL/api/public/health" >/dev/null
    end_time=$(date +%s%3N)
    local langfuse_response_time=$((end_time - start_time))

    if [[ $langfuse_response_time -lt 2000 ]]; then  # Less than 2 seconds
        log_test "Langfuse Response Time" "PASS" "${langfuse_response_time}ms"
    else
        log_test "Langfuse Response Time" "WARN" "${langfuse_response_time}ms (slow)"
    fi
}

# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

test_error_handling() {
    echo -e "\n${BLUE}🚨 Testing Error Handling${NC}"

    # Test malformed JSON request
    local malformed_response=$(curl -s -X POST \
        -H "Authorization: Bearer $API_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"invalid": json}' \
        "$AUTOMEM_URL/memory" 2>/dev/null)

    if echo "$malformed_response" | grep -E '"status":\s*"error"'; then
        log_test "Malformed JSON Handling" "PASS"
    else
        log_test "Malformed JSON Handling" "FAIL" "Should reject malformed JSON"
    fi

    # Test non-existent memory
    local not_found_response=$(curl -s -X GET \
        -H "Authorization: Bearer $API_TOKEN" \
        "$AUTOMEM_URL/memory/non-existent-id" 2>/dev/null)

    if echo "$not_found_response" | grep -E '"status":\s*"error"'; then
        log_test "Not Found Error Handling" "PASS"
    else
        log_test "Not Found Error Handling" "FAIL" "Should return 404 error"
    fi
}

# ============================================================================
# TEST EXECUTION AND REPORTING
# ============================================================================

run_all_tests() {
    echo -e "${BLUE}🧪 Starting Service Integration Test Suite${NC}\n"

    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    local warning_tests=0

    # Execute all test suites
    test_automem_health
    test_langfuse_health
    test_automem_memory_operations
    test_automem_authentication
    test_langfuse_tracing
    test_performance_basic
    test_error_handling

    # Calculate results
    for ((i=0; i<${#TEST_RESULTS[@]}; i++)); do
        total_tests=$((total_tests + 1))
        case "${TEST_RESULTS[$i]}" in
            "PASS") passed_tests=$((passed_tests + 1)) ;;
            "FAIL") failed_tests=$((failed_tests + 1)) ;;
            "WARN") warning_tests=$((warning_tests + 1)) ;;
        esac
    done

    # Print summary
    echo -e "\n${BLUE}📊 Test Results Summary${NC}"
    echo -e "  Total Tests: $total_tests"
    echo -e "  ${GREEN}✅ Passed: $passed_tests${NC}"
    echo -e "  ${YELLOW}⚠️  Warnings: $warning_tests${NC}"
    echo -e "  ${RED}❌ Failed: $failed_tests${NC}"

    # Detailed results
    echo -e "\n${BLUE}📋 Detailed Results${NC}"
    for ((i=0; i<${#TEST_NAMES[@]}; i++)); do
        local status="${TEST_RESULTS[$i]}"
        local name="${TEST_NAMES[$i]}"

        case "$status" in
            "PASS") echo -e "  ${GREEN}✅ $name${NC}" ;;
            "FAIL") echo -e "  ${RED}❌ $name${NC}" ;;
            "WARN") echo -e "  ${YELLOW}⚠️  $name${NC}" ;;
        esac
    done

    # Return appropriate exit code
    if [[ $failed_tests -eq 0 ]]; then
        echo -e "\n${GREEN}🎉 All critical tests passed!${NC}"
        return 0
    else
        echo -e "\n${RED}🚨 $failed_tests test(s) failed. Check service configuration.${NC}"
        return 1
    fi
}

# Parse command line arguments
case "${1:-all}" in
    "health")
        test_automem_health
        test_langfuse_health
        ;;
    "automem")
        test_automem_health
        test_automem_memory_operations
        test_automem_authentication
        ;;
    "langfuse")
        test_langfuse_health
        test_langfuse_tracing
        ;;
    "performance")
        test_performance_basic
        ;;
    "error")
        test_error_handling
        ;;
    "all"|*)
        run_all_tests
        ;;
esac
