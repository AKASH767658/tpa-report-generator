# TPA Management Report

Streamlit dashboard for TPA production adoption, login counts, plan activity,
Graylog CSV downloads, and plan-management status.

## Project layout

```text
tpa_management_report/
├── ui/
│   ├── app.py
│   └── assets/branding/
├── backend/
│   ├── plan_management_report.py
│   ├── graylog/
│   │   ├── pp_prod.py
│   │   └── spai_prod.py
│   └── db_engine/
│       ├── connection.py
│       └── queries.py
├── tests/
├── run.py
├── config.json
├── .env
└── data/
```

`DATA_PATH` in `.env` is the single location used for Graylog CSV downloads,
customer data, and report generation. Relative paths are resolved from the
project root.
