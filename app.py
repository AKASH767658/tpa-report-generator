import base64
import json
import mimetypes
import os
from html import escape
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
from plotly.io import to_html
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


def classify_plans(plans):
    categorized = plans.copy()
    categorized["Plan type"] = "Other"
    if "PLAN_CATEGORY" in categorized.columns:
        source = categorized["PLAN_CATEGORY"].fillna("").astype(str).str.upper()
        categorized.loc[source.str.contains("START", na=False), "Plan type"] = "Startup"
        categorized.loc[source.str.contains("TAKE", na=False), "Plan type"] = "Takeover"
    return categorized


def daily_counts(data, timestamp_column, count_name):
    counts = data.groupby(data[timestamp_column].dt.date).size().reset_index(name=count_name)
    return counts.rename(columns={timestamp_column: "Date"}).sort_values("Date")


def display_value(value):
    return "-" if pd.isna(value) or str(value).strip() == "" else value


def build_downloadable_report(customer, go_live_date, first_plan, plans, figures, branding):
    """Create a standalone, branded HTML report with the generated charts."""
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
    colors = branding["downloadable_report_colors"]
    metrics = [
        ("Production go-live", go_live_date.strftime("%d %b %Y")),
        ("First plan processed", first_plan_text),
        ("Time to first plan", time_to_first),
        ("Total processed plans", str(len(plans))),
        ("Startup plans", str(startup_count)),
        ("Takeover plans", str(takeover_count)),
    ]
    metric_html = "".join(
        f'<div class="metric"><span>{escape(label)}</span><strong>{escape(value)}</strong></div>'
        for label, value in metrics
    )
    chart_html = ""
    for index, figure in enumerate(figures):
        figure.update_layout(
            colorway=[colors["teal"], colors["chart_secondary"], colors["chart_tertiary"], colors["chart_quaternary"], colors["teal_light"]],
            paper_bgcolor=colors["card_background"],
            plot_bgcolor=colors["card_background"],
            font={"family": "Inter, Arial, sans-serif", "color": colors["navy"]},
            title={"font": {"size": 18, "color": colors["navy"]}},
            # Leave enough space for horizontal-bar labels and the y-axis title
            # in the standalone HTML report.
            margin={"l": 150, "r": 24, "t": 60, "b": 42},
        )
        figure.update_xaxes(gridcolor=colors["grid"], linecolor=colors["border"], automargin=True)
        figure.update_yaxes(
            gridcolor=colors["grid"], linecolor=colors["border"], automargin=True,
            title_standoff=18,
        )
        # Plotly can otherwise fall back to black for bar and line traces in
        # standalone HTML. Keep dark chart marks on the configured brand navy.
        for trace in figure.data:
            if trace.type == "bar":
                trace.update(
                    marker={"color": colors["navy"], "line": {"color": colors["navy"]}},
                )
            elif trace.type == "scatter":
                trace.update(
                    marker={"color": colors["navy"]},
                    line={"color": colors["navy"]},
                )
        chart_html += f'<section class="chart">{to_html(figure, full_html=False, include_plotlyjs=index == 0)}</section>'

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{escape(branding['company_name'])} | {escape(str(customer['TPA']))}</title>
<style>
* {{ box-sizing:border-box; }}
body {{ font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: {colors['navy']}; margin: 0; background: {colors['page_background']}; }}
.page {{ max-width: 1280px; min-height: 100vh; margin: 0 auto; padding: 40px 48px 56px; background: {colors['background']}; }}
.brand-row {{ display:flex; align-items:center; gap:16px; }}
.sp-mark {{ width:32px; height:32px; flex:0 0 32px; }}
.brand-logo {{ display:block; width:232px; height:auto; max-width:64vw; flex:0 0 auto; object-fit:contain; object-position:left center; }}
.sp-mark {{ border:5px solid {colors['teal']}; border-radius:50%; box-sizing:border-box; position:relative; }}
.sp-mark:after {{ content:""; position:absolute; width:8px; height:8px; border-radius:50%; background:{colors['navy']}; top:5px; left:5px; }}
 .brand {{ color: {colors['navy']}; font-size:17px; font-weight:750; }} .slash {{ color:{colors['border']}; font-size:24px; }} .product {{ color:{colors['muted']}; font-size:13px; font-weight:700; letter-spacing:.03em; text-transform:uppercase; }}
.header {{ padding-bottom:28px; border-bottom:1px solid {colors['border']}; }}
.eyebrow {{ margin:44px 0 8px; color:{colors['teal']}; font-size:12px; font-weight:800; letter-spacing:.12em; text-transform:uppercase; }}
h1 {{ margin:0; max-width:760px; font-size:clamp(32px, 4vw, 48px); line-height:1.08; letter-spacing:-.045em; }}
.subtitle {{ color:{colors['muted']}; margin:12px 0 0; font-size:18px; font-weight:600; }}
.milestone-summary {{ display:grid; grid-template-columns:1fr 1.1fr 1fr; position:relative; align-items:start; gap:12px; max-width:780px; margin:30px 0 0; padding:22px 0 4px; }}
.milestone-summary:before {{ content:""; position:absolute; top:37px; left:17%; right:17%; height:2px; background:{colors['teal_light']}; }}
.milestone, .timeline-metric {{ position:relative; z-index:1; text-align:center; }}
.milestone-icon {{ display:inline-flex; align-items:center; justify-content:center; width:32px; height:32px; border-radius:50%; background:{colors['background']}; font-size:17px; }}
.milestone-label {{ margin-top:6px; color:{colors['navy']}; font-size:13px; font-weight:800; }}
.milestone-date {{ margin-top:4px; color:{colors['muted']}; font-size:13px; font-weight:650; }}
.timeline-metric {{ margin-top:7px; padding:0 13px; background:{colors['background']}; }}
.timeline-value {{ color:{colors['navy']}; font-size:24px; font-weight:800; letter-spacing:-.04em; line-height:1.1; }}
.timeline-caption {{ margin-top:4px; color:{colors['muted']}; font-size:12px; font-weight:700; }}
.metrics {{ display:grid; grid-template-columns:repeat(3, 1fr); gap:14px; margin:28px 0 30px; }}
.metric {{ min-height:112px; background:{colors['card_background']}; border:1px solid {colors['border']}; border-radius:12px; padding:20px; box-shadow:0 3px 12px {colors['shadow']}; }}
.metric span {{ display:block; color:{colors['muted']}; font-size:12px; font-weight:700; letter-spacing:.02em; margin-bottom:11px; }}
.metric strong {{ color:{colors['navy']}; font-size:24px; line-height:1.2; letter-spacing:-.03em; }}
.chart {{ margin:22px 0; padding:10px 4px; border-top:1px solid {colors['border']}; }}
.details {{ background:{colors['surface_subtle']}; border:1px solid {colors['border']}; padding:22px 24px; border-radius:12px; margin-top:28px; }}
.details h2 {{ margin:0 0 14px; font-size:18px; }} .details p {{ margin:8px 0; color:{colors['muted']}; }} .details strong {{ color:{colors['navy']}; }}
@media (max-width:720px) {{ .page {{ padding:28px 22px 40px; }} .brand-row {{ gap:10px; }} .brand-logo {{ width:210px; }} .brand, .slash {{ display:none; }} .product {{ font-size:11px; }} .eyebrow {{ margin-top:34px; }} .milestone-summary {{ gap:4px; }} .milestone-summary:before {{ left:13%; right:13%; }} .timeline-metric {{ padding:0 4px; }} .timeline-value {{ font-size:19px; }} .milestone-label, .milestone-date {{ font-size:11px; }} .metrics {{ grid-template-columns:1fr 1fr; gap:10px; }} .metric {{ min-height:96px; padding:15px; }} .metric strong {{ font-size:20px; }} }}
@media print {{ body {{ background:{colors['background']}; }} .page {{ max-width:none; padding:0; }} .metric {{ box-shadow:none; }} }}
</style></head><body><main class="page"><header class="header"><div class="brand-row">{logo_html(branding, 'brand-logo')}<div class="product">{escape(branding['product_name'])}</div></div>
<p class="eyebrow">Production adoption report</p><h1>{escape(str(customer['TPA']))}</h1><p class="subtitle">Go-live progress, first-plan timing, and production activity</p>
<section class="milestone-summary" aria-label="Production adoption milestones"><div class="milestone"><div class="milestone-icon">&#128640;</div><div class="milestone-label">Prod Live</div><div class="milestone-date">{go_live_date.strftime("%d %b %Y")}</div></div><div class="timeline-metric"><div class="timeline-value">{milestone_value}</div><div class="timeline-caption">{milestone_caption}</div></div><div class="milestone"><div class="milestone-icon">&#128196;</div><div class="milestone-label">First Plan</div><div class="milestone-date">{first_plan_milestone}</div></div></section></header>
<section class="metrics">{metric_html}</section>{chart_html}
<section class="details"><h2>Report details</h2><p><strong>TPA:</strong> {escape(str(customer['TPA']))}</p>
<p><strong>Production go-live date:</strong> {go_live_date.isoformat()}</p>
<p><strong>First plan processed after go-live:</strong> {escape(first_plan_text)}</p></section>
</main></body></html>"""


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

    st.dataframe(setup_customers, use_container_width=True, hide_index=True)

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

        if pd.isna(first_plan):
            st.warning("No plan in this file was processed on or after the production go-live date.")

        st.subheader("Login activity")
        if report_logins.empty:
            st.info("The login CSV needs `timestamp` and `username` columns with valid data to show the login trend.")
        else:
            fig_logins = px.line(daily_counts(report_logins, "LoggedAt", "Logins"), x="Date", y="Logins", markers=True, title="Logins by day")
            st.plotly_chart(fig_logins, use_container_width=True)
            report_figures.append(fig_logins)

        st.subheader("Plan-processing activity")
        if report_plans.empty:
            st.info("No valid plan timestamps are available in the uploaded file.")
        else:
            fig_uploads = px.line(daily_counts(report_plans, "ProcessedAt", "Plans processed"), x="Date", y="Plans processed", markers=True, title="Plans processed by day")
            st.plotly_chart(fig_uploads, use_container_width=True)
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
                st.plotly_chart(fig_uploaders, use_container_width=True)
                report_figures.append(fig_uploaders)
        with categories_column:
            category_counts = report_plans["Plan type"].value_counts().rename_axis("Plan type").reset_index(name="Plans")
            if category_counts.empty:
                st.info("No plan data is available for the category chart.")
            else:
                fig_categories = px.pie(category_counts, names="Plan type", values="Plans", hole=0.45, title="Startup vs takeover plans")
                st.plotly_chart(fig_categories, use_container_width=True)
                report_figures.append(fig_categories)

        details = pd.DataFrame([
            {"Field": "TPA", "Value": customer["TPA"]},
            {"Field": "Production go-live date", "Value": go_live_date.isoformat()},
            {"Field": "First plan processed after go-live", "Value": first_plan.isoformat(sep=" ") if pd.notna(first_plan) else "Not found"},
        ])
        st.subheader("Report details")
        st.dataframe(details, use_container_width=True, hide_index=True)
        st.download_button(
            f"Download {BRANDING['company_name']} report",
            data=build_downloadable_report(
                customer, go_live_date, first_plan, report_plans, report_figures, BRANDING
            ),
            file_name=f"singlepointai-{str(customer['TPA']).replace(' ', '-').lower()}-go-live-report.html",
            mime="text/html",
            help="Downloads a branded interactive HTML report. Open it in a browser or print it to PDF.",
        )
