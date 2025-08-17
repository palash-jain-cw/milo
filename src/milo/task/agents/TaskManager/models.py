from pydantic import BaseModel
from enum import Enum
from typing import List, Optional


class Action(str, Enum):
    CREATE_TASK = "createTask"
    UPDATE_TASK = "updateTask"
    DELETE_TASK = "deleteTask"
    GET_TASK = "getTask"
    LIST_TASKS = "listTasks"
    INVALID = "invalid"


class Intent(BaseModel):
    action: Action
    text: str
    confidence: float
    result: Optional[str] = None


class IntentSequence(BaseModel):
    intents: List[Intent]


class MultiIntentResult(BaseModel):
    sequences: List[IntentSequence]
