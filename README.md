# Milo - AI Task Manager

An intelligent task management system powered by multi-agent AI architecture using OpenAI's function calling API.

## Features

- 🤖 **Multi-Agent Architecture** - Specialized agents for routing, clarification, and task execution
- 💬 **Natural Conversation** - Chat naturally about your tasks
- 🔍 **Smart Clarification** - Automatically asks for clarification when needed
- 📅 **Temporal Intelligence** - Understands relative dates (tomorrow, next week, etc.)
- 🧠 **Context Awareness** - Remembers conversation history for implicit references
- ⚡ **Agentic Loop** - Chains multiple operations automatically

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd milo

# Install dependencies using uv
uv sync
```

### Setup

1. Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

2. Initialize the database and create sample tasks:

```bash
python -m milo.main chat
```

## Usage

### Interactive Chat Mode

Run the interactive chat interface:

```bash
python -m milo.main chat
```

Example conversation:

```
You: Hi
Assistant: Hello! How can I help you today?

You: I need to write a new report on Memory Patterns in AI Agent
Assistant: Created task: 'Write report on Memory Patterns in AI Agent'

You: Its due tomorrow
Assistant: Updated task (ID: 8)

You: exit
👋 Goodbye!
```

### FastAPI Server Mode

Run the API server:

```bash
python -m milo.main
```

The server will start at `http://localhost:8000` with automatic API documentation at `/docs`.

## Project Structure

```
milo/
├── src/milo/
│   ├── agents/              # Multi-agent system
│   │   ├── models.py        # Pydantic response models
│   │   ├── router.py        # Intent classification
│   │   ├── clarifier.py     # Ambiguity resolution
│   │   ├── conversational.py # Social message handler
│   │   ├── task_agent.py    # Task execution agent
│   │   ├── orchestrator.py  # Main coordinator
│   │   └── README.md        # Detailed agent documentation
│   ├── core/                # Configuration & logging
│   │   ├── config.py
│   │   └── logger/
│   ├── models/              # Domain models
│   ├── shared/              # Utilities
│   │   ├── database.py      # Database session management
│   │   ├── json_generator.py # JSON serialization
│   │   └── utils.py         # Prompt builders & validators
│   ├── tasks/               # Task domain
│   │   ├── models.py        # Task data models
│   │   ├── service.py       # CRUD operations
│   │   └── tools.py         # Tool execution
│   └── main.py              # Entry point
├── data/                    # SQLite database
├── logs/                    # Application logs
├── rough/                   # Notebooks & experiments
└── pyproject.toml          # Project dependencies
```

## Agent System Architecture

```
User Message
    ↓
Router Agent (Intent Classification)
    ↓
    ├─→ Conversational Handler (greetings, thanks)
    ├─→ Clarifier Agent (ambiguous messages)
    └─→ Task Agent (task operations)
          └─→ Tool Execution (CRUD operations)
```

### Agent Types

1. **Router Agent** - Classifies user intent into:
   - `conversational` - Social/emotional messages
   - `agent` - Task-related actions
   - `clarify` - Ambiguous references

2. **Clarifier Agent** - Handles ambiguous messages:
   - Generates clarifying questions
   - Resolves user responses
   - Uses conversation history

3. **Conversational Handler** - Friendly responses for social messages

4. **Task Agent** - Executes task operations:
   - Function calling with agentic loop
   - Context-aware (uses conversation history)
   - Temporal intelligence (relative dates)

## Example Interactions

### Direct Task Operations

```
User: "Create a task to review the quarterly report"
→ Created task: 'Review quarterly report'

User: "Show me all my high priority tasks"
→ Found 3 tasks

User: "Mark task 5 as completed"
→ Marked task as complete (ID: 5)
```

### Clarification Flow

```
User: "Delete the one with the people"
→ Did you mean to delete the task about organizing the team lunch 
  or the one about reviewing team proposals?

User: "The team lunch"
→ Deleted task (ID: 7)
```

### Context-Aware Updates

```
User: "Create a task to write a report"
→ Created task: 'Write a report'

User: "Make it high priority"
→ Updated task (ID: 8)

User: "It's due tomorrow"
→ Updated task (ID: 8)
```

## Available Task Operations

- **Create**: `create_task(title, description, priority)`
- **Read**: `get_task(task_id)`, `list_tasks(status, priority, limit)`, `list_all_tasks()`
- **Update**: `update_task(task_id, title, description, status, priority, due_date)`
- **Delete**: `delete_task(task_id)`
- **Complete**: `complete_task(task_id)`, `mark_complete(task_id)`

## Development

### Running Tests

```bash
# Run linter
uv run ruff check .

# Format code
uv run ruff format .
```

### Adding Dependencies

```bash
# Add a new dependency
uv add package_name

# Remove a dependency
uv remove package_name
```

### Notebooks

Experimental notebooks are in the `rough/` directory:
- `PJ_01_Create_Task_Models_and_Tools.ipynb` - Task models and CRUD
- `PJ_02_Pydantic_Ai_Agents.ipynb` - Pydantic AI experiments
- `PJ_03_Agents_From_Scratch.ipynb` - Original agent implementation

## Technical Details

### Database

- **Engine**: SQLite
- **ORM**: SQLModel (Pydantic + SQLAlchemy)
- **Location**: `data/milo.db`

### Logging

- **Library**: Loguru
- **Location**: `logs/`
- **Features**: Structured logging with traceback support

### AI Model

- **Provider**: OpenAI
- **Default Model**: gpt-4o-mini
- **Features**: Function calling, structured outputs

## Configuration

All configuration is managed through environment variables:

```env
# Required
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Optional (auto-detected)
PROJECT_ROOT_DIR=/path/to/milo
```

## Contributing

1. Follow the existing code structure
2. Add logging to all functions
3. Use traceback.format_exc() for error logging
4. Use `uv` for dependency management
5. Run linter before committing

## License

[Add your license here]

## Acknowledgments

Built with:
- OpenAI API
- FastAPI
- SQLModel
- Pydantic
- Loguru

