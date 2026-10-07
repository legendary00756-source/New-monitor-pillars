# MS Intelligence dashboard — v4 loading fix

## Run on Windows
Extract ALL.zip and double-click START_WINDOWS.bat. Python 3.11–3.13 must be installed. The launcher installs requirements and opens Streamlit. Click Refresh this section or Refresh all modules. No paid API key is required.

Manual setup:
```
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Upgrade without losing your data
Stop the app and background collector. Back up your old folder. Copy the old **data** folder into this extracted MS_Intelligence_Dashboard folder, then start the app. Keep SQLite sidecar files together and stop processes before copying. Existing settings, notes, bookmarks and reviews are retained. Old generic P2 and P3 technology coverage moves to separate historical sections. Legacy scripts/workbooks remain in legacy/.

## Loading fix
Refresh now runs in a background worker. Saved articles remain usable during collection, and completed searches become visible automatically. Progress is polled every two seconds. Only one dashboard refresh can run at a time; use Stop refresh to cancel queued searches. Active requests finish or time out before the worker stops. No automatic download runs on initial page load; choose a section and click Refresh this section for the fastest first result. Refresh all modules includes entity watchlists and may take several minutes, but does not block browsing.

## Latest-news rules
- Rolling last 24 hours and newest-first order remain the defaults.
- Fast feed-date mode is now the default. Publisher pages are no longer fetched during collection. Dates are labelled unverified unless previously verified evidence exists.
- Strict original-publication dates is optional and only shows previously verified records. It can show an empty feed; leave it OFF for normal use.
- GDELT dates are discovery times, not original publication dates. RSS/Atom entries with only an updated date remain excluded.
- Existing articles keep their earliest stored date when refreshed. Previously verified old publication dates remain respected.
- Free feeds cannot guarantee every story or exclude every resurfaced article. All matching collected records are available via pagination and exports.

## Duplicate handling
Expensive fuzzy headline matching and cross-publisher grouping have been removed from collection and display. Similar reports from different publishers can appear separately. Stable article IDs still prevent repeatedly inserting the same record, and module/topic tags remain intact. Existing records and notes are preserved; reports already merged in older versions cannot be fully separated without recollection. Read, pin and bookmark actions now apply to the selected stored record.

## Curated sections
### P3 · Global tech hiring
Worldwide AI/data, cybersecurity, software engineering, cloud/DevOps, fintech hiring and technology job creation. Requires a hiring signal in the headline and technology context. Excludes general product news, layoffs, hiring freezes/slowdowns and job scams. These are hiring news articles, not an exhaustive job-vacancy board. Conservative wording filters may miss some relevant reports.

### Global cybersecurity
Threats/incidents, ransomware/breaches, vulnerabilities/patches, cybersecurity companies and regulation. Headlines/snippets must contain a cybersecurity signal.

### Global data analytics
Analytics/business intelligence, data science/engineering, data platforms and governance. Generic AI news without analytics/data context is excluded.

### UAE · Key people & movements
Public professional appointments, departures, promotions, succession, board changes and senior government/institutional appointments. Requires leadership and movement signals with a UAE connection. This does not track personal locations or travel. User-defined entity searches and keywords can supplement coverage.

All other modules remain: UAE/global M&A, wealth, real estate, UAE corridors, India PE/M&A/foreign investment/AIF, GIFT City, ADGM/DIFC/QFC, family offices, industrial/infrastructure deals, macro developments, IPOs, sovereign/private credit, regulatory watch and custom monitoring.

## Sources
- **Google News RSS:** default discovery searches and entity watchlists. Feed date alone is unverified in strict mode.
- **Bing News RSS:** default supplementary discovery with direct publisher links when exposed; these open the original article for manual review. Actual returned volume may be lower than requested; stale feed items are filtered. Existing saved provider preferences are respected—enable Bing under Settings if upgrading from Google-only settings.
- **GDELT DOC API:** optional, free/no key; broad supplementary search per module, up to 250 results, six-second request spacing. HTTP 429 pauses GDELT in that process for 15 minutes; other providers continue. Its discovery timestamp is not a publication date.
- **Custom public HTTPS RSS/Atom:** configure in Settings. The new four curated sections apply topic gates even to custom feeds; other sections use your module assignment. Only published-dated entries are accepted at collection.

No paid keys, email sending or private-profile access is used by the dashboard. The fast collector makes feed/API requests only. Source failures are recorded in Sources & status and do not erase saved news.

## Other features
Key-news scores with reasons; persistent keyword alerts; read/unread, bookmarks and pins; analyst deal reviews (buyer/target/value/status/owner/action/notes); entity Excel import/editor; custom searches; coverage charts; CSV/Excel/PDF exports; text brief; settings export; database backup. Automated deal/sector/amount signals are suggestions, not verified transaction facts. The tracker is article-based and does not sum headline amounts as transaction volume. Alerts stay inside the dashboard.

## Background collector
```
python monitor.py --every 30 --days 1
```
Leave the computer and process running. Omit --every for one run. For Windows Task Scheduler use the virtual environment's python.exe with `monitor.py --days 1` and set Start in to the dashboard folder. No scheduled task is installed automatically. Streamlit auto-refresh runs only while a session is active. Settings are shared with the collector. Avoid overlapping multiple collection processes.

## Backup and restore
Settings & watchlists offers a consistent database backup. To restore, stop the app and collector, keep a backup of existing data, and place the downloaded news.sqlite3 at data/news.sqlite3. Settings/reviews are shared by users of this installation; this local/internal app has no built-in authentication.

## Legacy code
Original scripts and spreadsheets are retained under legacy/. Credentials were externalized and paths made portable. The new app does not invoke the original AI, paid-API or email pipeline. Running legacy/main.py separately can send email if configured. Rotate credentials from the original archive if you have not already done so.

## Tests and references
Run `python -m unittest discover -s . -p "test_*.py" -v` from this folder. Tests use explicitly labelled fixtures in temporary databases; no fixture news ships in the app database. Checks cover dates, updates, unknown timezones, duplicates, material follow-ups, curation, legacy migration, partial source failures, UI sections, review actions and exports.

https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment
