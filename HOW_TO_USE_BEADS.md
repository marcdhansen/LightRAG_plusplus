https://github.com/steveyegge/beads
Integrating Beads issue tracking with Git hooks and the Gemini CLI involves using Beads' built-in Git integration and the Gemini CLI's experimental hook system. Beads manages issues as a JSONL file in the repository, which is then committed to Git.

### Integrating Beads with Git Hooks

The Beads issue tracker stores its database in a versioned file (`.beads/issues.jsonl`) committed to the repository. The Beads setup process offers to install required Git hooks. 

1. **Initialize Beads:** Run `bd init` in the project directory (or `bd init --branch beads-sync` for a separate sync branch). The initialization wizard will prompt to install recommended Git hooks and configure a merge driver.
2. **Use the Daemon:** Start the Beads daemon with `bd daemon start --auto-commit` for continuous synchronization. This automatically commits changes to the issue database to the designated sync branch.
3. **Manual Sync:** For manual control, run `bd sync` before ending a session to commit and push issue changes.
4. **Teammate Setup:** Other users should install the `bd` CLI and their agents will share the same issue database via Git pull/push operations. 

### Integrating with Gemini CLI Hooks

The Gemini CLI can interact with this workflow by using its experimental hook system to run `bd` commands at specific points in its execution lifecycle (e.g., after an agent completes a task). 

1. **Enable Hooks:** Enable hooks in the Gemini CLI settings file (`.gemini/settings.json`):
    json
    ```
    {
      "tools": {
        "enableHooks": true
      },
      "hooks": {
        "enabled": true
      }
    }
    ```
2. **Create a Hook Script:** Create a script (e.g., `.gemini/hooks/beads-sync.sh`) that runs the `bd sync` command.
    bash
    ```
    #!/usr/bin/env bash
    # Run beads sync
    bd sync
    ```
    Make the script executable: `chmod +x .gemini/hooks/beads-sync.sh`.
3. **Configure the Hook:** Configure the hook in the `.gemini/settings.json` file to run after the agent finishes its work (e.g., `AfterRun` or `AfterTool` events, if applicable to the workflow):
    json
    ```
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
4. **AI Agent Instruction:** In the `AGENTS.md` file or initial prompt, instruct the AI agent to use the `bd` tool for all task management. For example: "Use `bd` for issue tracking. Run `bd ready` to find next work. Always run `bd sync` before ending a session". 

This setup allows the Gemini CLI to automatically keep the Beads issue tracker in sync with the repository state through Git operations, enabling an AI-powered workflow. For more details on Gemini CLI hooks, refer to the Gemini CLI documentation on writing hooks. The Beads tool and its documentation can be found on the beads GitHub repository.

---
Beads provides a persistent, structured memory for coding agents. It replaces messy markdown plans with a dependency-aware graph, allowing agents to handle long-horizon tasks without losing context.

To use the Beads issue tracker with the Gemini CLI, use the shell command within the Gemini interactive session after installing the Beads CLI tool. Beads is a git-backed issue tracker. The Gemini AI agent can be instructed to interact with it using standard shell commands. [[1](https://github.com/steveyegge/beads#:~:text=%E2%9A%A1%20Quick%20Start.%20%23%20Install%20\(macOS/Linux/FreeBSD\)%20curl,%22Use%20'bd'%20for%20task%20tracking%22%20%3E%3E%20AGENTS.md.), [2](https://www.linkedin.com/posts/steveyegge_github-steveyeggebeads-beads-a-memory-activity-7383408928665042944-tkcj), [3](https://levelup.gitconnected.com/a-coding-agent-framework-with-memory-and-issue-tracking-combined-b75122828ee1), [4](https://steve-yegge.medium.com/beads-blows-up-a0a61bb889b4), [5](https://www.philschmid.de/building-agents-interactions-api)] 

### Step-by-Step Guide 

1. Install the Beads CLIRun the quick install script for macOS/Linux in your system's terminal: 
`curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash
`
2. For other installation methods (Homebrew, npm, Windows), see the official Beads GitHub repository.
3. Initialize Beads in Your ProjectGo to your project's root directory and initialize the Beads database:  
4. `bd init`
5. This creates a directory containing the database file, which is tracked in Git. 
6. **Agent Instructions**: Instruct the Gemini agent to use `bd` commands for task management instead of inline `TODOs` or Markdown plans. Add a note to a file like `AGENTS.md`:
    
    > BEFORE ANYTHING ELSE: run `bd onboard` and follow the instructions, and use `bd` commands for issue tracking instead of markdown TODOs.
7. Install Git Hooks (Recommended)To ensure automatic synchronization between the local SQLite cache and the file during Git operations, install the provided hooks: 
8. **Gemini CLI Hooks**: Configure Gemini CLI hooks to run `bd` commands at key points in the agentic workflow. This is an experimental feature requiring hooks to be enabled in your `settings.json` file.
    - **Enable Hooks**: In your user or project-level `settings.json`, ensure hooks are enabled:
        json
        ```
        {
          "tools": {
            "enableHooks": true
          },
          "hooks": {
            "enabled": true
          }
        }
        ```
        
    - **Configure Custom Hooks**: Define custom scripts and link them to Gemini CLI events (e.g., `AfterTool`, `BeforeTool`, etc.). For example, you could write a script that runs `bd doctor --fix` after a major file operation or merge. Then configure a Gemini hook to run it.
9. This ensures the Gemini agent (and any human collaborators) always see up-to-date issue data. 
10. Instruct the Gemini CLI to Use BeadsLaunch the Gemini CLI in your project directory by typing in your terminal. Once in the interactive session, inform the AI agent about the workflow: `echo "Use 'bd' for task tracking. All tasks must be filed as beads issues." >> GEMINI.md`

- Tell the agent to use commands for task tracking instead of creating a file. 
- You can also add an file to your repository with instructions like: . 

9. Let the Agent Manage TasksYou can now give high-level instructions to the Gemini agent. It will use the commands internally to break down the work, create issues, manage dependencies, and mark tasks as complete. 

- Ask Gemini to create a plan: "Write a plan to implement a new login feature and create Beads issues for all the tasks". 
- Ask Gemini to work: "What are the ready beads issues? Implement the next one". 
- Manually run commands within the Gemini session by prefixing them with : . [[1](https://github.com/steveyegge/beads#:~:text=%E2%9A%A1%20Quick%20Start.%20%23%20Install%20\(macOS/Linux/FreeBSD\)%20curl,%22Use%20'bd'%20for%20task%20tracking%22%20%3E%3E%20AGENTS.md.), [3](https://levelup.gitconnected.com/a-coding-agent-framework-with-memory-and-issue-tracking-combined-b75122828ee1), [9](https://www.reddit.com/r/ClaudeCode/comments/1pq2hsp/beads_resources/#:~:text=*%20install%20the%20beads%20claude%20code%20plugin.,beads%20issues%22%20*%20say%20%22implement%20issue%20xyz%22), [10](https://news.ycombinator.com/item?id=46075616), [11](https://levelup.gitconnected.com/a-coding-agent-framework-with-memory-and-issue-tracking-combined-b75122828ee1), [12](https://www.youtube.com/watch?v=YAy7kd5Nqm0), [13](https://ampcode.com/threads/T-adc03ba9-db60-49e6-bae9-e5f9749f4312)] 

Core Beads Commands for Reference 

While the agent will handle most interactions, you can use these commands in your regular terminal or with in the Gemini CLI to inspect or manage issues: 

- : Shows issues that have no blockers and are ready to be worked on. 
- : Creates a new issue. 
- : Updates an issue's status. 
- : Closes a completed issue. 
- : Forces an immediate flush of the database to the JSONL file and pushes to the remote git repo. [[16](https://github.com/frankbria/iris/blob/main/docs/beads-migration-guide.md), [17](https://finance.yahoo.com/news/google-dev-tools-manager-makes-182854202.html#:~:text=A%20development%20task%20will%20usually%20start%20as,a%20more%20robust%20requirement%20doc%20in%20Markdown.), [18](https://gitbetter.substack.com/p/git-cli-bring-github-to-the-command#:~:text=Creating%20an%20issue%20Creating%20a%20simple%20issue,issue%20with%20the%20respective%20title%20and%20body.), [19](https://medium.com/google-cloud/using-gemini-cli-to-create-a-gemini-cli-config-repo-519399e25d9a), [20](https://github.com/steveyegge/beads/blob/main/AGENT_INSTRUCTIONS.md#:~:text=Agent%20Session%20Workflow%20Without%20bd%20sync%20%2C,still%20dirty%20bd%20sync%20forces%20immediate%20flush/commit/push)] 

  

_AI responses may include mistakes._

[1] [https://github.com/steveyegge/beads](https://github.com/steveyegge/beads#:~:text=%E2%9A%A1%20Quick%20Start.%20%23%20Install%20\(macOS/Linux/FreeBSD\)%20curl,%22Use%20'bd'%20for%20task%20tracking%22%20%3E%3E%20AGENTS.md.)

[2] [https://www.linkedin.com/posts/steveyegge_github-steveyeggebeads-beads-a-memory-activity-7383408928665042944-tkcj](https://www.linkedin.com/posts/steveyegge_github-steveyeggebeads-beads-a-memory-activity-7383408928665042944-tkcj)

[3] [https://levelup.gitconnected.com/a-coding-agent-framework-with-memory-and-issue-tracking-combined-b75122828ee1](https://levelup.gitconnected.com/a-coding-agent-framework-with-memory-and-issue-tracking-combined-b75122828ee1)

[4] [https://steve-yegge.medium.com/beads-blows-up-a0a61bb889b4](https://steve-yegge.medium.com/beads-blows-up-a0a61bb889b4)

[5] [https://www.philschmid.de/building-agents-interactions-api](https://www.philschmid.de/building-agents-interactions-api)

[6] [https://cloud.google.com/blog/products/ai-machine-learning/automate-app-deployment-and-security-analysis-with-new-gemini-cli-extensions](https://cloud.google.com/blog/products/ai-machine-learning/automate-app-deployment-and-security-analysis-with-new-gemini-cli-extensions)

[7] [https://realpython.com/how-to-use-gemini-cli/](https://realpython.com/how-to-use-gemini-cli/)

[8] [https://medium.com/google-cloud/gemini-cli-tutorial-series-part-13-gemini-cli-observability-c410806bc112](https://medium.com/google-cloud/gemini-cli-tutorial-series-part-13-gemini-cli-observability-c410806bc112#:~:text=Gemini%20CLI:%20You%20should%20have%20Gemini%20CLI,account.%20We%20covered%20this%20in%20Part%201.)

[9] [https://www.reddit.com/r/ClaudeCode/comments/1pq2hsp/beads_resources/](https://www.reddit.com/r/ClaudeCode/comments/1pq2hsp/beads_resources/#:~:text=*%20install%20the%20beads%20claude%20code%20plugin.,beads%20issues%22%20*%20say%20%22implement%20issue%20xyz%22)

[10] [https://news.ycombinator.com/item?id=46075616](https://news.ycombinator.com/item?id=46075616)

[11] [https://levelup.gitconnected.com/a-coding-agent-framework-with-memory-and-issue-tracking-combined-b75122828ee1](https://levelup.gitconnected.com/a-coding-agent-framework-with-memory-and-issue-tracking-combined-b75122828ee1)

[12] [https://www.youtube.com/watch?v=YAy7kd5Nqm0](https://www.youtube.com/watch?v=YAy7kd5Nqm0)

[13] [https://ampcode.com/threads/T-adc03ba9-db60-49e6-bae9-e5f9749f4312](https://ampcode.com/threads/T-adc03ba9-db60-49e6-bae9-e5f9749f4312)

[14] [https://geminicli.com/docs/cli/commands/](https://geminicli.com/docs/cli/commands/#:~:text=Copy%20as%20Markdown%20Copied!%20Gemini%20CLI%20supports,or%20an%20exclamation%20mark%20\(%20!%20\).)

[15] [https://github.com/addyosmani/gemini-cli-tips](https://github.com/addyosmani/gemini-cli-tips#:~:text=Gemini%20CLI%20is%20available%20on%20all%20major,your%20terminal%20to%20launch%20the%20interactive%20CLI.)

[16] [https://github.com/frankbria/iris/blob/main/docs/beads-migration-guide.md](https://github.com/frankbria/iris/blob/main/docs/beads-migration-guide.md)

[17] [https://finance.yahoo.com/news/google-dev-tools-manager-makes-182854202.html](https://finance.yahoo.com/news/google-dev-tools-manager-makes-182854202.html#:~:text=A%20development%20task%20will%20usually%20start%20as,a%20more%20robust%20requirement%20doc%20in%20Markdown.)

[18] [https://gitbetter.substack.com/p/git-cli-bring-github-to-the-command](https://gitbetter.substack.com/p/git-cli-bring-github-to-the-command#:~:text=Creating%20an%20issue%20Creating%20a%20simple%20issue,issue%20with%20the%20respective%20title%20and%20body.)

[19] [https://medium.com/google-cloud/using-gemini-cli-to-create-a-gemini-cli-config-repo-519399e25d9a](https://medium.com/google-cloud/using-gemini-cli-to-create-a-gemini-cli-config-repo-519399e25d9a)

[20] [https://github.com/steveyegge/beads/blob/main/AGENT_INSTRUCTIONS.md](https://github.com/steveyegge/beads/blob/main/AGENT_INSTRUCTIONS.md#:~:text=Agent%20Session%20Workflow%20Without%20bd%20sync%20%2C,still%20dirty%20bd%20sync%20forces%20immediate%20flush/commit/push)


Using Gemini Conductor with Beads allows for managing software development projects with persistent, AI-driven context (Conductor) and tracking issues in a git-native, AI-readable database (Beads). Conductor plans and codes, while Beads serves as the issue repository, typically storing data in a `.beads/issues.jsonl` file within a repository. 

Here is how to use Gemini Conductor with Beads for issue tracking:

1. Initial Setup

- Install Gemini CLI & Conductor: Install the Gemini CLI and the Conductor extension using `gemini extensions install`.
- Initialize Conductor: Run `/conductor:setup` in the terminal within the project directory. This creates the necessary `.conductor` folder and context files (`product.md`, `tech-stack.md`, `workflow.md`).
- Initialize Beads: Install the Beads CLI (`bd`) and run `bd init` in the project root to set up the `.beads` repository. 

2. Issue Tracking Workflow

Beads acts as a private database for the AI agent to track issues, which Conductor uses to structure its work. 

1. Define Tasks in Beads: Use `bd add "Issue description"` to create tasks. Beads stores these locally in `.beads/issues.jsonl`.
2. Create a Conductor Track: Run `/conductor:newTrack "Solve issue #X from Beads"`.
3. Generate Plan with Conductor: Conductor will read the current state of the project and the specific issue, generating a `plan.md` file in `conductor/tracks/<track_id>/`.
4. Execute and Implement: Run `/conductor:implement`. Conductor will follow the `plan.md`, performing coding, testing, and implementation while keeping the context.
5. Close the Issue: Once the implementation is verified, use `bd close #X` to mark the issue as completed in Beads. 

6. Best Practices for Combined Use

- Plan Outside, Track Inside: Use Conductor to create detailed plans, but store the actionable tickets/bugs in Beads.
- Manage Context Size: Keep the Beads issue set small; if the `issues.jsonl` file exceeds ~25k tokens, AI agents may struggle to read it.
- Use `bd doctor`: Periodically run `bd doctor --fix` to resolve potential conflicts in the issue database, as Bead handles complex, Git-backed data.
- Hybrid Workflow: Use Conductor to update `plan.md` (the "how"), while using Beads to update the status of the "what" (bugs/features). 

Key Commands

- `/conductor:setup`: Sets up project context.
- `/conductor:newTrack`: Starts a new task/bug fix.
- `/conductor:implement`: Executes the plan.
- `bd add` / `bd edit` / `bd close`: Manages Beads issue database. 

_Note: As of early 2026, Conductor and Beads are often used in advanced AI workflows and may require familiarity with git-based, agentic systems._
