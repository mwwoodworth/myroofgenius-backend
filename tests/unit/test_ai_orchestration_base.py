import pytest

from ai_orchestration.core import Agent


@pytest.mark.asyncio
async def test_base_agent_execute_action_requires_override():
    agent = Agent("test", "testing", ["noop"])

    with pytest.raises(RuntimeError, match="not implemented"):
        await agent._execute_action({"action": "noop"})
