"""Streamlit UI for Milo Task Manager."""

import streamlit as st
import httpx
from datetime import datetime
from typing import List, Dict

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="Milo - AI Task Manager",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .task-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid;
        margin-bottom: 1rem;
        background-color: #fafafa;
    }
    .task-high {
        border-left-color: #f44336;
    }
    .task-medium {
        border-left-color: #ff9800;
    }
    .task-low {
        border-left-color: #4caf50;
    }
    .stButton>button {
        width: 100%;
    }
    /* Improve chat message spacing */
    .stChatMessage {
        padding: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Initialize session state
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "awaiting_clarification" not in st.session_state:
    st.session_state.awaiting_clarification = False


def call_api(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Call the FastAPI backend."""
    url = f"{API_BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = httpx.get(url, timeout=30.0)
        elif method == "POST":
            response = httpx.post(url, json=data, timeout=30.0)
        elif method == "DELETE":
            response = httpx.delete(url, timeout=30.0)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()

    except httpx.HTTPError as e:
        st.error(f"API Error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def send_message(message: str, is_clarification: bool = False):
    """Send a message to the chat API."""
    endpoint = "/chat/clarify" if is_clarification else "/chat"

    data = {
        "message": message,
        "conversation_history": st.session_state.conversation_history,
    }

    response = call_api(endpoint, method="POST", data=data)

    if response:
        # Update conversation history
        st.session_state.conversation_history = response["conversation_history"]

        # Add messages to display
        st.session_state.messages.append({"role": "user", "content": message})
        st.session_state.messages.append(
            {"role": "assistant", "content": response["response"]}
        )

        # Check if clarification is needed
        st.session_state.awaiting_clarification = response.get(
            "needs_user_input", False
        )

        return response
    return None


def get_tasks(status: str = None, priority: str = None) -> List[Dict]:
    """Get tasks from the API."""
    params = []
    if status:
        params.append(f"status={status}")
    if priority:
        params.append(f"priority={priority}")

    query_string = "?" + "&".join(params) if params else ""
    response = call_api(f"/tasks{query_string}")

    return response if response else []


def format_task_card(task: Dict):
    """Format a task as a card."""
    priority_class = f"task-{task['priority']}"

    # Status emoji
    status_emoji = {
        "pending": "⏳",
        "in_progress": "🔄",
        "completed": "✅",
        "cancelled": "❌",
    }

    # Priority badge
    priority_badge = {
        "high": "🔴 HIGH",
        "medium": "🟡 MEDIUM",
        "low": "🟢 LOW",
    }

    due_date_str = ""
    if task.get("due_date"):
        due_date = datetime.fromisoformat(task["due_date"])
        due_date_str = f"📅 Due: {due_date.strftime('%b %d, %Y')}"

    st.markdown(
        f"""
    <div class="task-card {priority_class}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>{status_emoji.get(task["status"], "📋")} {task["title"]}</strong>
                <br>
                <small>{priority_badge.get(task["priority"], "MEDIUM")} | {task["status"].replace("_", " ").title()}</small>
            </div>
            <div style="text-align: right;">
                <small>{due_date_str}</small>
            </div>
        </div>
        {f"<p style='margin-top: 0.5rem; color: #666;'>{task['description']}</p>" if task.get("description") else ""}
    </div>
    """,
        unsafe_allow_html=True,
    )


# Main UI
def main():
    # Header
    st.markdown('<div class="main-header">🤖 Milo</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Your AI-Powered Task Manager</div>',
        unsafe_allow_html=True,
    )

    # Sidebar
    with st.sidebar:
        st.header("📊 Task Overview")

        # Get all tasks
        all_tasks = get_tasks()

        # Initialize filter variables with defaults
        status_filter = "All"
        priority_filter = "All"

        if all_tasks:
            # Count by status
            status_counts = {}
            for task in all_tasks:
                status = task["status"]
                status_counts[status] = status_counts.get(status, 0) + 1

            # Display metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Tasks", len(all_tasks))
                st.metric("Pending", status_counts.get("pending", 0))
            with col2:
                st.metric("In Progress", status_counts.get("in_progress", 0))
                st.metric("Completed", status_counts.get("completed", 0))

            st.divider()

            # Filter options
            st.subheader("🔍 Filters")
            status_filter = st.selectbox(
                "Status",
                ["All", "pending", "in_progress", "completed", "cancelled"],
                key="status_filter",
            )
            priority_filter = st.selectbox(
                "Priority", ["All", "high", "medium", "low"], key="priority_filter"
            )

            if st.button("Apply Filters", use_container_width=True):
                st.rerun()

        else:
            st.info("No tasks yet. Start by creating one!")

        st.divider()

        # Quick actions
        st.subheader("⚡ Quick Actions")
        if st.button("📋 Show All Tasks", use_container_width=True):
            send_message("Show me all my tasks")
            st.rerun()

        if st.button("🔥 High Priority", use_container_width=True):
            send_message("Show me my high priority tasks")
            st.rerun()

        if st.button("📅 Due Soon", use_container_width=True):
            send_message("What tasks are due this week?")
            st.rerun()

        if st.button("🔄 Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_history = []
            st.session_state.awaiting_clarification = False
            st.rerun()

    # Main content area with tabs
    tab1, tab2 = st.tabs(["💬 Chat", "📋 Tasks"])

    with tab1:
        # Chat interface
        st.subheader("Chat with Milo")

        # Show clarification notice if needed
        if st.session_state.awaiting_clarification:
            st.info(
                "💡 Milo needs clarification. Please provide more details in your next message."
            )

        # Create a container for chat messages with fixed height
        chat_container = st.container(height=500)

        # Display chat messages using Streamlit's native chat components
        with chat_container:
            for message in st.session_state.messages:
                role = message["role"]
                content = message["content"]

                # Use native chat message component
                with st.chat_message(
                    role, avatar="🤖" if role == "assistant" else "👤"
                ):
                    st.markdown(content)

        # Chat input using Streamlit's native chat input (stays at bottom)
        if prompt := st.chat_input("Type your message here...", key="chat_input"):
            # Send the message
            send_message(
                prompt, is_clarification=st.session_state.awaiting_clarification
            )
            st.rerun()

    with tab2:
        # Task list view
        st.subheader("All Tasks")

        # Apply filters
        filtered_tasks = all_tasks
        if status_filter != "All":
            filtered_tasks = [t for t in filtered_tasks if t["status"] == status_filter]
        if priority_filter != "All":
            filtered_tasks = [
                t for t in filtered_tasks if t["priority"] == priority_filter
            ]

        if filtered_tasks:
            # Group by status
            status_groups = {}
            for task in filtered_tasks:
                status = task["status"]
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(task)

            # Display by status
            for status in ["in_progress", "pending", "completed", "cancelled"]:
                if status in status_groups:
                    st.markdown(f"### {status.replace('_', ' ').title()}")
                    for task in status_groups[status]:
                        format_task_card(task)
        else:
            st.info("No tasks found. Try adjusting your filters or create a new task!")


if __name__ == "__main__":
    main()
