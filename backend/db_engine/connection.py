"""PostgreSQL connection and data-access functions."""

import pandas as pd
import psycopg2

from backend.config import (
    INFRA_POSTGRES_DBNAME,
    INFRA_POSTGRES_HOST,
    INFRA_POSTGRES_PASS,
    INFRA_POSTGRES_USER,
)
from backend.db_engine.queries import PLAN_QUERY, PLAN_STATUS_QUERY


def get_connection():
    return psycopg2.connect(
        host=INFRA_POSTGRES_HOST,
        dbname=INFRA_POSTGRES_DBNAME,
        user=INFRA_POSTGRES_USER,
        password=INFRA_POSTGRES_PASS,
        connect_timeout=8,
    )


def load_plan_management_data():
    """Load active plans and workflow statuses from PostgreSQL."""
    connection = get_connection()
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(PLAN_QUERY)
                plan_rows = cursor.fetchall()
                cursor.execute(PLAN_STATUS_QUERY)
                status_rows = cursor.fetchall()
    finally:
        connection.close()

    plans = pd.DataFrame(
        plan_rows, columns=["Plan ID", "DP", "TPA", "Plan category", "created_on"]
    )
    plans["Created"] = pd.to_datetime(plans["created_on"], unit="ms", errors="coerce")

    statuses = pd.DataFrame(
        status_rows,
        columns=[
            "TPA", "Plan ID", "Prior document provider", "Plan category",
            "Stage", "Plan status", "last_updated_at",
        ],
    )
    statuses["Last updated"] = pd.to_datetime(
        statuses["last_updated_at"], unit="ms", errors="coerce"
    )
    return plans, statuses
