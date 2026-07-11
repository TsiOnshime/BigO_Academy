from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from domain.models import Warning
from domain.enums import WarningStatus
from domain.exceptions import (
    WarningNotFoundError,
    WarningAlreadyDismissedError,
)
from application.ports.outbound.warning_repository import WarningRepositoryPort
from application.ports.outbound.event_publisher import EventPublisherPort


@dataclass
class DismissWarningCommand:
    warning_id: UUID
    dismissed_by: UUID     # admin or teacher user_id
    note: str


class DismissWarningUseCase:

    def __init__(
        self,
        warning_repository: WarningRepositoryPort,
        event_publisher: EventPublisherPort,
    ):
        self.warning_repository = warning_repository
        self.event_publisher = event_publisher

    def execute(self, command: DismissWarningCommand) -> Warning:

        warning = self.warning_repository.find_by_id(command.warning_id)
        if warning is None:
            raise WarningNotFoundError(str(command.warning_id))

        # Cannot dismiss an already dismissed warning
        if not warning.is_active():
            raise WarningAlreadyDismissedError(str(command.warning_id))

        warning.status = WarningStatus.DISMISSED
        warning.dismissed_at = datetime.now(timezone.utc)
        warning.dismissed_by = command.dismissed_by
        warning.dismissal_note = command.note

        saved_warning = self.warning_repository.save(warning)

        # Publish event — Analytics tracks improvement metrics
        self.event_publisher.publish_warning_resolved(saved_warning)

        return saved_warning