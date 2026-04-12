import os
from pathlib import Path

from airflow.sdk import dag
from cosmos import DbtTaskGroup, ProfileConfig, ProjectConfig, RenderConfig


DBT_PROJECT_PATH = f"{os.environ['AIRFLOW_HOME']}/include/event_analytics_dbt"

profile_config = ProfileConfig(
    profile_name="event_analytics",
    target_name="dev",
    profiles_yml_filepath=Path(os.path.join(DBT_PROJECT_PATH, "profiles.yml")),
)


@dag(
    dag_id="dbt_daily",
    schedule="@daily",
    tags=["dbt", "marts"],
    default_args={"owner": "jinjik19", "retries": 3},
    description="Daily run dbt command for build marts models",
)
def dbt_daily() -> None:
    DbtTaskGroup(
        group_id="create_marts",
        project_config=ProjectConfig(DBT_PROJECT_PATH),
        profile_config=profile_config,
        render_config=RenderConfig(enable_cache=False),
    )


dbt_daily()
