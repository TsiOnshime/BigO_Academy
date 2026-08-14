from django.db import models


class WarningRulesConfig(models.Model):
    """
    Singleton config row (id fixed to 1 by the DjangoWarningRulesRepository
    adapter) backing WarningRulesRepositoryPort.
    """

    min_attendance_percentage = models.FloatField(default=60.0)
    min_contest_participation_percentage = models.FloatField(default=50.0)
    max_warnings_before_escalation = models.IntegerField(default=3)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        db_table = "warning_rules_config"

    def __str__(self):
        return "Warning Rules Config"