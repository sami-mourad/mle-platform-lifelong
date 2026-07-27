from __future__ import annotations

from dagster import Definitions, ScheduleDefinition, define_asset_job, load_assets_from_modules

from mle_platform.orchestration.assets import dummy_imbalance

all_assets = load_assets_from_modules([dummy_imbalance])
full_retrain_job = define_asset_job(name="full_retrain_job", selection="*")
daily_retrain_schedule = ScheduleDefinition(
    job=full_retrain_job,
    cron_schedule="0 2 * * *",
    execution_timezone="UTC",
)

defs = Definitions(
    assets=all_assets,
    jobs=[full_retrain_job],
    schedules=[daily_retrain_schedule],
)
