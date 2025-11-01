# Agent System

This directory contains the multi-agent task management system built from scratch using OpenAI's function calling API.

## Architecture

The system uses a **routing-based architecture** with specialized agents:

```
User Message
    ↓
Router Agent (Intent Classification)
    ↓
    ├─→ Conversational Handler (social messages)
    ├─→ Clarifier Agent (ambiguous messages)
    └─→ Task Agent (task operations)
```

## Components

### 1. **models.py**
Pydantic models for structured agent responses:
- `IntentClassificationResponse` - Router output
- `ClarifierResponse` - Clarification questions
- `ClarificationResolutionResponse` - Resolved messages

### 2. **router.py**
Intent classification agent that routes messages to:
- `conversational` - Social/emotional messages
- `agent` - Task-related actions
- `clarify` - Ambiguous references

### 3. **clarifier.py**
Handles ambiguous user messages:
- Generates clarifying questions
- Resolves user responses into explicit messages
- Uses conversation history for context

### 4. **conversational.py**
Handles social messages with friendly responses:
- Greetings
- Thanks
- Emotional expressions

### 5. **task_agent.py**
Function-calling agent for task operations:
- Context-aware (uses conversation history)
- Handles temporal references (tomorrow, next week)
- Implements agentic loop (max 10 iterations)
- Generates natural language summaries

**Available Operations:**
- `list_all_tasks()`, `list_tasks(status, priority, limit)`
- `get_task(task_id)`
- `create_task(title, description, priority)`
- `update_task(task_id, ...)`
- `complete_task(task_id)`, `mark_complete(task_id)`
- `delete_task(task_id)`

### 6. **orchestrator.py**
Main coordinator that:
- Routes messages through appropriate agents
- Manages conversation history
- Provides `run_task_manager()` and `interactive_chat()`

## Usage

### Interactive Chat

Run the interactive chat interface:

```bash
python -m milo.main chat
```

Or programmatically:

```python
from milo.agents import interactive_chat

interactive_chat()
```

### Programmatic Usage

```python
from openai import OpenAI
from milo.agents import run_task_manager
from milo.tasks.service import TaskService
from milo.core.config import settings

# Initialize
client = OpenAI(api_key=settings.OPENAI_API_KEY)
task_service = TaskService()
conversation_history = []

# Process a message
result = run_task_manager(
    "Create a task to review the quarterly report",
    task_service,
    client,
    conversation_history
)

print(result["response"])
print(f"Route: {result['route']}")
```

## Example Flows

### Direct Task Operation
```
User: "Create a task to buy groceries"
→ Router: agent
→ Task Agent: create_task()
→ Response: "Created task: 'Buy groceries'"
```

### Clarification Flow
```
User: "Delete the one with the people"
→ Router: clarify
→ Clarifier: "Did you mean team proposals or client meeting?"
User: "The client one"
→ Resolver: "Delete the task titled 'Schedule client meeting'"
→ Router: agent
→ Task Agent: list_all_tasks() → delete_task(3)
→ Response: "Deleted task (ID: 3)"
```

### Context-Aware Updates
```
User: "I need to write a new report on Memory Patterns"
→ Creates task (ID: 8)
User: "Its due tomorrow"
→ Task Agent recognizes "it" refers to task 8
→ Updates task with due_date = tomorrow
```

## Design Patterns

### Agentic Loop
The task agent implements an agentic loop that:
1. Calls LLM with available tools
2. Executes tool calls
3. Feeds results back to LLM
4. Repeats until task is complete (max 10 iterations)

### Search-Then-Operate
When task ID is unknown:
1. Call `list_all_tasks()` to find task
2. Extract task_id from results
3. Perform operation (delete/update/complete)

### Conversation History Management
- Router uses entire history for context
- Task agent uses last 3 messages (configurable)
- Clarifier uses all history

## Key Features

1. **Modular Design** - Each agent is self-contained
2. **Context Awareness** - Uses conversation history for implicit references
3. **Temporal Intelligence** - Handles relative dates naturally
4. **Robust Error Handling** - Traceback logging, graceful failures
5. **Natural Interaction** - Clarification flow feels conversational
6. **Extensible** - Easy to add new agents

## Dependencies

- OpenAI API (function calling)
- Pydantic (structured outputs)
- TaskService (database operations)
- Utility functions (prompt builders, validators)

