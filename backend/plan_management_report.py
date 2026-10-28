from datetime import date

import pandas as pd
import streamlit as st

from backend.db_engine.connection import load_plan_management_data


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
        period_mode = st.selectbox(
            "Reporting period",
            ["Overall", "Monthly", "Quarterly", "Custom range"],
            key="pm_period_mode",
        )

        if period_mode == "Overall":
            range_plans = tpa_plans
            period_label = "overall"
        elif period_mode == "Monthly":
            available_months = (
                tpa_plans["Created"].dropna().dt.to_period("M").astype(str).unique().tolist()
            )
            month_options = sorted(available_months, reverse=True) or [
                date.today().strftime("%Y-%m")
            ]
            selected_month = st.selectbox(
                "Month", month_options, key="pm_selected_month"
            )
            month_period = pd.Period(selected_month, freq="M")
            range_plans = tpa_plans[
                tpa_plans["Created"].dt.to_period("M") == month_period
            ]
            period_label = month_period.strftime("%B %Y")
        elif period_mode == "Quarterly":
            available_quarters = (
                tpa_plans["Created"].dropna().dt.to_period("Q").unique().tolist()
            )
            quarter_options = sorted(available_quarters, reverse=True) or [
                pd.Period(date.today(), freq="Q")
            ]
            quarter_labels = {
                f"{quarter.year} Q{quarter.quarter}": quarter
                for quarter in quarter_options
            }
            selected_quarter_label = st.selectbox(
                "Quarter", list(quarter_labels), key="pm_selected_quarter"
            )
            quarter_period = quarter_labels[selected_quarter_label]
            range_plans = tpa_plans[
                tpa_plans["Created"].dt.to_period("Q") == quarter_period
            ]
            period_label = selected_quarter_label
        else:
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
            period_label = (
                f"{range_start:%b %d, %Y} to {range_end:%b %d, %Y}"
                if range_start <= range_end
                else "custom range (start date is after end date)"
            )
        startup = range_plans[range_plans["Plan category"] == "START_UP_PLAN"]
        takeover = range_plans[range_plans["Plan category"] == "TAKEOVER_PLAN"]
        this_year = tpa_plans[tpa_plans["Created"].dt.year == current_year]

        st.subheader(f"Plan counts for selected TPA · {period_label}")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Plans", len(range_plans))
        k2.metric("Startup Plans", len(startup))
        k3.metric("Takeover Plans", len(takeover))
        k4.metric("Plans This Year", len(this_year))

        st.subheader(f"Plans by DP for selected TPA · {period_label}")
        st.dataframe(
            range_plans.groupby("DP", dropna=False)
            .size()
            .rename("Plan count")
            .reset_index(),
            hide_index=True,
            width="stretch",
        )
        st.subheader(f"Plans created · {period_label}")
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
