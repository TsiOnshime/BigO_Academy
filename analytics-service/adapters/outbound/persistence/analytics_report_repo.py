from uuid import UUID
from typing import Optional

from domain.models import AnalyticsReport
from domain.enums import ReportType
from application.ports.outbound.analytics_report_repository import (
    AnalyticsReportRepositoryPort,
)
from core.models import AnalyticsReportModel


class DjangoAnalyticsReportRepository(AnalyticsReportRepositoryPort):

    def _to_domain(self, orm: AnalyticsReportModel) -> AnalyticsReport:
        return AnalyticsReport(
            id=orm.id,
            report_type=ReportType(orm.report_type),
            generated_at=orm.generated_at,
            data=orm.data,
        )

    def save(self, report: AnalyticsReport) -> AnalyticsReport:
        orm, _ = AnalyticsReportModel.objects.update_or_create(
            id=report.id,
            defaults={
                "report_type": report.report_type.value,
                "data": report.data,
            },
        )
        return self._to_domain(orm)

    def find_by_id(
        self,
        report_id: UUID,
    ) -> Optional[AnalyticsReport]:
        try:
            return self._to_domain(
                AnalyticsReportModel.objects.get(id=report_id)
            )
        except AnalyticsReportModel.DoesNotExist:
            return None