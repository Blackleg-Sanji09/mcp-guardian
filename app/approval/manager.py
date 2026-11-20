import asyncio
from collections.abc import Callable

from app.approval.models import ApprovalRequest, ApprovalStatus


class ApprovalManager:
    def __init__(self) -> None:
        self.pending_requests: dict[str, ApprovalRequest] = {}
        self.approval_events: dict[str, asyncio.Event] = {}
        self.timeout_callbacks: dict[str, list[Callable[[], None]]] = {}

    def create_request(
        self,
        tool_name: str,
        arguments: dict,
    ) -> ApprovalRequest:
        request = ApprovalRequest(
            tool_name=tool_name,
            arguments=arguments,
        )

        self.pending_requests[request.request_id] = request
        self.approval_events[request.request_id] = asyncio.Event()
        self.timeout_callbacks[request.request_id] = []

        return request

    def approve_request(self, request_id: str) -> ApprovalRequest:
        request = self._get_pending_request(request_id)

        request.status = ApprovalStatus.APPROVED
        request.reason = "Approved by user through MCP Guardian."

        self.approval_events[request_id].set()

        return request

    def block_request(
        self,
        request_id: str,
        reason: str = "Blocked by user through MCP Guardian.",
    ) -> ApprovalRequest:
        request = self._get_pending_request(request_id)

        request.status = ApprovalStatus.BLOCKED
        request.reason = reason

        self.approval_events[request_id].set()

        return request

    def register_timeout_callback(
        self,
        request_id: str,
        callback: Callable[[], None],
    ) -> None:
        if request_id not in self.pending_requests:
            raise ValueError(f"Approval request not found: {request_id}")

        self.timeout_callbacks[request_id].append(callback)

    async def wait_for_decision(
        self,
        request_id: str,
        timeout: float = 120,
    ) -> ApprovalRequest:
        request = self.pending_requests.get(request_id)

        if request is None:
            raise ValueError(f"Approval request not found: {request_id}")

        event = self.approval_events[request_id]

        try:
            await asyncio.wait_for(
                event.wait(),
                timeout=timeout,
            )

        except asyncio.TimeoutError:
            if request.status == ApprovalStatus.PENDING:
                request.status = ApprovalStatus.TIMED_OUT
                request.reason = (
                    f"Approval timed out after {timeout} seconds."
                )

                callbacks = self.timeout_callbacks.get(request_id, [])

                for callback in callbacks:
                    try:
                        callback()
                    except Exception as error:
                        print(f"Timeout callback failed: {error}")

        return request

    def cleanup_request(self, request_id: str) -> None:
        self.pending_requests.pop(request_id, None)
        self.approval_events.pop(request_id, None)
        self.timeout_callbacks.pop(request_id, None)

    def _get_pending_request(self, request_id: str) -> ApprovalRequest:
        request = self.pending_requests.get(request_id)

        if request is None:
            raise ValueError(f"Approval request not found: {request_id}")

        if request.status != ApprovalStatus.PENDING:
            raise ValueError(
                f"Request {request_id} has already been decided: "
                f"{request.status.value}"
            )

        return request