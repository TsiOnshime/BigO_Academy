from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional
from domain.models import AnalyticsReport
from domain.enums import ReportType

class AnalyticsReportRepositoryPort(ABC):
    @abstractmethod
    def save(self, report: AnalyticsReport) -> AnalyticsReport:
        """Save a generated report."""
        ...

    @abstractmethod
    def find_by_id(self, report_id: UUID) -> Optional[AnalyticsReport]:
        """Fetch report by UUID."""
        ...