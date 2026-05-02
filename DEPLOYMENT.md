# PyTickets Deployment

## Local API and Dashboard

```bash
python -m pip install -r requirements.txt
python run_api.py
```

Open `http://localhost:8000`.

## Scheduled Crawling

```bash
python run_scheduler.py
```

Set `PYTICKETS_SCHEDULE_SITE`, `PYTICKETS_SCHEDULE_URL`, and
`PYTICKETS_SCHEDULE_INTERVAL_HOURS` in `.env`.

## Docker

```bash
copy .env.example .env
docker compose up --build
```

The `data/` directory is mounted so SQLite, URL cache, and debug files persist.

## Email

Configure SMTP or Mailgun variables in `.env`. `PYTICKETS_NOTIFY_MODE=first`
sends the first new matching link and stops. `PYTICKETS_NOTIFY_MODE=batch`
sends one email containing every new matching link found in the page.

## Proxy Rotation

Set `PYTICKETS_PROXIES` to a comma-separated list:

```bash
PYTICKETS_PROXIES=http://user:pass@host1:8000,http://host2:8000
```

Supported strategies are `round_robin` and `random`.

## Ticketmaster Discovery API

Set `TICKETMASTER_API_KEY` in `.env`. With the key present, a public event URL
such as `https://www.ticketmaster.com/.../event/<EVENT_ID>` is crawled through:

```text
https://app.ticketmaster.com/discovery/v2/events/<EVENT_ID>.json
```

The notification still links customers to the public Ticketmaster event page for
manual purchase.
