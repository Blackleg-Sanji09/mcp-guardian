from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    BLOCKED = "blocked"
    TIMED_OUT = "timed_out"


@dataclass
class ApprovalRequest:
    tool_name: str
    arguments: dict[str, Any]
    request_id: str = field(default_factory=lambda: str(uuid4()))
    status: ApprovalStatus = ApprovalStatus.PENDING
    reason: str | None = None