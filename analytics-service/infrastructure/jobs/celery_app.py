from celery import Celery
from django.conf import settings

app = Celery("analytics")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task
def refresh_leaderboard_task():
    """
    Runs every 5 minutes.
    Recalculates all rankings and updates the leaderboard table.
    """
    from infrastructure.config.dependencies import (
        get_refresh_leaderboard_use_case,
    )

    use_case = get_refresh_leaderboard_use_case()
    use_case.execute()


@app.task
def snapshot_historical_metrics_task():
    """
    Runs daily.
    Takes a snapshot of all student analytics for trend charts.
    """
    from infrastructure.config.dependencies import (
        get_snapshot_historical_metrics_use_case,
    )

    use_case = get_snapshot_historical_metrics_use_case()
    use_case.execute()