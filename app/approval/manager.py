import asyncio

from app.approval.models import ApprovalRequest, ApprovalStatus


class ApprovalManager:
    def __init__(self):
        self.pending_requests: dict[str, ApprovalRequest] = {}
        self.approval_events: dict[str, asyncio.Event] = {}

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

        return request

    def approve_request(self, request_id: str) -> ApprovalRequest:
        request = self._get_pending_request(request_id)

        request.status = ApprovalStatus.APPROVED
        self.approval_events[request_id].set()

        return request

    def block_request(self, request_id: str) -> ApprovalRequest:
        request = self._get_pending_request(request_id)

        request.status = ApprovalStatus.BLOCKED
        self.approval_events[request_id].set()

        return request

    async def wait_for_decision(self, request_id: str) -> ApprovalRequest:
        request = self.pending_requests.get(request_id)

        if request is None:
            raise ValueError(f"Approval request not found: {request_id}")

        event = self.approval_events[request_id]

        await event.wait()

        return request

    def _get_pending_request(self, request_id: str) -> ApprovalRequest:
        request = self.pending_requests.get(request_id)

        if request is None:
            raise ValueError(f"Approval request not found: {request_id}")

        if request.status != ApprovalStatus.PENDING:
            raise ValueError(
                f"Request {request_id} has already been decided: {request.status.value}"
            )

        return request