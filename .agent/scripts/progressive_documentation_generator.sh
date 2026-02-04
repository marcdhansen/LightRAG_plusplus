#!/bin/bash

# Progressive Documentation Generator
# Creates contextual documentation based on user's current position and workflow state

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$(dirname "$SCRIPT_DIR")/config"
DOCS_DIR="$(dirname "$SCRIPT_DIR")/docs/progressive"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
CONTEXT_TYPE=""
WORKFLOW_STATE=""
USER_POSITION=""
DETAIL_LEVEL="standard"
OUTPUT_FORMAT="markdown"

usage() {
    echo "Usage: $0 --context <type> --workflow <state> --position <user_level> [options]"
    echo ""
    echo "Generates progressive documentation based on user context and needs"
    echo ""
    echo "Required:"
    echo "  --context <type>      Context type (preflight, work, rtb, error, learning)"
    echo "  --workflow <state>    Workflow state (planning, implementing, testing, reviewing)"
    echo "  --position <level>    User level (new, intermediate, advanced, expert)"
    echo ""
    echo "Optional:"
    echo "  --detail <level>      Detail level (minimal, standard, comprehensive)"
    echo "  --format <format>     Output format (markdown, terminal, json)"
    echo "  --output <file>       Output file (default: stdout)"
    echo "  --interactive         Interactive mode with prompts"
    echo ""
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --context)
            CONTEXT_TYPE="$2"
            shift 2
            ;;
        --workflow)
            WORKFLOW_STATE="$2"
            shift 2
            ;;
        --position)
            USER_POSITION="$2"
            shift 2
            ;;
        --detail)
            DETAIL_LEVEL="$2"
            shift 2
            ;;
        --format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --interactive)
            INTERACTIVE=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            usage
            ;;
    esac
done

# Validate required arguments
if [[ -z "$CONTEXT_TYPE" || -z "$WORKFLOW_STATE" || -z "$USER_POSITION" ]]; then
    echo -e "${RED}Error: Missing required arguments${NC}"
    usage
fi

# Interactive mode
if [[ "${INTERACTIVE:-false}" == "true" ]]; then
    echo -e "${BLUE}=== Progressive Documentation Generator ===${NC}"
    echo "Please provide the following information:"
    
    # Context selection
    echo "Available contexts:"
    echo "1) preflight - Before starting work"
    echo "2) work - During active work"
    echo "3) rtb - Return to base/completion"
    echo "4) error - Troubleshooting errors"
    echo "5) learning - Skill development"
    read -p "Select context (1-5): " context_choice
    
    case $context_choice in
        1) CONTEXT_TYPE="preflight" ;;
        2) CONTEXT_TYPE="work" ;;
        3) CONTEXT_TYPE="rtb" ;;
        4) CONTEXT_TYPE="error" ;;
        5) CONTEXT_TYPE="learning" ;;
        *) echo -e "${RED}Invalid choice${NC}"; exit 1 ;;
    esac
    
    # Workflow state
    echo "Available workflow states:"
    echo "1) planning - Planning and preparation"
    echo "2) implementing - Active development"
    echo "3) testing - Testing and validation"
    echo "4) reviewing - Review and refinement"
    read -p "Select workflow state (1-4): " workflow_choice
    
    case $workflow_choice in
        1) WORKFLOW_STATE="planning" ;;
        2) WORKFLOW_STATE="implementing" ;;
        3) WORKFLOW_STATE="testing" ;;
        4) WORKFLOW_STATE="reviewing" ;;
        *) echo -e "${RED}Invalid choice${NC}"; exit 1 ;;
    esac
    
    # User position
    echo "User experience levels:"
    echo "1) new - First time with this workflow"
    echo "2) intermediate - Familiar but needs guidance"
    echo "3) advanced - Experienced with this workflow"
    echo "4) expert - Can teach others"
    read -p "Select your level (1-4): " position_choice
    
    case $position_choice in
        1) USER_POSITION="new" ;;
        2) USER_POSITION="intermediate" ;;
        3) USER_POSITION="advanced" ;;
        4) USER_POSITION="expert" ;;
        *) echo -e "${RED}Invalid choice${NC}"; exit 1 ;;
    esac
fi

# Create docs directory if it doesn't exist
mkdir -p "$DOCS_DIR"

# Function to get current context data
get_context_data() {
    local context_file="$CONFIG_DIR/contexts/${CONTEXT_TYPE}.json"
    if [[ -f "$context_file" ]]; then
        cat "$context_file"
    else
        echo "{}"
    fi
}

# Function to get user position profile
get_user_profile() {
    local profile_file="$CONFIG_DIR/user_profiles/${USER_POSITION}.json"
    if [[ -f "$profile_file" ]]; then
        cat "$profile_file"
    else
        echo "{}"
    fi
}

# Function to adapt content based on detail level
adapt_content_detail() {
    local content="$1"
    local detail="$2"
    
    case "$detail" in
        "minimal")
            # Show only essential steps
            echo "$content" | jq -r '.essential // .'
            ;;
        "standard")
            # Show essential + important details
            echo "$content" | jq -r '.standard // .essential // .'
            ;;
        "comprehensive")
            # Show everything
            echo "$content"
            ;;
        *)
            echo "$content"
            ;;
    esac
}

# Function to format output
format_output() {
    local content="$1"
    local format="$2"
    
    case "$format" in
        "json")
            echo "$content" | jq .
            ;;
        "terminal")
            echo "$content" | jq -r '
                if .title then "# \(.title)\n" else "" end +
                if .description then "\(.description)\n" else "" end +
                if .steps then (.steps | map("- \(.title): \(.description)") | join("\n")) else "" end
            '
            ;;
        "markdown"|*)
            echo "$content" | jq -r '
                if .title then "# \(.title)\n" else "" end +
                if .description then "\(.description)\n\n" else "" end +
                if .prerequisites then "## Prerequisites\n\n" + (.prerequisites | map("- \(. )") | join("\n")) + "\n\n" else "" end +
                if .steps then "## Steps\n\n" + (.steps | to_entries[] | "### \(.value.title | gsub("\\("; ""; gsub("\\)"; ""))\n\n\(.value.description)\n\n```\n\(.value.command)\n```\n\n") else "" end +
                if .notes then "## Notes\n\n\(.notes)\n" else "" end
            '
            ;;
    esac
}

# Function to get workflow-specific content
get_workflow_content() {
    local context="$1"
    local workflow="$2"
    local position="$3"
    
    # Check for context + workflow specific content
    local specific_file="$DOCS_DIR/${context}_${workflow}_${position}.md"
    if [[ -f "$specific_file" ]]; then
        echo "$specific_file"
        return 0
    fi
    
    # Check for context + workflow content
    local context_workflow_file="$DOCS_DIR/${context}_${workflow}.md"
    if [[ -f "$context_workflow_file" ]]; then
        echo "$context_workflow_file"
        return 0
    fi
    
    # Check for context-specific content
    local context_file="$DOCS_DIR/${context}.md"
    if [[ -f "$context_file" ]]; then
        echo "$context_file"
        return 0
    fi
    
    # Return empty if no specific content found
    echo ""
}

# Function to generate dynamic content
generate_dynamic_content() {
    local context="$1"
    local workflow="$2"
    local position="$3"
    
    # Get current git status for context
    local git_status=""
    if command -v git >/dev/null 2>&1 && git rev-parse --git-dir >/dev/null 2>&1; then
        git_status=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    fi
    
    # Get current task context
    local current_task=""
    if [[ -f ".agent/current_task.json" ]]; then
        current_task=$(jq -r '.task // ""' .agent/current_task.json 2>/dev/null || echo "")
    fi
    
    # Generate content based on context
    cat <<EOF
{
  "title": "Progressive Documentation",
  "context": "$context",
  "workflow": "$workflow",
  "user_position": "$position",
  "detail_level": "$DETAIL_LEVEL",
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "environment": {
    "git_changes": "$git_status",
    "current_task": "$current_task",
    "working_directory": "$(pwd)"
  },
EOF

    # Add context-specific content
    case "$context" in
        "preflight")
            cat <<EOF
  "prerequisites": [
    "Run PFC validation",
    "Check resource availability",
    "Verify system state"
  ],
  "steps": [
    {
      "title": "Pre-Flight Check",
      "description": "Validate system and environment readiness",
      "command": "./scripts/preflight_check.sh",
      "critical": true
    }
EOF
            ;;
        "work")
            cat <<EOF
  "prerequisites": [
    "PFC completed successfully",
    "Resources allocated",
    "Session lock acquired"
  ],
  "steps": [
    {
      "title": "Continue Work",
      "description": "Proceed with planned tasks",
      "command": "bd ready",
      "critical": false
    }
EOF
            ;;
        "rtb")
            cat <<EOF
  "prerequisites": [
    "All work completed",
    "Tests passing",
    "Documentation updated"
  ],
  "steps": [
    {
      "title": "Return To Base",
      "description": "Complete session and cleanup",
      "command": "/rtb",
      "critical": true
    }
EOF
            ;;
        "error")
            cat <<EOF
  "prerequisites": [
    "Error identified",
    "Context collected"
  ],
  "steps": [
    {
      "title": "Error Analysis",
      "description": "Analyze and resolve the error",
      "command": "./scripts/error_analyzer.sh --error '$ERROR_INFO'",
      "critical": true
    }
EOF
            ;;
        "learning")
            cat <<EOF
  "prerequisites": [
    "Learning objectives identified",
    "Time allocated for skill development"
  ],
  "steps": [
    {
      "title": "Skill Development",
      "description": "Engage with learning materials",
      "command": "./scripts/learning_path.sh --skill '$TARGET_SKILL'",
      "critical": false
    }
EOF
            ;;
    esac
    
    # Close the JSON structure
    echo "}"
}

# Main execution
main() {
    echo -e "${GREEN}Generating progressive documentation...${NC}"
    echo "Context: $CONTEXT_TYPE"
    echo "Workflow: $WORKFLOW_STATE"
    echo "User Position: $USER_POSITION"
    echo "Detail Level: $DETAIL_LEVEL"
    echo ""
    
    # Try to get existing documentation first
    local doc_file=$(get_workflow_content "$CONTEXT_TYPE" "$WORKFLOW_STATE" "$USER_POSITION")
    
    if [[ -n "$doc_file" && -f "$doc_file" ]]; then
        echo -e "${GREEN}Found existing documentation: $doc_file${NC}"
        content=$(cat "$doc_file")
    else
        echo -e "${YELLOW}Generating dynamic documentation...${NC}"
        content=$(generate_dynamic_content "$CONTEXT_TYPE" "$WORKFLOW_STATE" "$USER_POSITION")
    fi
    
    # Format and output
    if [[ "${OUTPUT_FILE:-}" ]]; then
        format_output "$content" "$OUTPUT_FORMAT" > "$OUTPUT_FILE"
        echo -e "${GREEN}Documentation written to: $OUTPUT_FILE${NC}"
    else
        format_output "$content" "$OUTPUT_FORMAT"
    fi
    
    echo -e "${GREEN}Progressive documentation generated successfully!${NC}"
}

# Run main function
main "$@"