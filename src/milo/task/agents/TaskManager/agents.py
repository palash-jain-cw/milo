from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIModel
from milo.core.config import settings
from milo.task.agents.TaskManager.prompts import intent_classifier_system_prompt
from milo.task.agents.TaskManager.models import MultiIntentResult, Action, Intent


# Create a PydanticAI instance
_model_name = settings.OPENAI_MODEL_SMALL
_model = OpenAIModel(_model_name)
intent_classifier_agent = Agent(
    _model,
    system_prompt=intent_classifier_system_prompt,
    output_type=MultiIntentResult,
    output_retries=3,
)


@intent_classifier_agent.output_validator
def validate_result(
    ctx: RunContext[None], result: MultiIntentResult
) -> MultiIntentResult:
    for sequence in result.sequences:
        for intent in sequence.intents:
            if intent.action not in [
                Action.CREATE_TASK,
                Action.UPDATE_TASK,
                Action.DELETE_TASK,
                Action.GET_TASK,
                Action.LIST_TASKS,
                Action.INVALID,
            ]:
                raise ModelRetry(
                    f"Invalid action. Please choose from `{Action.CREATE_TASK}`, `{Action.UPDATE_TASK}`, `{Action.DELETE_TASK}`, `{Action.GET_TASK}`, `{Action.LIST_TASKS}` and `{Action.INVALID}`"
                )
            if intent.confidence < 0.5:
                raise ModelRetry(
                    f"Low confidence. Please choose from `{Action.CREATE_TASK}`, `{Action.UPDATE_TASK}`, `{Action.DELETE_TASK}`, `{Action.GET_TASK}`, `{Action.LIST_TASKS}` and `{Action.INVALID}`"
                )

    return result
