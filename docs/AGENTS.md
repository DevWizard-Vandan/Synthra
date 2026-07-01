# Synthra Agent Specification

> **Version:** 1.0.0  
> **Topic:** Agent Interfaces, Protocols, and Sandbox Integration  

---

## 🤖 Agent Taxonomy

Synthra defines a hierarchy of agents, each designed for specific scopes of action:

```
                  +---------------------+
                  |  Coordinator Agent  |  <--- Interface with User/CLI
                  +---------------------+
                             |
              +--------------+--------------+
              |                             |
      +---------------+             +---------------+
      |  Worker Agent |             | Specialist Agt|  <--- Focused on specific
      |  (File/Code)  |             |  (e.g., DB)   |       tools / models
      +---------------+             +---------------+
```

### 1. Coordinator Agent
*   **Role**: Orchestrates the high-level task. It interacts directly with the user interface, writes the `implementation_plan.md`, tracks task progress via `task.md`, and compiles the `walkthrough.md`.
*   **Capabilities**: Spawns worker and specialist subagents; monitors system states; manages human-in-the-loop loops.

### 2. Worker Agent
*   **Role**: Executes general development tasks, such as creating, reading, and editing source code files, and running build/test commands.
*   **Capabilities**: Code editing, directory parsing, and local command execution.

### 3. Specialist Agent
*   **Role**: Interacts with external systems, databases, or API protocols (e.g., running docker configurations, performing science queries, clinical trials).
*   **Capabilities**: Access to restricted toolsets with specialized models or prompt instructions.

---

## 📝 Interface Specifications

All agents must implement the base `ISynthraAgent` interface:

```typescript
interface ISynthraAgent {
  id: string;
  role: string;
  capabilities: string[];
  status: 'idle' | 'planning' | 'executing' | 'blocked' | 'done' | 'failed';
  
  // Lifecycle Hooks
  initialize(sessionContext: ISessionContext): Promise<void>;
  execute(taskPrompt: string): Promise<IExecutionResult>;
  onMessageReceived(message: IAgentMessage): void;
  terminate(): Promise<void>;
}
```

```python
class BaseSynthraAgent:
    def __init__(self, agent_id: str, role: str):
        self.id = agent_id
        self.role = role
        self.status = "idle"

    async def initialize(self, context: SessionContext) -> None:
        """Runs initialization routines (loading tools, memory connection)."""
        pass

    async def execute(self, prompt: str) -> ExecutionResult:
        """Executes a task loop until finished or blocked."""
        pass
```

---

## 💬 Message Schema & Protocol

Agents communicate over the Message Bus using structured JSON-RPC payloads. A standard message contains:

```json
{
  "jsonrpc": "2.0",
  "id": "msg_01H8X...",
  "method": "agent.message",
  "params": {
    "sender": "coordinator_01",
    "recipient": "worker_03",
    "timestamp": "2026-07-01T20:34:00Z",
    "payload": {
      "type": "TASK_DELEGATION",
      "task_id": "task_sub_42",
      "content": "Create a unit test file for math_utils.py and run pytest."
    }
  }
}
```

### Supported Message Types:
*   `TASK_DELEGATION`: Sent by a Coordinator to a Worker with specific task details.
*   `TASK_REPORT`: Sent by a Worker back to its parent detailing results or failures.
*   `RESOURCE_REQUEST`: Sent by an agent to request extra filesystem or network permissions.
*   `USER_PROMPT`: Sent by the Coordinator to solicit user feedback or choices.

---

## 🔒 Sandboxing & Permission Requests

Agents are blocked from executing commands or accessing directories outside of the active workspace root. If an agent requires wider access, it must follow the **Permission Escalation Lifecycle**:

1.  **Intercept**: The sandbox controller intercepts a forbidden system call (e.g., editing a file in `C:\Windows\`).
2.  **Request**: The agent sends a `RESOURCE_REQUEST` payload to the Coordinator.
3.  **Human Verification**: The Coordinator presents a detailed prompt to the user explaining *why* the access is needed.
4.  **Grant/Deny**: If the user approves, a temporary permission token is attached to the agent's runtime profile.
