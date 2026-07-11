from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class WarningRules:
    min_attendance_percentage: float
    min_contest_participation_percentage: float
    max_warnings_before_escalation: int


class WarningRulesRepositoryPort(ABC):

    @abstractmethod
    def get_rules(self) -> WarningRules:
        """
        Returns current warning threshold configuration.
        Returns sensible defaults if no rules have been configured yet.
        """
        ...

    @abstractmethod
    def save_rules(self, rules: WarningRules) -> WarningRules:
        """Update the warning rules configuration."""
        ...