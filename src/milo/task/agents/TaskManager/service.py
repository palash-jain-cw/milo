from milo.shared.dependencies import get_db_session
from milo.task.models.schema import TaskCreate, Task, TaskUpdate
from uuid import UUID
from typing import List
from milo.task.models.orm import Task as TaskORM
from sqlalchemy import select
from milo.task.agents.TaskManager.agents import intent_classifier_agent
from milo.task.agents.TaskManager.models import (
    MultiIntentResult,
    Intent,
    IntentSequence,
    Action,
)
from langgraph.types import Send
from typing_extensions import TypedDict


class OverallState(TypedDict):
    user_input: str
    intent_sequences: MultiIntentResult


class SequenceState(TypedDict):
    intent_sequence: IntentSequence
    index: int


class IntentState(TypedDict):
    intent: Intent


class TaskManagerService:
    def __init__(self) -> None:
        self.db_session = get_db_session()

    async def create_task(self, task: TaskCreate) -> Task:
        task = TaskORM(**task.model_dump())
        self.db_session.add(task)
        await self.db_session.commit()
        return {"result": f"Task created with id {task.id}"}

    async def update_task(self, task: TaskUpdate) -> Task:
        task = await self.db_session.get(TaskORM, task.id)
        update_data = task.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field != "id" and value is not None:
                setattr(task, field, value)
        await self.db_session.commit()
        return {"result": f"Task updated with id {task.id}"}

    async def delete_task(self, task_id: UUID) -> None:
        task = await self.db_session.get(TaskORM, task_id)
        await self.db_session.delete(task)
        await self.db_session.commit()
        return {"result": f"Task deleted with id {task_id}"}

    async def get_task(self, task_id: UUID) -> Task:
        task = await self.db_session.get(TaskORM, task_id)
        return {"result": task.model_dump()}

    async def list_tasks(self, project_id: UUID, user_id: UUID = None) -> List[Task]:
        query = select(TaskORM).where(TaskORM.project_id == project_id)
        if user_id:
            query = query.where(TaskORM.user_id == user_id)
        tasks = await self.db_session.execute(query)
        return {"result": tasks.scalars().all()}

    async def classify_intent(self, state: OverallState) -> MultiIntentResult:
        result = await intent_classifier_agent.run(state["user_input"])
        return result.output.model_dump()

    def map_intent_sequences(self, state: OverallState) -> List[Send]:
        return [
            Send(
                node="sequence_executor",
                args=SequenceState(intent_sequence=intent_sequence, index=0),
            )
            for intent_sequence in state["intent_sequences"].sequences
        ]

    async def intent_executor(self, state: SequenceState) -> List[Send]:
        num_intents = len(state["intent_sequence"].intents)
        if state["index"] > num_intents:
            intent = state["intent_sequence"].intents[state["index"]]
            if intent.action == Action.CREATE_TASK:
                intent.result = await self.create_task(intent)
            elif intent.action == Action.UPDATE_TASK:
                intent.result = await self.update_task(intent)
            elif intent.action == Action.DELETE_TASK:
                intent.result = await self.delete_task(intent)
            elif intent.action == Action.LIST_TASKS:
                intent.result = await self.list_tasks(intent)
            elif intent.action == Action.GET_TASK:
                intent.result = await self.get_task(intent)
        else:
            return "END"
