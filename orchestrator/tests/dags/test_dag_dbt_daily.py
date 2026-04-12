import pytest
from airflow.models import DagBag

from tests.conftest import suppress_logging


DAG_ID = "dbt_daily"


@pytest.fixture(scope="module")
def dag():
    with suppress_logging("airflow"):
        dag_bag = DagBag(include_examples=False)
    return dag_bag.dags.get(DAG_ID)


def test_dag_exists(dag):
    assert dag is not None, f"DAG '{DAG_ID}' not found in DagBag"


def test_dag_schedule(dag):
    assert dag.schedule_interval == "@daily", (
        f"Expected '@daily', got '{dag.schedule_interval}'"
    )


def test_dag_tags(dag):
    assert "dbt" in dag.tags, "Tag 'dbt' is missing"
    assert "marts" in dag.tags, "Tag 'marts' is missing"


def test_dag_retries(dag):
    retries = dag.default_args.get("retries", 0)
    assert retries >= 2, f"retries must be >= 2, got {retries}"
