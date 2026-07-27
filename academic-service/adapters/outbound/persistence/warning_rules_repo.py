"""
adapters/outbound/persistence/warning_rules_repo.py — Academic Service

Django ORM implementation of WarningRulesRepositoryPort.

Singleton config row: always id=1, so there's exactly one rules row for
the whole service.
"""
from application.ports.outbound.warning_rules_repository import (
    WarningRules,
    WarningRulesRepositoryPort,
)
from core.models import WarningRulesConfig

SINGLETON_ID = 1


class DjangoWarningRulesRepository(WarningRulesRepositoryPort):

    def get_rules(self) -> WarningRules:
        orm, _ = WarningRulesConfig.objects.get_or_create(
            id=SINGLETON_ID,
            defaults={
                "min_attendance_percentage": 60.0,
                "min_contest_participation_percentage": 50.0,
                "max_warnings_before_escalation": 3,
            },
        )
        return self._to_domain(orm)

    def save_rules(self, rules: WarningRules) -> WarningRules:
        orm, _ = WarningRulesConfig.objects.update_or_create(
            id=SINGLETON_ID,
            defaults={
                "min_attendance_percentage": rules.min_attendance_percentage,
                "min_contest_participation_percentage": rules.min_contest_participation_percentage,
                "max_warnings_before_escalation": rules.max_warnings_before_escalation,
            },
        )
        return self._to_domain(orm)

    # ── Mapping ─────────────────────────────────────────────────────────

    def _to_domain(self, orm: WarningRulesConfig) -> WarningRules:
        return WarningRules(
            min_attendance_percentage=orm.min_attendance_percentage,
            min_contest_participation_percentage=orm.min_contest_participation_percentage,
            max_warnings_before_escalation=orm.max_warnings_before_escalation,
        )