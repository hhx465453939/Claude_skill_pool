# Gemini CLI Developer Scaffold

This scaffold includes a suite of powerful skills designed to accelerate your development workflow with Gemini CLI.

## Included Skills

The following skills are pre-configured in `.gemini/skills/`:

### 1. **ai-spec**
   - **Role**: Full-stack Architect & AI Instruction Optimizer.
   - **Usage**: Use this skill to translate natural language requirements into production-ready technical specifications (PRD) and detailed AI coding instructions.
   - **Key Features**: Requirement audit, architecture search, spec generation, "God Prompt" creation.

### 2. **api-first-modular**
   - **Role**: API-First Development Framework Guide.
   - **Usage**: Follows the "API-First Modular" methodology. Enforces separation of concerns where backend features are encapsulated as API packages, and frontend only consumes APIs.
   - **Key Features**: 3-layer architecture model, 5-step backend development loop, cross-layer task decomposition.

### 3. **code-debugger**
   - **Role**: Intelligent Code Debugging & Incremental Development System.
   - **Usage**: Activates a context-aware debugging assistant.
   - **Key Features**:
     - **Context Builder**: Explore code, build relationship maps (call chains, variable dependencies).
     - **Debug Executor**: Locate issues, design solutions, implement fixes, and verify with tests.
     - **.debug documentation**: Maintains a persistent knowledge base of debugging sessions.

### 4. **debug-ui**
   - **Role**: Top-tier UI Visual Design & Implementation System.
   - **Usage**: specialized for UI/UX tasks. Bridges the gap between aesthetic intuition ("make it pop") and engineering implementation (CSS/Tailwind).
   - **Key Features**: Aesthetic resonance, holistic visual audit, artistic execution.

### 5. **prd**
   - **Role**: PRD Generator.
   - **Usage**: Interactive tool to generate structured Product Requirements Documents.
   - **Key Features**: Clarifying questions loop, standard PRD structure generation.

### 6. **ralph**
   - **Role**: Autonomous Agent Loop (Standard).
   - **Usage**: Automates the implementation of PRDs by spawning fresh agent instances for each user story.
   - **Note**: Requires an environment supporting the execution loop (like `ralph.sh`).

### 7. **ralph-yolo**
   - **Role**: Autonomous Agent Loop (Lightweight/YOLO).
   - **Usage**: A version of Ralph that runs directly within the current session context, managing sub-agents to complete user stories sequentially.

## How to Use

1. **Ensure Gemini CLI is installed.**
2. **Navigate to this project root.**
3. **Trigger a skill** by describing your intent.
   - *Example*: "I need to design a new feature for user authentication. Please help me create a spec." -> Activates `ai-spec` or `prd`.
   - *Example*: "Debug this API endpoint error." -> Activates `code-debugger`.
   - *Example*: "Make this dashboard look more modern and Swiss style." -> Activates `debug-ui`.

## Directory Structure

```
.gemini/
└── skills/
    ├── ai-spec/
    ├── api-first-modular/
    ├── code-debugger/
    ├── debug-ui/
    ├── prd/
    ├── ralph/
    └── ralph-yolo/
```

Enjoy building with Gemini!
