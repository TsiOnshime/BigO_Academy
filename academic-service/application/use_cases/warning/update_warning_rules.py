from dataclasses import dataclass
from typing import Optional

from application.ports.outbound.warning_rules_repository import (
    WarningRulesRepositoryPort,
    WarningRules,
)


@dataclass
class UpdateWarningRulesCommand:
    min_attendance_percentage: Optional[float] = None
    min_contest_participation_percentage: Optional[float] = None
    max_warnings_before_escalation: Optional[int] = None


class UpdateWarningRulesUseCase:

    def __init__(self, warning_rules_repository: WarningRulesRepositoryPort):
        self.warning_rules_repository = warning_rules_repository

    def execute(self, command: UpdateWarningRulesCommand) -> WarningRules:

        # Fetch current rules first
        current = self.warning_rules_repository.get_rules()

        # Only update fields that were provided
        updated = WarningRules(
            min_attendance_percentage=(
                command.min_attendance_percentage
                if command.min_attendance_percentage is not None
                else current.min_attendance_percentage
            ),
            min_contest_participation_percentage=(
                command.min_contest_participation_percentage
                if command.min_contest_participation_percentage is not None
                else current.min_contest_participation_percentage
            ),
            max_warnings_before_escalation=(
                command.max_warnings_before_escalation
                if command.max_warnings_before_escalation is not None
                else current.max_warnings_before_escalation
            ),
        )

        return self.warning_rules_repository.save_rules(updated)