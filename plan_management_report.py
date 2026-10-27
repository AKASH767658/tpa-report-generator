from datetime import date

import pandas as pd
import psycopg2
import streamlit as st

from config import (
    INFRA_POSTGRES_DBNAME,
    INFRA_POSTGRES_HOST,
    INFRA_POSTGRES_PASS,
    INFRA_POSTGRES_USER,
)


PLAN_QUERY = """
    SELECT p.id AS plan_id,
           p.document_provider AS dp,
           p.user_group_id AS tpa,
           s.plan_record_type,
           p.created_on
    FROM plan p
    LEFT JOIN plan_setup s ON s.plan_id = p.id
    WHERE p.is_active = TRUE
"""

PLAN_STATUS_QUERY = """
    SELECT p.user_group_id AS tpa,
           p.id AS plan_id,
           p.additional_info->>'PriorDocumentProvider' AS prior_dp,
           s.plan_record_type,
           st.name AS stage,
           st.status AS plan_status,
           st.last_updated_at
    FROM plan p
    LEFT JOIN plan_setup s ON s.plan_id = p.id
    JOIN stage st ON st.plan_id = p.id
    WHERE p.is_active = TRUE
"""


def load_plan_management_data():
    """Load saved plans and their workflow stage statuses from PostgreSQL."""
    connection = psycopg2.connect(
        host=INFRA_POSTGRES_HOST,
        dbname=INFRA_POSTGRES_DBNAME,
        user=INFRA_POSTGRES_USER,
        password=INFRA_POSTGRES_PASS,
        connect_timeout=8,
    )
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
        plan_rows,
        columns=["Plan ID", "DP", "TPA", "Plan category", "created_on"],
    )
    plans["Created"] = pd.to_datetime(plans["created_on"], unit="ms", errors="coerce")

    statuses = pd.DataFrame(
        status_rows,
        columns=["TPA", "Plan ID", "Prior document provider", "Plan category", "Stage", "Plan status", "last_updated_at"],
    )
    statuses["Last updated"] = pd.to_datetime(
        statuses["last_updated_at"], unit="ms", errors="coerce"
    )
    return plans, statuses


def render_plan_management_report():
    """Render a TPA-specific report with plan counts and workflow status."""
    st.header("Plan Management Report")
    st.caption("Total, startup, and takeover counts follow the selected TPA and date range. Plans This Year shows the full current year for the selected TPA.")

    try:
        plan_data, status_data = load_plan_management_data()
        tpa_options = sorted(plan_data["TPA"].dropna().astype(str).unique().tolist())
        if not tpa_options:
            st.info("No active plans with a TPA were found.")
            return

        selected_tpa = st.selectbox("Select TPA", tpa_options, key="pm_selected_tpa")
        tpa_plans = plan_data[plan_data["TPA"] == selected_tpa]

        st.subheader("Plan Status by TPA and Plan ID")
        tpa_status = status_data[status_data["TPA"] == selected_tpa]
        plan_ids = sorted(tpa_status["Plan ID"].dropna().astype(int).unique().tolist())
        if plan_ids:
            selected_plan_id = st.selectbox(
                "Plan ID", plan_ids, key="pm_selected_plan_id"
            )
            selected_status = tpa_status[tpa_status["Plan ID"] == selected_plan_id]
            st.dataframe(
                selected_status[
                    ["TPA", "Plan ID", "Prior document provider", "Plan category", "Stage", "Plan status", "Last updated"]
                ],
                hide_index=True,
                width="stretch",
            )
        else:
            st.info("No workflow status records were found for this TPA.")

        current_year = date.today().year
        date_col1, date_col2 = st.columns(2)
        with date_col1:
            range_start = st.date_input(
                "Created from", value=date(current_year, 1, 1), key="pm_created_from"
            )
        with date_col2:
            range_end = st.date_input(
                "Created through", value=date.today(), key="pm_created_through"
            )

        range_plans = (
            tpa_plans[
                (tpa_plans["Created"].dt.date >= range_start)
                & (tpa_plans["Created"].dt.date <= range_end)
            ]
            if range_start <= range_end
            else tpa_plans.iloc[0:0]
        )
        startup = range_plans[range_plans["Plan category"] == "START_UP_PLAN"]
        takeover = range_plans[range_plans["Plan category"] == "TAKEOVER_PLAN"]
        this_year = tpa_plans[tpa_plans["Created"].dt.year == current_year]

        st.subheader("Plan counts for selected TPA and date range")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Plans", len(range_plans))
        k2.metric("Startup Plans", len(startup))
        k3.metric("Takeover Plans", len(takeover))
        k4.metric("Plans This Year", len(this_year))

        st.subheader("Plans by DP for selected TPA and date range")
        st.dataframe(
            range_plans.groupby("DP", dropna=False)
            .size()
            .rename("Plan count")
            .reset_index(),
            hide_index=True,
            width="stretch",
        )
        st.subheader("Plans created in selected date range")
        st.dataframe(
            range_plans[["Plan ID", "DP", "TPA", "Plan category", "Created"]],
            hide_index=True,
            width="stretch",
        )
    except Exception as error:
        st.error(
            "Could not load Plan Management data. "
            "Check the database connection settings and access."
        )
        st.caption(type(error).__name__)