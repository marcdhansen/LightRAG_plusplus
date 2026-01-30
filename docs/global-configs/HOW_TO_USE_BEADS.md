# 🐚 Beads Field Manual

<https://github.com/steveyegge/beads>

Integrating Beads issue tracking with Git hooks and the Gemini CLI involves using Beads' built-in Git integration and the Gemini CLI's experimental hook system. Beads manages issues as a JSONL file in the repository, which is then committed to Git.

## Integrating Beads with Git Hooks

The Beads issue tracker stores its database in a versioned file (`.beads/issues.jsonl`) committed to the repository. The Beads setup process offers to install required Git hooks.

1. **Initialize Beads:** Run `bd init` in the project directory (or `bd init --branch beads-sync` for a separate sync branch). The initialization wizard will prompt to install recommended Git hooks and configure a merge driver.
2. **Use the Daemon:** Start the Beads daemon with `bd daemon start --auto-commit` for continuous synchronization. This automatically commits changes to the issue database to the designated sync branch.
3. **Manual Sync:** For manual control, run `bd sync` before ending a session to commit and push issue changes.
4. **Teammate Setup:** Other users should install the `bd` CLI and their agents will share the same issue database via Git pull/push operations.

## Integrating with Gemini CLI Hooks

The Gemini CLI can interact with this workflow by using its experimental hook system to run `bd` commands at specific points in its execution lifecycle (e.g., after an agent completes a task).

1. **Enable Hooks:** Enable hooks in the Gemini CLI settings file (`.gemini/settings.json`):

    ```json
    {
      "tools": {
        "enableHooks": true
      },
      "hooks": {
        "enabled": true
      }
    }
    ```

2. **Create a Hook Script:** Create a script (e.g., `.gemini/hooks/beads-sync.sh`) that runs the `bd sync` command.

    ```bash
    #!/usr/bin/env bash
    # Run beads sync
    bd sync
    ```

    Make the script executable: `chmod +x .gemini/hooks/beads-sync.sh`.

3. **Configure the Hook:** Configure the hook in the `.gemini/settings.json` file to run after the agent finishes its work (e.g., `AfterRun` or `AfterTool` events, if applicable to the workflow):

    ```json
    {
      "hooks": {
        "AfterRun": [
          {
            "name": "beads-sync",
            "type": "command",
            "command": "$GEMINI_PROJECT_DIR/.gemini/hooks/beads-sync.sh",
            "description": "Sync Beads issues after a Gemini run"
          }
        ]
      }
    }
    ```

4. **AI Agent Instruction:** In the `AGENTS.md` file or initial prompt, instruct the AI agent to use the `bd` tool for all task management. For example: "Use `bd` for issue tracking. Run `bd ready` to find next work. Always run `bd sync` before ending a session".

This setup allows the Gemini CLI to automatically keep the Beads issue tracker in sync with the repository state through Git operations, enabling an AI-powered workflow. For more details on Gemini CLI hooks, refer to the Gemini CLI documentation on writing hooks. The Beads tool and its documentation can be found on the beads GitHub repository.

---

Beads provides a persistent, structured memory for coding agents. It replaces messy markdown plans with a dependency-aware graph, allowing agents to handle long-horizon tasks without losing context.

To use the Beads issue tracker with the Gemini CLI, use the shell command within the Gemini interactive session after installing the Beads CLI tool. Beads is a git-backed issue tracker. The Gemini AI agent can be instructed to interact with it using standard shell commands. [[1](https://github.com/steveyegge/beads#:~:text=%E2%9A%A1%20Quick%20Start.%20%23%20Install%20\(macOS/Linux/FreeBSD\)%20curl,%22Use%20'bd'%20for%20task%20tracking%22%20%3E%3E%20AGENTS.md.), [2](https://www.linkedin.com/posts/steveyegge_github-steveyeggebeads-beads-a-memory-activity-7383408928665042944-tkcj), [3](https://levelup.gitconnected.com/a-coding-agent-framework-with-memory-and-issue-tracking-combined-b75122828ee1), [4](https://steve-yegge.medium.com/beads-blows-up-a0a61bb889b4), [5](https://www.philschmid.de/building-agents-interactions-api)]

## Step-by-Step Guide

1. **Install the Beads CLI**: Run the quick install script for macOS/Linux in your system's terminal:

    ```bash
    curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash
    ```

2. For other installation methods (Homebrew, npm, Windows), see the official Beads GitHub repository.

3. **Initialize Beads in Your Project**: Go to your project's root directory and initialize the Beads database:

    ```bash
    bd init
    ```

4. This creates a directory containing the database file, which is tracked in Git.

5. **Agent Instructions**: Instruct the Gemini agent to use `bd` commands for task management instead of inline `TODOs` or Markdown plans. Add a note to a file like `AGENTS.md`:

    > BEFORE ANYTHING ELSE: run `bd onboard` and follow the instructions, and use `bd` commands for issue tracking instead of markdown TODOs.

6. **Install Git Hooks (Recommended)**: To ensure automatic synchronization between the local SQLite cache and the file during Git operations, install the provided hooks.

7. **Gemini CLI Hooks**: Configure Gemini CLI hooks to run `bd` commands at key points in the agentic workflow. This is an experimental feature requiring hooks to be enabled in your `settings.json` file.
    - **Enable Hooks**: In your user or project-level `settings.json`, ensure hooks are enabled:

        ```json
        {
          "tools": {
            "enableHooks": true
          },
          "hooks": {
            "enabled": true
          }
        }
        ```

    - **Configure Custom Hooks**: Define custom scripts and link them to Gemini CLI events (e.g., `AfterTool`, `BeforeTool`, etc.). For example, you could write a script that runs `bd doctor --fix` after a major file operation or merge. Then configure a Gemini hook to run it.

8. This ensures the Gemini agent (and any human collaborators) always see up-to-date issue data.

9. **Instruct the Gemini CLI to Use Beads**: Launch the Gemini CLI in your project directory by typing in your terminal. Once in the interactive session, inform the AI agent about the workflow: `echo "Use 'bd' for task tracking. All tasks must be filed as beads issues." >> GEMINI.md`

- Tell the agent to use commands for task tracking instead of creating a file.
- You can also add an file to your repository with instructions like: .

1. **Let the Agent Manage Tasks**: You can now give high-level instructions to the Gemini agent. It will use the commands internally to break down the work, create issues, manage dependencies, and mark tasks as complete.

- Ask Gemini to create a plan: "Write a plan to implement a new login feature and create Beads issues for all the tasks".
- Ask Gemini to work: "What are the ready beads issues? Implement the next one".
- Manually run commands within the Gemini session. [[1](https://github.com/steveyegge/beads#:~:text=%E2%9A%A1%20Quick%20Start.%20%23%20Install%20\(macOS/Linux/FreeBSD\)%20curl,%22Use%20'bd'%20for%20task%20tracking%22%20%3E%3E%20AGENTS.md.), [3](https://levelup.gitconnected.com/a-coding-agent-framework-with-memory-and-issue-tracking-combined-b75122828ee1), [9](https://www.reddit.com/r/ClaudeCode/comments/1pq2hsp/beads_resources/#:~:text=*%20install%20the%20beads%20claude%20code%20plugin.,beads%20issues%22%20*%20say%20%22implement%20issue%20xyz%22), [10](https://news.ycombinator.com/item?id=46075616), [11](https://levelup.gitconnected.com/a-coding-agent-framework-with-memory-and-issue-tracking-combined-b75122828ee1), [12](https://www.youtube.com/watch?v=YAy7kd5Nqm0), [13](https://ampcode.com/threads/T-adc03ba9-db60-49e6-bae9-e5f9749f4312)]

## Core Beads Commands for Reference

While the agent will handle most interactions, you can use these commands in your regular terminal or with in the Gemini CLI to inspect or manage issues:

- `bd ready`: Shows issues that have no blockers and are ready to be worked on.
- `bd create`: Creates a new issue.
- `bd update`: Updates an issue's status.
- `bd close`: Closes a completed issue.
- `bd sync`: Forces an immediate flush of the database to the JSONL file and pushes to the remote git repo.
- `bd worktree create <name>`: Create a new Git worktree with an automatic Beads database redirect, allowing parallel development in a separate directory without losing issue context.

## Parallel Development Strategy

To work on multiple tasks simultaneously or with multiple agents:

1. **Create a Worktree**: Run `bd worktree create <task-name>`. This creates a new directory where you can branch and commit independently.
2. **Branching**: In the new worktree, create a task-specific branch: `git checkout -b task/lightrag-N`.
3. **Commit Discipline**: Always stage specific files (`git add path/to/file`) instead of using bulk commands like `git add .`.
4. **Sync**: Run `bd sync` as usual. Beads will handle the synchronization of the issue database across all worktrees.

_AI responses may include mistakes._

[1] <https://github.com/steveyegge/beads>

[2] <https://www.linkedin.com/posts/steveyegge_github-steveyeggebeads-beads-a-memory-activity-7383408928665042944-tkcj>

[3] <https://levelup.gitconnected.com/a-coding-agent-framework-with-memory-and-issue-tracking-combined-b75122828ee1>

[4] <https://steve-yegge.medium.com/beads-blows-up-a0a61bb889b4>

[5] <https://www.philschmid.de/building-agents-interactions-api>

[6] <https://cloud.google.com/blog/products/ai-machine-learning/automate-app-deployment-and-security-analysis-with-new-gemini-cli-extensions>

[7] <https://realpython.com/how-to-use-gemini-cli/>

[8] <https://medium.com/google-cloud/gemini-cli-tutorial-series-part-13-gemini-cli-observability-c410806bc112>

[9] <https://www.reddit.com/r/ClaudeCode/comments/1pq2hsp/beads_resources/>

[10] <https://news.ycombinator.com/item?id=46075616>

[11] <https://levelup.gitconnected.com/a-coding-agent-framework-with-memory-and-issue-tracking-combined-b75122828ee1>

[12] <https://www.youtube.com/watch?v=YAy7kd5Nqm0>

[13] <https://ampcode.com/threads/T-adc03ba9-db60-49e6-bae9-e5f9749f4312>

[14] <https://geminicli.com/docs/cli/commands/>

[15] <https://github.com/addyosmani/gemini-cli-tips>

[16] <https://github.com/frankbria/iris/blob/main/docs/beads-migration-guide.md>

[17] <https://finance.yahoo.com/news/google-dev-tools-manager-makes-182854202.html>

[18] <https://gitbetter.substack.com/p/git-cli-bring-github-to-the-command>

[19] <https://medium.com/google-cloud/using-gemini-cli-to-create-a-gemini-cli-config-repo-519399e25d9a>

[20] <https://github.com/steveyegge/beads/blob/main/AGENT_INSTRUCTIONS.md>

Using Gemini Conductor with Beads allows for managing software development projects with persistent, AI-driven context (Conductor) and tracking issues in a git-native, AI-readable database (Beads). Conductor plans and codes, while Beads serves as the issue repository, typically storing data in a `.beads/issues.jsonl` file within a repository.

Here is how to use Gemini Conductor with Beads for issue tracking:

## Initial Setup

- **Install Gemini CLI & Conductor**: Install the Gemini CLI and the Conductor extension using `gemini extensions install`.
- **Initialize Conductor**: Run `/conductor:setup` in the terminal within the project directory. This creates the necessary `.conductor` folder and context files (`product.md`, `tech-stack.md`, `workflow.md`).
- **Initialize Beads**: Install the Beads CLI (`bd`) and run `bd init` in the project root to set up the `.beads` repository.

## Issue Tracking Workflow

Beads acts as a private database for the AI agent to track issues, which Conductor uses to structure its work.

1. **Define Tasks in Beads**: Use `bd add "Issue description"` to create tasks. Beads stores these locally in `.beads/issues.jsonl`.
2. **Create a Conductor Track**: Run `/conductor:newTrack "Solve issue #X from Beads"`.
3. **Generate Plan with Conductor**: Conductor will read the current state of the project and the specific issue, generating a `plan.md` file in `conductor/tracks/<track_id>/`.
4. **Execute and Implement**: Run `/conductor:implement`. Conductor will follow the `plan.md`, performing coding, testing, and implementation while keeping the context.
5. **Close the Issue**: Once the implementation is verified, use `bd close #X` to mark the issue as completed in Beads.

## Best Practices for Combined Use

- **Plan Outside, Track Inside**: Use Conductor to create detailed plans, but store the actionable tickets/bugs in Beads.
- **Manage Context Size**: Keep the Beads issue set small; if the `issues.jsonl` file exceeds ~25k tokens, AI agents may struggle to read it.
- **Use `bd doctor`**: Periodically run `bd doctor --fix` to resolve potential conflicts in the issue database, as Bead handles complex, Git-backed data.
- **Hybrid Workflow**: Use Conductor to update `plan.md` (the "how"), while using Beads to update the status of the "what" (bugs/features).

## Key Commands

- `/conductor:setup`: Sets up project context.
- `/conductor:newTrack`: Starts a new task/bug fix.
- `/conductor:implement`: Executes the plan.
- `bd add` / `bd edit` / `bd close`: Manages Beads issue database.

## Troubleshooting Sync Issues

Here are the common Beads (bd) sync problems and their solutions based on official troubleshooting documentation:

### 1. Old Data Appears After Reset

**Problem**: Running `bd admin reset --force` followed by `bd init` causes old issues to reappear.
**Solution**:

1. Run `bd admin reset --force`.
2. Find your sync branch using `bd config get sync.branch` and delete it from the remote repository: `git push origin --delete <sync-branch-name>`.
3. If data persists, remove the JSONL file from Git history:

    ```bash
    git filter-branch --force --index-filter \
    'git rm --cached --ignore-unmatch .beads/issues.jsonl' \
    --prune-empty -- --all
    git push origin --force --all
    ```

### 2. Issues Lost or Desynced

**Problem**: `bd sync` fails to update issues across machines, or AI agents report fewer issues than exist on the remote.
**Solution**:

- **Force Pull/Merge**: Use `bd pull` or `bd sync --full` to force a 3-way merge.
- **Check Daemon Logs**: If the auto-sync fails, check the daemon logs for errors: `bd daemon logs`.
- **Manual Recovery**: Because Beads uses Git, you can inspect the JSONL history to restore lost issues.

### 3. Concurrent Edit Conflicts

**Problem**: Multiple AI agents create or update issues simultaneously.
**Solution**:

- **Assign Unique Work**: Define specific, non-overlapping tasks for agents by using unique labels (e.g., `agent:alpha`, `agent:beta`).
- **Use `bd sync` Often**: Regularly sync (at the start and end of every session/turn) to keep local state in check and avoid merge conflicts.
- **Dependency Tracking**: Use `bd dep` to establish clear work orders, ensuring agents do not start tasks with unsatisfied blockers.
- **Use `bd doctor`**: If database locks or corruption occurs due to concurrency, run `bd doctor --fix`.
- **Swarm Coordination**: For complex epics, use `bd swarm` to manage a DAG of parallelizable tasks. Regardless of the tool, ensure each agent is working on a distinct issue in the `ready` state.

### 4. Sync Branch is Protected

**Problem**: `bd sync` fails because the remote repository protects the beads-sync or beads-metadata branch.
**Solution**:

- **Unprotect Branch**: Remove protection rules for the beads-sync branch, as it is just metadata.

### 5. "Git Add Failed" due to Local Exclude

**Problem**: `bd sync` fails with `git add failed` error, claiming the path is ignored, even though `.gitignore` does not exclude `.beads/`.
**Cause**: `bd init` (or other tools) may populate `.git/info/exclude` with `.beads/` to generically hide the directory, which overrides `.gitignore` allow-lists.
**Solution**:

1. Run `cat .git/info/exclude`.
2. Edit the file to remove the `.beads/` line, or run `sed -i '' '/\.beads\//d' .git/info/exclude`.
3. "Operation Not Permitted" or "Failed to rename"

**Problem**: `bd ready` or other commands fail with `failed to rename file: ... .beads/issues.jsonl: operation not permitted`.
**Cause**: This often happens on macOS when `.beads/issues.jsonl` is ignored by Git but something else is accessing it, or if there's a file lock conflict.
**Solution**:

1. Ensure `.beads/issues.jsonl` is NOT in your `.gitignore`. Beads expects the JSONL file to be tracked in Git for synchronization.
2. If it was in `.gitignore`, remove it and run `git add .beads/issues.jsonl`.
3. Stop any background Beads daemons: `bd daemon stop`.
4. Try running the command again.
5. If the issue persists, check if any sync tools (like iCloud, Dropbox, or a file watcher) are locking the `.beads` directory.
