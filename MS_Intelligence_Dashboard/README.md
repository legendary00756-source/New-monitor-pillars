# MS Intelligence dashboard

## Start on Windows
Extract the entire ZIP into a folder. Double-click START_WINDOWS.bat. Python 3.11–3.13 must be installed (with the Python launcher). The first run installs dependencies and opens the dashboard. Click **Refresh this section** or **Refresh all modules** to collect news.

Manual setup (Windows, macOS or Linux):
```
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Sections
- P1 Wealth intelligence: original entities.xlsx watchlist plus UAE wealth market.
- P2 Entity intelligence: original entities (1).xlsx watchlist plus market news.
- P3 Technology & hiring: original AI/Data, Cybersecurity, Cloud & DevOps, and Fintech fields, plus technology market.
- E7 Real estate: market and developer news.
- UAE corridors: India, USA, Singapore, Africa, China, UK, Saudi Arabia, Europe, Japan/Korea and other countries.
- India Private equity, M&A, Foreign investments, and AIF: separate sections.
- GIFT City: ecosystem, funds/administration, policy/regulation, banking/markets.
- Additional ADGM/DIFC/QFC, family office/succession, and industrial/infrastructure monitors.

## Operation
The new dashboard uses a shared free Google News RSS collector for all sections. It preserves module subjects and Excel entity watchlists, but does not invoke the old scraping/paid API/AI/email pipeline. All original Python modules remain in `legacy/`, with credentials externalized and paths made portable. The old main.py can still perform its original pipeline when its environment is configured, including sending email; the dashboard and monitor.py never send email.

Date filters apply to publication time, not download time. Missing dates are excluded. Articles are stored in data/news.sqlite3 across restarts, deduplicated by normalized headline and publisher, with many module/topic tags. Similar syndicated stories with different headlines/publishers may remain. Saving an article bookmarks it in the database. Date filters also apply to saved articles. CSV/Excel/PDF export the current filtered view. Source health records the latest result of each attempted query. Empty results and failed requests are shown separately; previous articles survive failed refreshes.

An uploaded entity Excel file is session-only. For permanent changes used by background collection, replace the corresponding file under legacy/ using the same filename. No entity limit is imposed. Add countries or modules by editing MODULES / COUNTRIES in monitor.py. The 'Other countries' query currently covers Australia, Canada, Brazil, Indonesia, Malaysia, Pakistan and Turkey; it is not universal coverage.

Auto-refresh runs while the dashboard session is open. To collect in the background, run a separate terminal:
```
python monitor.py --every 60 --days 7
```
Leave that process and the computer running. To use Windows Task Scheduler, schedule `.venv\Scripts\python.exe` with arguments `monitor.py --days 7` and set **Start in** to this dashboard folder. This one-shot command can run hourly. No task has been installed automatically. Back up data/news.sqlite3 while the app and collector are stopped.

## Source limitations
Internet access to news.google.com is required. Free RSS can be blocked, rate-limited, delayed or incomplete. Queries provide discovery, not verified deal status or regulatory advice. Snippets are publisher feed excerpts, not generated factual analysis. Africa and regional groups are explicitly search baskets. Publisher links may redirect through Google News. LinkedIn private content is not accessed. The source-status page exposes failed queries. No historic archive is supplied, and a 90-day query may not return every article in that period.

## Legacy credentials
The supplied archive contained hardcoded credentials. Rotate those original API keys and email app password. This distribution does not include their values or historical logs/bytecode. The dashboard requires no secrets. Legacy optional integrations read GROQ_API_KEY_P1, GROQ_API_KEY_P2, GROQ_API_KEY_P3, GROQ_API_KEY_E7, NEWS_API_KEY, NEWSDATA_KEY, MEDIASTACK_KEY, CURRENTS_KEY, SENDER_EMAIL, SENDER_PASSWORD and comma-separated RECIPIENT_EMAIL from environment variables.

Dashboard API reference: https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment
