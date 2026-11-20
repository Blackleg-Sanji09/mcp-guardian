import asyncio

import pytest

from app.approval.manager import ApprovalManager
from app.approval.models import ApprovalStatus


def test_create_request():
    manager = ApprovalManager()

    request = manager.create_request(
        tool_name="calculate_sum",
        arguments={"a": 10, "b": 20},
    )

    assert request.tool_name == "calculate_sum"
    assert request.arguments == {"a": 10, "b": 20}
    assert request.status == ApprovalStatus.PENDING

    assert request.request_id in manager.pending_requests
    assert request.request_id in manager.approval_events


def test_approve_request():
    manager = ApprovalManager()

    request = manager.create_request(
        tool_name="calculate_sum",
        arguments={"a": 10, "b": 20},
    )

    manager.approve_request(request.request_id)

    assert request.status == ApprovalStatus.APPROVED
    assert request.reason == "Approved by user through MCP Guardian."

    assert manager.approval_events[request.request_id].is_set()


def test_block_request():
    manager = ApprovalManager()

    request = manager.create_request(
        tool_name="calculate_sum",
        arguments={"a": 10, "b": 20},
    )

    manager.block_request(request.request_id)

    assert request.status == ApprovalStatus.BLOCKED
    assert request.reason == "Blocked by user through MCP Guardian."

    assert manager.approval_events[request.request_id].is_set()


def test_block_request_with_custom_reason():
    manager = ApprovalManager()

    request = manager.create_request(
        tool_name="get_system_info",
        arguments={},
    )

    custom_reason = "Blocked by security policy."

    manager.block_request(
        request.request_id,
        custom_reason,
    )

    assert request.status == ApprovalStatus.BLOCKED
    assert request.reason == custom_reason


def test_approval_timeout():
    manager = ApprovalManager()

    request = manager.create_request(
        tool_name="calculate_sum",
        arguments={"a": 10, "b": 20},
    )

    async def run_timeout():
        return await manager.wait_for_decision(
            request.request_id,
            timeout=0.01,
        )

    result = asyncio.run(run_timeout())

    assert result.status == ApprovalStatus.TIMED_OUT
    assert "timed out" in result.reason.lower()


def test_wait_for_approval():
    manager = ApprovalManager()

    request = manager.create_request(
        tool_name="calculate_sum",
        arguments={"a": 10, "b": 20},
    )

    async def run_approval():
        async def approve_later():
            await asyncio.sleep(0.01)
            manager.approve_request(request.request_id)

        approval_task = asyncio.create_task(approve_later())

        result = await manager.wait_for_decision(
            request.request_id,
            timeout=1,
        )

        await approval_task

        return result

    result = asyncio.run(run_approval())

    assert result.status == ApprovalStatus.APPROVED


def test_cleanup_request():
    manager = ApprovalManager()

    request = manager.create_request(
        tool_name="calculate_sum",
        arguments={"a": 10, "b": 20},
    )

    request_id = request.request_id

    manager.cleanup_request(request_id)

    assert request_id not in manager.pending_requests
    assert request_id not in manager.approval_events


def test_duplicate_decision_rejected():
    manager = ApprovalManager()

    request = manager.create_request(
        tool_name="calculate_sum",
        arguments={"a": 10, "b": 20},
    )

    manager.approve_request(request.request_id)

    with pytest.raises(ValueError):
        manager.block_request(request.request_id)


def test_unknown_request_rejected():
    manager = ApprovalManager()

    with pytest.raises(ValueError):
        manager.approve_request("invalid-request-id")