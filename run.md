# Running the application

From the project root:

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
python run.py
```

Alternatively:

```powershell
python -m streamlit run ui/app.py
```

The application opens at `http://localhost:8501`.

Before using Graylog import, set the Graylog and PostgreSQL values in `.env`.
Set `DATA_PATH` to the folder where downloaded CSV files should be stored.
