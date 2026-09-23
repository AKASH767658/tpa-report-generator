import base64
import json
import mimetypes
import os
import shutil
from html import escape
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st


BRANDING_DIR = Path("assets") / "branding"
BRANDING_CONFIG_FILE = BRANDING_DIR / "branding.json"
DEFAULT_DOWNLOADABLE_REPORT_COLORS = {
    "navy": "#104866", "teal": "#00BBB4", "teal_light": "#08C8C5",
    "muted": "#49616A", "border": "#D5E4E8", "background": "#FFFFFF",
    "page_background": "#F4FAFA", "card_background": "#FFFFFF",
    "surface_subtle": "#EDF8F8", "grid": "#E5F1F2",
    "chart_secondary": "#104866", "chart_tertiary": "#FF7D59",
    "chart_quaternary": "#FFC857", "shadow": "rgba(16, 72, 102, .08)",
}
DEFAULT_BRANDING = {
    "company_name": "SinglepointAI",
    "product_name": "TPA Go-Live Dashboard",
    "logo_file": "logo.svg",
    "colors": {
        "navy": "#0b2532", "teal": "#087e7b", "muted": "#49616a",
        "border": "#c9dfdc", "background": "#f6f4ed",
    },
    "downloadable_report_colors": DEFAULT_DOWNLOADABLE_REPORT_COLORS,
}


def load_branding():
    """Load branding from assets/branding without requiring code changes."""
    branding = {
        **DEFAULT_BRANDING,
        "colors": DEFAULT_BRANDING["colors"].copy(),
        "downloadable_report_colors": DEFAULT_DOWNLOADABLE_REPORT_COLORS.copy(),
    }
    try:
        with BRANDING_CONFIG_FILE.open(encoding="utf-8") as file:
            configured = json.load(file)
        for key in ("company_name", "product_name", "logo_file"):
            if isinstance(configured.get(key), str) and configured[key].strip():
                branding[key] = configured[key].strip()
        if isinstance(configured.get("colors"), dict):
            for key, value in configured["colors"].items():
                if key in branding["colors"] and isinstance(value, str) and value.strip():
                    branding["colors"][key] = value.strip()
        if isinstance(configured.get("downloadable_report_colors"), dict):
            for key, value in configured["downloadable_report_colors"].items():
                if key in branding["downloadable_report_colors"] and isinstance(value, str) and value.strip():
                    branding["downloadable_report_colors"][key] = value.strip()
    except (OSError, json.JSONDecodeError):
        pass
    return branding


def logo_html(branding, css_class="sp-logo"):
    """Embed the configured logo in both the app and downloadable HTML."""
    logo_path = BRANDING_DIR / branding["logo_file"]
    try:
        logo_bytes = logo_path.read_bytes()
        mime_type = mimetypes.guess_type(logo_path.name)[0] or "image/png"
        encoded = base64.b64encode(logo_bytes).decode("ascii")
        return f'<img class="{css_class}" src="data:{mime_type};base64,{encoded}" alt="{escape(branding["company_name"])} logo">'
    except OSError:
        return '<div class="sp-mark" aria-label="Brand logo"></div>'


def milestone_summary_html(tpa_name, go_live_date, first_plan):
    """Render the compact production-adoption milestone header."""
    has_first_plan = pd.notna(first_plan)
    first_plan_date = first_plan.date() if has_first_plan else None
    duration = (first_plan_date - go_live_date).days if has_first_plan else None
    first_plan_display = first_plan_date.strftime("%d %b %Y") if has_first_plan else "Not yet onboarded"
    duration_display = f"{duration} days" if has_first_plan else "&mdash;"
    duration_caption = "Time to first plan" if has_first_plan else "Awaiting first plan"

    return f'''<section class="sp-milestone-summary" aria-label="Production adoption milestones">
      <div class="sp-tpa-name">{escape(str(tpa_name))}</div>
      <div class="sp-timeline">
        <div class="sp-milestone">
          <div class="sp-milestone-icon" aria-hidden="true">&#128640;</div>
          <div class="sp-milestone-label">Prod Live</div>
          <div class="sp-milestone-date">{go_live_date.strftime("%d %b %Y")}</div>
        </div>
        <div class="sp-timeline-metric">
          <div class="sp-timeline-value">{duration_display}</div>
          <div class="sp-timeline-caption">{duration_caption}</div>
        </div>
        <div class="sp-milestone">
          <div class="sp-milestone-icon" aria-hidden="true">&#128196;</div>
          <div class="sp-milestone-label">First Plan</div>
          <div class="sp-milestone-date">{first_plan_display}</div>
        </div>
      </div>
    </section>'''


BRANDING = load_branding()
COLORS = BRANDING["colors"]
PLAN_TYPE_COLORS = {"Startup": COLORS["navy"], "Takeover": COLORS["teal"], "Other": COLORS["muted"]}

st.set_page_config(page_title=f"{BRANDING['company_name']} | TPA Go-Live", layout="wide")

st.markdown(
    "<style>:root {"
    f" --sp-navy:{COLORS['navy']}; --sp-teal:{COLORS['teal']};"
    f" --sp-muted:{COLORS['muted']}; --sp-border:{COLORS['border']};"
    f" --sp-background:{COLORS['background']}; }}"
    """
    .stApp { background:var(--sp-background); color:var(--sp-navy); }
    [data-testid="stHeader"] { background:rgba(255,255,255,.96); border-bottom:1px solid var(--sp-border); }
    /* Reserve space for Streamlit's fixed header and deployment controls. */
    .block-container { max-width:none; padding:4.4rem 3.2rem 3rem; }
    .sp-header { display:flex; align-items:center; gap:16px; height:47px; margin:0 -3.2rem 20px; padding:0 3.2rem;
      border-bottom:1px solid var(--sp-border); color:var(--sp-navy); }
    .sp-mark, .sp-logo { width:30px; height:30px; flex:0 0 30px; object-fit:contain; }
    .sp-mark { border:5px solid var(--sp-teal); border-radius:50%; box-sizing:border-box;
      position:relative; box-shadow:inset 0 0 0 3px var(--sp-background); }
    .sp-mark:after { content:""; position:absolute; width:9px; height:9px; border-radius:50%; background:var(--sp-navy); top:5px; left:5px; }
    .sp-brand { font-size:16px; font-weight:700; letter-spacing:-.3px; } .sp-separator { color:var(--sp-border); font-size:25px; font-weight:200; }
    .sp-product { color:var(--sp-muted); font-size:15px; font-weight:600; }
    h1,h2,h3 { color:var(--sp-navy) !important; letter-spacing:-.35px; }
    h1 { font-size:25px !important; } h2 { font-size:20px !important; } h3 { font-size:16px !important; }
    [data-testid="stCaptionContainer"] p { color:var(--sp-muted) !important; }
    [data-testid="stMetric"] { border:1px solid var(--sp-border); border-radius:9px; padding:14px 16px; background:var(--sp-background); }
    [data-testid="stMetricLabel"] { color:var(--sp-muted); font-size:13px; } [data-testid="stMetricValue"] { color:var(--sp-navy); font-size:25px; }
    .sp-highlight-metric { border:1px solid var(--sp-border); border-radius:9px; padding:14px 16px; background:var(--sp-navy); min-height:82px; }
    .sp-highlight-label { color:rgba(255,255,255,.72); font-size:13px; }
    .sp-highlight-value { color:#ffffff; font-size:25px; font-weight:600; margin-top:2px; }
    .sp-highlight-metric--warning { background:#7A2626; border-color:#C64242; }
    .sp-highlight-metric--warning .sp-highlight-label, .sp-highlight-metric--warning .sp-highlight-value { color:#FBDADA; }
    .stTabs [data-baseweb="tab-list"] { gap:28px; border-bottom:1px solid var(--sp-border); }
    .stTabs [data-baseweb="tab"] { color:var(--sp-muted); font-weight:600; padding:10px 0; }
    .stTabs [aria-selected="true"] { color:var(--sp-navy) !important; border-bottom:2px solid var(--sp-teal); }
    .stButton > button, .stDownloadButton > button { border:1px solid var(--sp-teal); background:var(--sp-background); color:var(--sp-teal); border-radius:22px; font-weight:600; }
    .stButton > button[kind="primary"] { background:var(--sp-teal); color:var(--sp-background); }
    [data-testid="stFileUploader"] { border:1px solid var(--sp-border); border-radius:8px; padding:8px; }
    [data-testid="stDataFrame"] { border:1px solid var(--sp-border); border-radius:8px; overflow:hidden; }
    hr { border-color:var(--sp-border) !important; }
    .sp-milestone-summary { margin:0 0 1.25rem; padding:.2rem 0 1.15rem; border-bottom:1px solid var(--sp-border); }
    .sp-tpa-name { margin:0 0 .8rem; color:var(--sp-navy); font-size:20px; font-weight:700; letter-spacing:-.3px; }
    .sp-timeline { position:relative; display:grid; grid-template-columns:1fr 1.15fr 1fr; align-items:start; gap:.75rem; max-width:760px; }
    .sp-timeline:before { content:""; position:absolute; z-index:0; top:14px; left:17%; right:17%; height:1px; background:var(--sp-border); }
    .sp-milestone, .sp-timeline-metric { position:relative; z-index:1; text-align:center; }
    .sp-milestone-icon { display:inline-flex; align-items:center; justify-content:center; width:28px; height:28px; margin:0 0 .3rem; border-radius:50%; background:var(--sp-background); color:var(--sp-teal); font-size:16px; }
    .sp-milestone-label { color:var(--sp-navy); font-size:13px; font-weight:700; }
    .sp-milestone-date { margin-top:.18rem; color:var(--sp-muted); font-size:13px; font-weight:600; }
    .sp-timeline-metric { padding:0 .75rem; background:var(--sp-background); }
    .sp-timeline-value { color:var(--sp-navy); font-size:20px; font-weight:700; letter-spacing:-.3px; line-height:1.35; }
    .sp-timeline-caption { margin-top:.16rem; color:var(--sp-muted); font-size:12px; font-weight:600; }
    @media (max-width:640px) { .sp-timeline { gap:.25rem; } .sp-timeline:before { left:13%; right:13%; } .sp-timeline-metric { padding:0 .3rem; } .sp-timeline-value { font-size:17px; } .sp-milestone-label, .sp-milestone-date { font-size:12px; } }
    </style>""",
    unsafe_allow_html=True,
)

DATA_DIR = "data"
CUSTOMER_FILE = os.path.join(DATA_DIR, "customers.csv")
REQUIRED_CUSTOMER_COLUMNS = ["TPA", "GoLiveDate", "AccountManager", "ExpectedUsers", "Notes"]
INTERNAL_USERS = ["Raksha", "Michael Haas"]
FLAG_COLOR = "#C64242"
STALE_PLAN_THRESHOLD_DAYS = 14
CHART_TICK_FORMATS = {"Daily": "%d %b", "Weekly": "%d %b %Y", "Monthly": "%b %Y"}

os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(CUSTOMER_FILE):
    pd.DataFrame(columns=REQUIRED_CUSTOMER_COLUMNS).to_csv(CUSTOMER_FILE, index=False)


def load_customers():
    customers = pd.read_csv(CUSTOMER_FILE)
    for column in REQUIRED_CUSTOMER_COLUMNS:
        if column not in customers.columns:
            customers[column] = pd.NA
    return customers[REQUIRED_CUSTOMER_COLUMNS]


def save_customer(customer):
    """Save a TPA and replace an existing record with the same name."""
    customers = load_customers()
    customers = customers[
        customers["TPA"].fillna("").str.casefold() != customer["TPA"].casefold()
    ]
    pd.concat([customers, pd.DataFrame([customer])], ignore_index=True).to_csv(
        CUSTOMER_FILE, index=False
    )


def find_tpa_from_logins(logins):
    if "GROUPS" not in logins or logins["GROUPS"].dropna().empty:
        return None
    return str(logins["GROUPS"].dropna().iloc[0]).replace("/", "").strip()


def first_plan_after_go_live(plans, go_live_date):
    if plans.empty:
        return pd.NaT
    eligible = plans.loc[plans["ProcessedAt"].dt.date >= go_live_date, "ProcessedAt"]
    return eligible.min() if not eligible.empty else pd.NaT


def last_plan_processed(plans):
    """Most recent plan-processed timestamp, used for the days-since-last-plan metric."""
    if plans.empty:
        return pd.NaT
    return plans["ProcessedAt"].max()


def classify_plans(plans):
    categorized = plans.copy()
    categorized["Plan type"] = "Other"
    if "PLAN_CATEGORY" in categorized.columns:
        source = categorized["PLAN_CATEGORY"].fillna("").astype(str).str.upper()
        categorized.loc[source.str.contains("START", na=False), "Plan type"] = "Startup"
        categorized.loc[source.str.contains("TAKE", na=False), "Plan type"] = "Takeover"
    return categorized


def daily_counts(data, timestamp_column, count_name, freq="D"):
    """Group timestamps into counts per period. freq: 'D' daily, 'W' weekly, 'ME' monthly.
    pd.Grouper fills any gap periods within the range with a zero count."""
    counts = (
        data.groupby(pd.Grouper(key=timestamp_column, freq=freq))
        .size()
        .reset_index(name=count_name)
    )
    return counts.rename(columns={timestamp_column: "Date"}).sort_values("Date")


def type_split_counts(data, timestamp_column, freq, all_dates):
    """Per-period counts split by Plan type, zero-filled against all_dates so every
    period lines up across bar/line charts even where a type had no activity."""
    if data.empty or "Plan type" not in data.columns:
        return pd.DataFrame({"Date": all_dates})
    pivot = (
        data.groupby([pd.Grouper(key=timestamp_column, freq=freq), "Plan type"])
        .size()
        .unstack(fill_value=0)
    )
    pivot = pivot.reindex(all_dates, fill_value=0)
    pivot.index.name = "Date"
    return pivot.reset_index()


def integer_dtick_for(max_value):
    """Pick a 'nice' integer tick step so the y-axis never lands on fractional
    ticks. tickformat alone doesn't fix this — it just rounds whatever
    fractional ticks Plotly auto-picks, which produces repeated labels
    (e.g. 3, 3, 2, 2, 1, 1, 0) when the data range is small."""
    if max_value is None or max_value <= 0:
        return 1
    for step in (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000):
        if max_value / step <= 8:
            return step
    magnitude = 10 ** len(str(int(max_value)))
    return magnitude // 10


def apply_trend_chart_styling(fig, freq_label, go_live_date=None, y_max=None):
    """Shared styling for the Login/Plan trend charts: integer y-axis ticks,
    a date format that matches the selected granularity, and a go-live marker."""
    fig.update_yaxes(tickformat=",d", rangemode="tozero", dtick=integer_dtick_for(y_max))
    fig.update_xaxes(tickformat=CHART_TICK_FORMATS[freq_label])
    if go_live_date is not None:
        # Kaleido serializes Plotly figures when producing PDF chart images.
        # A pandas Timestamp in the marker is not JSON serializable.
        go_live_marker = pd.Timestamp(go_live_date).isoformat()
        fig.add_vline(
            x=go_live_marker, line_dash="dash", line_color="#FF7D59",
            annotation_text="Go-live", annotation_position="top right",
            annotation_font_color="#FF7D59",
        )
    return fig


def flag_zero_activity(fig, counts_df, value_col):
    """Mark periods with no activity at all with a small red 'x' at the baseline,
    so a TPA overseeing onboarding can spot stalled periods at a glance."""
    zero_periods = counts_df[counts_df[value_col] == 0]
    if not zero_periods.empty:
        fig.add_trace(go.Scatter(
            x=zero_periods["Date"], y=[0] * len(zero_periods), mode="markers",
            marker={"color": FLAG_COLOR, "size": 10, "symbol": "x"},
            name="No activity", showlegend=True,
        ))
    return fig


def display_value(value):
    return "-" if pd.isna(value) or str(value).strip() == "" else value


def report_colors_from_ui(branding):
    """The report uses exactly the UI's colors — no separate report palette."""
    return dict(branding["colors"])


def export_safe_figure(figure):
    """Return a Plotly figure with pandas values converted to JSON-safe values.

    Chart annotations and traces may contain pandas Timestamps. Plotly displays
    them in Streamlit, but Kaleido needs a fully JSON-serializable figure when
    it creates the static chart images used by the PDF export.
    """
    return pio.from_json(pio.to_json(figure, validate=False), output_type="Figure")


def build_downloadable_report(customer, go_live_date, first_plan, plans, figures, branding):
    """Create a standalone, branded HTML report with the generated charts,
    used as the source for the downloadable PDF."""
    startup_count = int((plans["Plan type"] == "Startup").sum())
    takeover_count = int((plans["Plan type"] == "Takeover").sum())
    first_plan_text = first_plan.strftime("%d %b %Y, %H:%M") if pd.notna(first_plan) else "Not found"
    time_to_first = (
        f"{(first_plan.date() - go_live_date).days} days" if pd.notna(first_plan) else "-"
    )
    has_first_plan = pd.notna(first_plan)
    first_plan_date = first_plan.date() if has_first_plan else None
    milestone_duration = (first_plan_date - go_live_date).days if has_first_plan else None
    first_plan_milestone = first_plan_date.strftime("%d %b %Y") if has_first_plan else "Not yet onboarded"
    milestone_value = f"{milestone_duration} days" if has_first_plan else "&mdash;"
    milestone_caption = "Time to first plan" if has_first_plan else "Awaiting first plan"
    last_plan = last_plan_processed(plans)
    last_plan_text = last_plan.strftime("%d %b %Y, %H:%M") if pd.notna(last_plan) else "Not found"
    days_since_last_plan = (date.today() - last_plan.date()).days if pd.notna(last_plan) else None
    days_since_last_plan_text = f"{days_since_last_plan} days" if days_since_last_plan is not None else "-"
    is_stale = days_since_last_plan is not None and days_since_last_plan > STALE_PLAN_THRESHOLD_DAYS
    colors = report_colors_from_ui(branding)
    metrics = [
        ("Production go-live", go_live_date.strftime("%d %b %Y")),
        ("First plan processed", first_plan_text),
        ("Time to first plan", time_to_first),
        ("Total processed plans", str(len(plans))),
        ("Startup plans", str(startup_count)),
        ("Takeover plans", str(takeover_count)),
    ]
    metric_rows = []
    for i in range(0, len(metrics), 3):
        cells = "".join(
            f'''<td style="width:33.33%;padding:0 {0 if (i + j) % 3 == 2 else 7}px 14px 0;">
              <div style="background:{colors['background']};border:1px solid {colors['border']};border-radius:12px;padding:18px;min-height:78px;">
                <div style="color:{colors['muted']};font-size:11px;font-weight:700;letter-spacing:.02em;margin-bottom:10px;">{escape(label)}</div>
                <div style="color:{colors['navy']};font-size:21px;font-weight:800;">{escape(value)}</div>
              </div>
            </td>'''
            for j, (label, value) in enumerate(metrics[i:i + 3])
        )
        metric_rows.append(f"<tr>{cells}</tr>")
    metric_html = f'<table style="width:100%;border-collapse:collapse;table-layout:fixed;">{"".join(metric_rows)}</table>'

    stale_days_display = f"⚠ {days_since_last_plan_text}" if is_stale else days_since_last_plan_text
    warning_bg, warning_text = "#7A2626", "#FBDADA"
    highlight_html = f'''<table style="width:100%;border-collapse:collapse;table-layout:fixed;margin-top:2px;">
    <tr>
    <td style="width:50%;padding:0 7px 14px 0;">
      <div style="background:{colors['navy']};border-radius:12px;padding:18px;min-height:78px;">
        <div style="color:rgba(255,255,255,.72);font-size:11px;font-weight:700;margin-bottom:10px;">Last plan processed</div>
        <div style="color:#ffffff;font-size:21px;font-weight:800;">{escape(last_plan_text)}</div>
      </div>
    </td>
    <td style="width:50%;padding:0 0 14px 7px;">
      <div style="background:{warning_bg if is_stale else colors['navy']};border-radius:12px;padding:18px;min-height:78px;">
        <div style="color:{warning_text if is_stale else 'rgba(255,255,255,.72)'};font-size:11px;font-weight:700;margin-bottom:10px;">Days since last plan</div>
        <div style="color:{warning_text if is_stale else '#ffffff'};font-size:21px;font-weight:800;">{escape(stale_days_display)}</div>
      </div>
    </td>
    </tr></table>'''

    milestone_html = f'''<table style="width:100%;max-width:640px;border-collapse:collapse;margin:24px 0 8px;">
    <tr>
    <td style="width:33%;text-align:center;border-top:2px solid {colors['teal']};padding-top:10px;">
      <div style="color:{colors['navy']};font-size:13px;font-weight:800;">PROD LIVE</div>
      <div style="color:{colors['muted']};font-size:13px;margin-top:2px;">{go_live_date.strftime("%d %b %Y")}</div>
    </td>
    <td style="width:34%;text-align:center;border-top:2px solid {colors['teal']};padding-top:10px;">
      <div style="color:{colors['navy']};font-size:21px;font-weight:800;">{milestone_value}</div>
      <div style="color:{colors['muted']};font-size:11px;font-weight:700;margin-top:2px;">{milestone_caption.upper()}</div>
    </td>
    <td style="width:33%;text-align:center;border-top:2px solid {colors['teal']};padding-top:10px;">
      <div style="color:{colors['navy']};font-size:13px;font-weight:800;">FIRST PLAN</div>
      <div style="color:{colors['muted']};font-size:13px;margin-top:2px;">{first_plan_milestone}</div>
    </td>
    </tr></table>'''

    chart_html = ""
    for figure in figures:
        figure = export_safe_figure(figure)
        figure.update_layout(
            colorway=[colors["teal"], colors["navy"], colors["muted"]],
            paper_bgcolor=colors["background"],
            plot_bgcolor=colors["background"],
            font={"family": "Arial, sans-serif", "color": colors["navy"]},
            title={"font": {"size": 16, "color": colors["navy"]}},
            margin={"l": 60, "r": 24, "t": 55, "b": 42},
        )
        figure.update_xaxes(gridcolor=colors["border"], linecolor=colors["border"], automargin=True)
        figure.update_yaxes(gridcolor=colors["border"], linecolor=colors["border"], automargin=True, title_standoff=14)
        # Only backfill navy where a trace has no explicit color of its own —
        # traces we deliberately colored (plan-type stacks, the cumulative
        # line, zero-activity flags) keep their colors as-is.
        for trace in figure.data:
            if trace.type == "bar" and not trace.marker.color:
                trace.update(marker={"color": colors["navy"], "line": {"color": colors["navy"]}})
            elif trace.type == "scatter":
                has_marker_color = trace.marker and trace.marker.color
                has_line_color = trace.line and trace.line.color
                if not has_marker_color and not has_line_color:
                    trace.update(marker={"color": colors["navy"]}, line={"color": colors["navy"]})
        img_bytes = figure.to_image(format="png", width=1200, height=550, scale=2)
        encoded = base64.b64encode(img_bytes).decode("ascii")
        chart_html += (
            f'<div style="margin:18px 0;padding-top:14px;border-top:1px solid {colors["border"]};">'
            f'<img src="data:image/png;base64,{encoded}" alt="chart" style="width:100%;height:auto;display:block;"></div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{escape(branding['company_name'])} | {escape(str(customer['TPA']))}</title>
<style>
body {{ font-family: Arial, Helvetica, sans-serif; color: {colors['navy']}; margin: 0; background: {colors['background']}; }}
.page {{ padding: 34px 40px 44px; }}
.eyebrow {{ color:{colors['teal']}; font-size:11px; font-weight:800; letter-spacing:.1em; text-transform:uppercase; margin:0 0 6px; }}
h1 {{ margin:0; font-size:32px; }}
.subtitle {{ color:{colors['muted']}; margin:8px 0 0; font-size:14px; font-weight:600; }}
.details {{ background:{colors['background']}; border:1px solid {colors['border']}; padding:18px 22px; border-radius:12px; margin-top:24px; }}
.details h2 {{ margin:0 0 12px; font-size:16px; }} .details p {{ margin:7px 0; color:{colors['muted']}; font-size:13px; }} .details strong {{ color:{colors['navy']}; }}
</style></head><body><div class="page">
<div class="eyebrow">Production adoption report</div>
<h1>{escape(str(customer['TPA']))}</h1>
<div class="subtitle">Go-live progress, first-plan timing, and production activity</div>
{milestone_html}
<div style="margin-top:20px;">{metric_html}</div>
{highlight_html}
{chart_html}
<div class="details"><h2>Report details</h2><p><strong>TPA:</strong> {escape(str(customer['TPA']))}</p>
<p><strong>Production go-live date:</strong> {go_live_date.isoformat()}</p>
<p><strong>First plan processed after go-live:</strong> {escape(first_plan_text)}</p>
<p><strong>Last plan processed:</strong> {escape(last_plan_text)}</p>
<p><strong>Days since last plan processed:</strong> {escape(days_since_last_plan_text)}</p></div>
</div></body></html>"""


def build_pdf_report(customer, go_live_date, first_plan, plans, figures, branding):
    """Render the report to PDF bytes via wkhtmltopdf (through pdfkit)."""
    import pdfkit
    executable = find_wkhtmltopdf()
    if executable is None:
        raise RuntimeError("wkhtmltopdf is not available on this computer.")
    html = build_downloadable_report(customer, go_live_date, first_plan, plans, figures, branding)
    options = {
        "page-size": "A4", "encoding": "UTF-8", "quiet": "",
        "margin-top": "12mm", "margin-bottom": "12mm", "margin-left": "12mm", "margin-right": "12mm",
    }
    configuration = pdfkit.configuration(wkhtmltopdf=executable)
    return pdfkit.from_string(html, False, options=options, configuration=configuration)


def find_wkhtmltopdf():
    """Return a usable wkhtmltopdf path, if the optional PDF dependency is installed."""
    candidates = [
        os.environ.get("WKHTMLTOPDF_PATH"),
        shutil.which("wkhtmltopdf"),
        r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe",
        r"C:\\Program Files (x86)\\wkhtmltopdf\\bin\\wkhtmltopdf.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    return None


st.markdown(
    f'''<div class="sp-header">{logo_html(BRANDING)}<div class="sp-brand">{escape(BRANDING["company_name"])}</div>
    <div class="sp-separator">/</div><div class="sp-product">{escape(BRANDING["product_name"])}</div></div>''',
    unsafe_allow_html=True,
)
st.title("TPA production go-live report")
st.caption("Track production go-live, first plan processed, and adoption activity in one report.")

setup_tab, report_tab = st.tabs(["TPA setup", "Go-live report"])

with setup_tab:
    st.header("TPA register")
    st.caption("Select a TPA to edit it. The production go-live date saved here is used in reports.")
    setup_customers = load_customers()
    setup_names = setup_customers["TPA"].dropna().astype(str).tolist()
    tpa_to_edit = st.selectbox(
        "TPA to add or edit",
        options=["Add a new TPA"] + setup_names,
        help="Choose an existing TPA to change its production go-live date or details.",
    )
    existing_customer = None
    if tpa_to_edit != "Add a new TPA":
        existing_customer = setup_customers.loc[setup_customers["TPA"] == tpa_to_edit].iloc[0]

    existing_go_live = date.today()
    if existing_customer is not None:
        parsed_date = pd.to_datetime(existing_customer["GoLiveDate"], errors="coerce")
        if pd.notna(parsed_date):
            existing_go_live = parsed_date.date()

    with st.form("customer_form", clear_on_submit=False):
        name = st.text_input("TPA name", value="" if existing_customer is None else existing_customer["TPA"])
        go_live = st.date_input(
            "Production go-live date (used in reports)",
            value=existing_go_live,
            help="The report finds the first plan processed on or after this manually entered date.",
        )
        manager = st.text_input(
            "Account manager",
            value="" if existing_customer is None else display_value(existing_customer["AccountManager"]),
        )
        expected_users = st.number_input(
            "Expected users",
            min_value=0,
            value=0 if existing_customer is None or pd.isna(existing_customer["ExpectedUsers"])
            else int(existing_customer["ExpectedUsers"]),
        )
        notes = st.text_area("Notes", value="" if existing_customer is None else display_value(existing_customer["Notes"]))
        save = st.form_submit_button("Save TPA changes")

    if save:
        if not name.strip():
            st.error("Enter a TPA name before saving.")
        else:
            save_customer({
                "TPA": name.strip(), "GoLiveDate": go_live.isoformat(),
                "AccountManager": manager.strip(), "ExpectedUsers": expected_users,
                "Notes": notes.strip(),
            })
            st.success(f"Saved {name.strip()}.")

    st.dataframe(setup_customers, width="stretch", hide_index=True)

with report_tab:
    st.header("Production adoption")
    st.caption("The TPA is detected automatically from the login export. Upload both files to create the report.")

    customers = load_customers()
    plan_csv = st.file_uploader("Plan-processing CSV", type="csv")
    login_csv = st.file_uploader("Login activity CSV", type="csv")
    plans, logins = None, None

    if plan_csv is not None:
        try:
            plans = pd.read_csv(plan_csv)
        except (UnicodeDecodeError, pd.errors.ParserError):
            st.error("The plan file could not be read as a CSV.")
    if login_csv is not None:
        try:
            logins = pd.read_csv(login_csv)
        except (UnicodeDecodeError, pd.errors.ParserError):
            st.error("The login file could not be read as a CSV.")

    detected_tpa = find_tpa_from_logins(logins) if logins is not None else None
    if detected_tpa:
        st.info(f"Detected TPA: {detected_tpa}")
    elif logins is not None:
        st.warning("The login CSV needs a usable `GROUPS` value to detect the TPA.")

    user_options = []
    if plans is not None and "USER_NAME" in plans.columns:
        user_options.extend(plans["USER_NAME"].dropna().astype(str).unique())
    if logins is not None and "username" in logins.columns:
        user_options.extend(logins["username"].dropna().astype(str).unique())
    user_options = sorted(set(user_options))
    excluded_users = st.multiselect(
        "Exclude internal users", options=user_options,
        default=[user for user in INTERNAL_USERS if user in user_options],
        help="Excluded users are removed from every metric and graph.",
    )

    if st.button("Create go-live report", type="primary"):
        if plans is None:
            st.error("Upload a plan-processing CSV to create the report.")
        elif logins is None:
            st.error("Upload a login activity CSV so the TPA can be detected automatically.")
        elif not detected_tpa:
            st.error("A TPA could not be detected from the login CSV.")
        elif "timestamp" not in plans.columns:
            st.error("The plan CSV must contain a `timestamp` column.")
        else:
            matches = customers[
                customers["TPA"].fillna("").str.casefold() == detected_tpa.casefold()
            ]
            if matches.empty:
                st.error(
                    f"{detected_tpa} is not in the TPA register. Add it in TPA setup and save its production go-live date before creating the report."
                )
            else:
                customer = matches.iloc[0]
                go_live_date = pd.to_datetime(customer["GoLiveDate"], errors="coerce")
                if pd.isna(go_live_date):
                    st.error("The detected TPA does not have a valid production go-live date.")
                else:
                    report_plans = plans.copy()
                    report_plans["ProcessedAt"] = pd.to_datetime(report_plans["timestamp"], errors="coerce")
                    report_plans = report_plans.dropna(subset=["ProcessedAt"])
                    if "USER_NAME" in report_plans.columns:
                        report_plans = report_plans[~report_plans["USER_NAME"].isin(excluded_users)]
                    report_plans = classify_plans(report_plans)

                    report_logins = pd.DataFrame(columns=["LoggedAt", "username"])
                    if {"timestamp", "username"}.issubset(logins.columns):
                        report_logins = logins.copy()
                        report_logins["LoggedAt"] = pd.to_datetime(report_logins["timestamp"], errors="coerce")
                        report_logins = report_logins.dropna(subset=["LoggedAt"])
                        report_logins = report_logins[~report_logins["username"].isin(excluded_users)]

                    st.session_state["go_live_report"] = {
                        "customer": customer, "go_live_date": go_live_date.date(),
                        "first_plan": first_plan_after_go_live(report_plans, go_live_date.date()),
                        "plans": report_plans, "logins": report_logins,
                    }

    report = st.session_state.get("go_live_report")
    if report:
        customer, go_live_date = report["customer"], report["go_live_date"]
        first_plan, report_plans, report_logins = report["first_plan"], report["plans"], report["logins"]
        startup_count = int((report_plans["Plan type"] == "Startup").sum())
        takeover_count = int((report_plans["Plan type"] == "Takeover").sum())
        report_figures = []

        st.divider()
        st.markdown(
            milestone_summary_html(customer["TPA"], go_live_date, first_plan),
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Production go-live", go_live_date.strftime("%d %b %Y"))
        c2.metric("First plan processed", first_plan.strftime("%d %b %Y, %H:%M") if pd.notna(first_plan) else "Not found")
        c3.metric("Time to first plan", f"{(first_plan.date() - go_live_date).days} days" if pd.notna(first_plan) else "-")
        c4, c5, c6 = st.columns(3)
        c4.metric("Total processed plans", len(report_plans))
        c5.metric("Startup plans", startup_count)
        c6.metric("Takeover plans", takeover_count)

        last_plan = last_plan_processed(report_plans)
        days_since_last_plan = (date.today() - last_plan.date()).days if pd.notna(last_plan) else None
        is_stale = days_since_last_plan is not None and days_since_last_plan > STALE_PLAN_THRESHOLD_DAYS
        c7, c8 = st.columns(2)
        with c7:
            st.markdown(
                f"""<div class="sp-highlight-metric">
                <div class="sp-highlight-label">Last plan processed</div>
                <div class="sp-highlight-value">{escape(last_plan.strftime("%d %b %Y, %H:%M") if pd.notna(last_plan) else "Not found")}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with c8:
            card_class = "sp-highlight-metric sp-highlight-metric--warning" if is_stale else "sp-highlight-metric"
            value_text = f"{days_since_last_plan} days" if days_since_last_plan is not None else "-"
            if is_stale:
                value_text = f"⚠ {value_text}"
            st.markdown(
                f"""<div class="{card_class}">
                <div class="sp-highlight-label">Days since last plan</div>
                <div class="sp-highlight-value">{escape(value_text)}</div>
                </div>""",
                unsafe_allow_html=True,
            )

        if pd.isna(first_plan):
            st.warning("No plan in this file was processed on or after the production go-live date.")

        chart_freq_label = st.radio(
            "Chart granularity", options=["Weekly", "Monthly", "Daily"], index=0, horizontal=True,
        )
        st.caption("Applies to the Login activity and Plan-processing activity charts below, and carries through to the downloaded report.")
        chart_freq = {"Daily": "D", "Weekly": "W", "Monthly": "ME"}[chart_freq_label]
        chart_freq_word = {"Daily": "day", "Weekly": "week", "Monthly": "month"}[chart_freq_label]

        is_bar_view = chart_freq_label in ("Weekly", "Monthly")

        st.subheader("Login activity")
        if report_logins.empty:
            st.info("The login CSV needs `timestamp` and `username` columns with valid data to show the login trend.")
        else:
            login_counts = daily_counts(report_logins, "LoggedAt", "Logins", chart_freq)
            if is_bar_view:
                fig_logins = px.bar(login_counts, x="Date", y="Logins", text="Logins", title=f"Logins by {chart_freq_word}")
                fig_logins.update_traces(textposition="outside", marker_color=COLORS["teal"])
            else:
                fig_logins = px.line(login_counts, x="Date", y="Logins", markers=True, title=f"Logins by {chart_freq_word}")
                fig_logins.update_traces(marker_color=COLORS["teal"], line_color=COLORS["teal"])
            apply_trend_chart_styling(fig_logins, chart_freq_label, go_live_date, y_max=login_counts["Logins"].max())
            flag_zero_activity(fig_logins, login_counts, "Logins")
            st.plotly_chart(fig_logins, width="stretch")
            report_figures.append(fig_logins)

        st.subheader("Plan-processing activity")
        if report_plans.empty:
            st.info("No valid plan timestamps are available in the uploaded file.")
        else:
            plan_totals = daily_counts(report_plans, "ProcessedAt", "Plans processed", chart_freq)
            plan_totals["Cumulative"] = plan_totals["Plans processed"].cumsum()
            plan_types_present = sorted(report_plans["Plan type"].dropna().unique())
            type_pivot = type_split_counts(report_plans, "ProcessedAt", chart_freq, plan_totals["Date"])
            long_type_counts = type_pivot.melt(id_vars="Date", value_vars=plan_types_present, var_name="Plan type", value_name="Plans processed")

            if is_bar_view:
                fig_uploads = px.bar(
                    long_type_counts, x="Date", y="Plans processed", color="Plan type", barmode="stack",
                    title=f"Plans processed by {chart_freq_word}", color_discrete_map=PLAN_TYPE_COLORS,
                )
            else:
                fig_uploads = px.line(
                    long_type_counts, x="Date", y="Plans processed", color="Plan type", markers=True,
                    title=f"Plans processed by {chart_freq_word}", color_discrete_map=PLAN_TYPE_COLORS,
                )
            fig_uploads.update_layout(legend_title_text="Plan type")
            apply_trend_chart_styling(fig_uploads, chart_freq_label, go_live_date, y_max=plan_totals["Plans processed"].max())
            flag_zero_activity(fig_uploads, plan_totals, "Plans processed")

            # Total-per-bar labels (segment-level labels get cluttered once stacked).
            for _, row in plan_totals.iterrows():
                if row["Plans processed"] > 0:
                    fig_uploads.add_annotation(
                        x=row["Date"], y=row["Plans processed"], text=str(int(row["Plans processed"])),
                        showarrow=False, yshift=10, font={"color": COLORS["navy"], "size": 12},
                    )

            # Cumulative running total on a secondary axis, per TPA request to see overall progress.
            fig_uploads.add_trace(go.Scatter(
                x=plan_totals["Date"], y=plan_totals["Cumulative"], name="Cumulative total",
                mode="lines", line={"color": COLORS["navy"], "dash": "dot"}, yaxis="y2",
            ))
            fig_uploads.update_layout(yaxis2={
                "title": "Cumulative", "overlaying": "y", "side": "right",
                "rangemode": "tozero", "tickformat": ",d",
                "dtick": integer_dtick_for(plan_totals["Cumulative"].max()),
            })

            st.plotly_chart(fig_uploads, width="stretch")
            report_figures.append(fig_uploads)

        st.subheader("Plan ownership and categories")
        uploaders_column, categories_column = st.columns(2)
        with uploaders_column:
            if "USER_NAME" not in report_plans.columns:
                st.info("Add a `USER_NAME` column to the plan CSV to view top uploaders.")
            elif report_plans.empty:
                st.info("No plan data is available for the uploader chart.")
            else:
                top_uploaders = (report_plans["USER_NAME"].fillna("Unknown").value_counts().head(10).sort_values().rename_axis("User").reset_index(name="Plans processed"))
                fig_uploaders = px.bar(top_uploaders, x="Plans processed", y="User", orientation="h", text="Plans processed", title="Top plan uploaders")
                fig_uploaders.update_traces(marker_color=COLORS["teal"])
                st.plotly_chart(fig_uploaders, width="stretch")
                report_figures.append(fig_uploaders)
        with categories_column:
            category_counts = report_plans["Plan type"].value_counts().rename_axis("Plan type").reset_index(name="Plans")
            if category_counts.empty:
                st.info("No plan data is available for the category chart.")
            else:
                fig_categories = px.pie(
                    category_counts, names="Plan type", values="Plans", hole=0.45, title="Startup vs takeover plans",
                    color="Plan type", color_discrete_map=PLAN_TYPE_COLORS,
                )
                st.plotly_chart(fig_categories, width="stretch")
                report_figures.append(fig_categories)

        details = pd.DataFrame([
            {"Field": "TPA", "Value": customer["TPA"]},
            {"Field": "Production go-live date", "Value": go_live_date.isoformat()},
            {"Field": "First plan processed after go-live", "Value": first_plan.isoformat(sep=" ") if pd.notna(first_plan) else "Not found"},
            {"Field": "Last plan processed", "Value": last_plan.isoformat(sep=" ") if pd.notna(last_plan) else "Not found"},
            {"Field": "Days since last plan processed", "Value": f"{days_since_last_plan} days" if days_since_last_plan is not None else "Not available"},
        ])
        st.subheader("Report details")
        st.dataframe(details, width="stretch", hide_index=True)
        html_report = build_downloadable_report(
            customer, go_live_date, first_plan, report_plans, report_figures, BRANDING
        )
        st.download_button(
            "Download interactive HTML report",
            data=html_report,
            file_name=f"singlepointai-{str(customer['TPA']).replace(' ', '-').lower()}-go-live-report.html",
            mime="text/html",
            help="Open in a browser or print to PDF. This option is always available.",
        )
        wkhtmltopdf_path = find_wkhtmltopdf()
        if wkhtmltopdf_path:
            if st.button("Prepare PDF report", icon=":material/picture_as_pdf:"):
                try:
                    st.session_state["pdf_report"] = build_pdf_report(
                        customer, go_live_date, first_plan, report_plans, report_figures, BRANDING
                    )
                    st.session_state["pdf_report_tpa"] = customer["TPA"]
                except Exception as error:
                    st.error(f"Could not create the PDF report: {error}")
            if st.session_state.get("pdf_report") and st.session_state.get("pdf_report_tpa") == customer["TPA"]:
                st.download_button(
                    "Download PDF report",
                    data=st.session_state["pdf_report"],
                    file_name=f"singlepointai-{str(customer['TPA']).replace(' ', '-').lower()}-go-live-report.pdf",
                    mime="application/pdf",
                    help="Downloads a branded PDF report.",
                )
        else:
            st.info(
                "PDF export is not configured on this computer. Download the interactive HTML report and use your browser's Print > Save as PDF option."
            )
