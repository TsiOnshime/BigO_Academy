from application.ports.outbound.warning_rules_repository import (
    WarningRulesRepositoryPort,
    WarningRules,
)


class GetWarningRulesUseCase:

    def __init__(self, warning_rules_repository: WarningRulesRepositoryPort):
        self.warning_rules_repository = warning_rules_repository

    def execute(self) -> WarningRules:
        return self.warning_rules_repository.get_rules()