"""
Dagster definitions for monitoring and orchestrating the trading engine.

Jobs:
- Health check sensor: Monitors trading-engine service, restarts if down
- D1 sync job: Pushes trades/positions to D1 for dashboard

To add to Dagster workspace, add to /opt/dagster/dagster_home/workspace.yaml:

    - python_file:
        relative_path: /mnt/c/Users/emily/Documents/GitHub/get-money-get-paid/realtime/dagster_definitions/definitions.py
        location_name: trading_engine
"""
import subprocess
import logging

from dagster import (
    Definitions,
    ScheduleDefinition,
    sensor,
    job,
    op,
    RunRequest,
    SensorEvaluationContext,
    OpExecutionContext,
)

log = logging.getLogger(__name__)


# ============================================================================
# Health Monitoring
# ============================================================================

def is_service_running(service_name: str) -> bool:
    """Check if a systemd service is running"""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() == "active"
    except Exception as e:
        log.error(f"Failed to check service status: {e}")
        return False


def restart_service(service_name: str):
    """Restart a systemd service"""
    try:
        subprocess.run(["sudo", "systemctl", "restart", service_name], check=True)
        log.info(f"Restarted service: {service_name}")
    except Exception as e:
        log.error(f"Failed to restart service: {e}")


@sensor(minimum_interval_seconds=60)
def trading_engine_health_sensor(context: SensorEvaluationContext):
    """
    Monitor trading-engine service health.
    Restarts the service if it's not running during market hours.
    """
    # TODO: Add market hours check
    service_name = "trading-engine"

    if not is_service_running(service_name):
        context.log.warning(f"Service {service_name} is not running, restarting...")
        restart_service(service_name)
        # Could yield a run request to trigger an alert job here


# ============================================================================
# D1 Sync (placeholder - implement when needed)
# ============================================================================

@op
def sync_trades_to_d1(context: OpExecutionContext):
    """Sync trades from local Postgres to D1"""
    context.log.info("Syncing trades to D1...")
    # TODO: Implement
    # 1. Query local Postgres for trades since last sync
    # 2. POST to https://stonks.emilycogsdill.com/api/sync/trades
    context.log.info("Trade sync complete")


@op
def sync_positions_to_d1(context: OpExecutionContext):
    """Sync positions from local Postgres to D1"""
    context.log.info("Syncing positions to D1...")
    # TODO: Implement
    context.log.info("Position sync complete")


@op
def sync_snapshots_to_d1(context: OpExecutionContext):
    """Sync equity snapshots to D1"""
    context.log.info("Syncing snapshots to D1...")
    # TODO: Implement
    context.log.info("Snapshot sync complete")


@job
def sync_to_d1_job():
    """Push local data to D1 for dashboard"""
    sync_trades_to_d1()
    sync_positions_to_d1()
    sync_snapshots_to_d1()


# Every 5 minutes during market hours
sync_schedule = ScheduleDefinition(
    job=sync_to_d1_job,
    cron_schedule="*/5 9-16 * * 1-5",  # Every 5 min, 9am-4pm, Mon-Fri
)


# ============================================================================
# Definitions Export
# ============================================================================

defs = Definitions(
    sensors=[trading_engine_health_sensor],
    jobs=[sync_to_d1_job],
    schedules=[sync_schedule],
)
