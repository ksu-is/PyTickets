# PyTickets - Implementation Roadmap

**Purpose**: End-to-end ticket discovery and customer notification system. The crawler finds tickets, filters them, and sends links to customers for manual purchase.

**Scope**: All suggested features EXCEPT purchase automation (human purchase decision)

---

## 🎯 Vision

```
Ticket Website
     ↓
   Crawler (Selenium)
     ↓
   Filter Engine
     ↓
   Database Storage
     ↓
   Multi-Channel Notifications
     ↓
   Customer Links
     ↓
   [HUMAN PURCHASES]  ← Manual step
```

---

## 📅 Implementation Phases

### Phase 0: Foundation (Complete ✅)
- [x] Multi-site adapter architecture
- [x] Flexible authentication system
- [x] Advanced filtering engine
- [x] Multi-channel notifications
- [x] Structured logging
- [x] Unit tests (50+)
- [x] Configuration system

**Status**: Ready for Phase 1

---

## 🔥 Phase 1: Core Operations (Weeks 1-2)

### 1.1 URL Deduplication & Caching
**Why**: Prevent buying same ticket twice, optimize crawling

**What to Build**:
```python
# ticketCrawler/utils/url_cache.py
class URLCache:
    - is_visited(url) → bool
    - mark_visited(url, metadata={}) → None
    - get_metadata(url) → dict
    - save_to_disk() → None
    - load_from_disk() → None
    - clear_old_entries(days=30) → None
    
Storage:
    - In-memory: Set for current session
    - Disk: JSON file for persistence
    - Optional: Redis for distributed
```

**Implementation**:
- Store: URL → timestamp + ticket metadata
- Auto-save after each crawl
- Auto-clear entries older than 30 days
- Prevent duplicate tickets from being notified

**Integration Points**:
- RefactoredTicketsSpider: Skip visited URLs
- Database: Check before storing
- Notifications: Deduplicate before sending

**Estimated Effort**: 1-2 days | **Impact**: ⭐⭐⭐⭐

---

### 1.2 APScheduler Integration
**Why**: Fully autonomous periodic crawling

**What to Build**:
```python
# ticketCrawler/scheduler/job_manager.py
class CrawlerScheduler:
    - schedule_site(site_name, interval_hours=2) → job_id
    - list_scheduled_jobs() → List[Job]
    - cancel_job(job_id) → bool
    - pause_job(job_id) → bool
    - resume_job(job_id) → bool
    - get_job_status(job_id) → JobStatus
    
# ticketCrawler/scheduler/config.py
SCHEDULE_CONFIG = {
    'dutch_tickets': {
        'interval': 2,  # hours
        'enabled': True,
        'max_concurrent': 1
    },
    'eventim': {
        'interval': 3,
        'enabled': False
    }
}
```

**Features**:
- Cron-style scheduling (hourly, daily, weekly)
- Concurrent crawl management
- Job persistence (resume after restart)
- Failure notifications
- Configurable per-site intervals

**Integration Points**:
- Start script: Initialize scheduler on startup
- Web API: List/manage scheduled jobs
- Database: Log job execution

**Usage Example**:
```bash
# Run continuously with scheduling
python run_scheduler.py

# Or as systemd service
[Unit]
Description=PyTickets Scheduler
ExecStart=/usr/bin/python3 /path/to/run_scheduler.py
Restart=always
```

**Estimated Effort**: 1-2 days | **Impact**: ⭐⭐⭐⭐

---

### 1.3 SQLite Database Integration
**Why**: Persist data, enable analytics, track history

**What to Build**:
```python
# ticketCrawler/database/models.py
class Ticket(Base):
    id: str (unique)
    site: str
    url: str
    price: float
    seat_type: str
    event_date: datetime
    found_at: datetime
    notified_at: datetime | None
    
class CrawlRun(Base):
    id: str
    site: str
    start_time: datetime
    end_time: datetime
    tickets_found: int
    tickets_notified: int
    errors: str | None
    
class URLVisited(Base):
    url: str
    visited_at: datetime
    metadata: JSON (ticket info)
    
class Customer(Base):
    id: str
    email: str
    telegram_id: str | None
    preferences: JSON (filters)
    created_at: datetime
```

**Schema Design**:
```sql
CREATE TABLE tickets (
    id TEXT PRIMARY KEY,
    site TEXT,
    url TEXT UNIQUE,
    price REAL,
    seat_type TEXT,
    event_date DATETIME,
    found_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notified_at DATETIME,
    notification_status TEXT
);

CREATE INDEX idx_site_found ON tickets(site, found_at);
CREATE INDEX idx_notified ON tickets(notified_at);
```

**ORM Implementation**:
- SQLAlchemy for abstraction
- Alembic for migrations
- Connection pooling for concurrency

**Integration Points**:
- RefactoredTicketsSpider: Store tickets found
- URLCache: Query previous visits
- Notifications: Update notification status
- Web API: Query historical data

**Usage**:
```python
from ticketCrawler.database import Database

db = Database('sqlite:///tickets.db')
db.save_ticket(ticket_data)
recent = db.get_tickets(site='dutch_tickets', hours=24)
```

**Estimated Effort**: 2-3 days | **Impact**: ⭐⭐⭐⭐

---

### 1.4 Enhanced Error Handling & Recovery
**Why**: Better reliability and debugging

**What to Add**:
```python
# Extend ticketCrawler/utils/helpers.py
class RetryHelper:
    - retry_with_backoff() [already done]
    - Add circuit breaker pattern
    - Add adaptive backoff based on error type
    - Parse Retry-After headers
    
class ErrorHandler:
    - classify_error(error) → ErrorType
    - is_retryable(error) → bool
    - suggest_action(error) → str
    
# Extend RefactoredTicketsSpider
Spider improvements:
    - Retry on 429 (rate limit)
    - Fallback proxy on 403 (blocked)
    - Clear cookies on 401 (auth failed)
    - Alert on 5xx (server issues)
    - Store error details for debugging
```

**Estimated Effort**: 1-2 days | **Impact**: ⭐⭐⭐

---

## 📦 Phase 2: Deployment & Scale (Weeks 3-4)

### 2.1 Docker Containerization
**Why**: One-command deployment anywhere

**Files to Create**:
```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app

# Chrome + Chromedriver
RUN apt-get update && apt-get install -y chromium chromium-driver

# Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# App code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "run_scheduler.py"]
```

**Supporting Files**:
- `docker-compose.yml` - with optional PostgreSQL, Redis
- `.dockerignore` - exclude unnecessary files
- `docker-entrypoint.sh` - initialization script

**Cloud Deployment Options**:
1. **Docker Desktop** (local): `docker-compose up`
2. **AWS ECS** (managed): ECR + ECS task definition
3. **EC2** (VPS): Docker + systemd
4. **Heroku** (PaaS): Procfile + Docker
5. **Railway/Render** (modern): Git push deploy

**Estimated Effort**: 2-3 days | **Impact**: ⭐⭐⭐⭐

---

### 2.2 REST API & Web Dashboard
**Why**: Remote control and monitoring

**Backend API** (`Flask` or `FastAPI`):
```python
# ticketCrawler/api/routes.py
GET  /api/health                    → Status
GET  /api/sites                     → List configured sites
GET  /api/jobs                      → List scheduled jobs
POST /api/jobs                      → Schedule new job
GET  /api/tickets?site=dutch&hours=24 → Query tickets
GET  /api/crawls                    → Crawl history
POST /api/notifications/test        → Send test notification
GET  /api/config                    → Current configuration
PUT  /api/config                    → Update configuration
DELETE /api/cache                   → Clear URL cache
```

**Frontend Dashboard** (React/Vue):
```
Dashboard Features:
├── Live Crawl Status
│   ├── Running jobs
│   ├── Last run time
│   └── Tickets found
├── Ticket Listings
│   ├── Filter by site/price/date
│   ├── Copy link to clipboard
│   └── Mark as purchased
├── Configuration
│   ├── Schedule management
│   ├── Filter settings
│   └── Notification channels
└── Analytics
    ├── Tickets found per hour
    ├── Success rate
    └── Most common prices
```

**Tech Stack Options**:
- Backend: FastAPI (modern) or Flask (simple)
- Frontend: React (feature-rich) or Vue (lightweight)
- Database: PostgreSQL (production) or SQLite (dev)
- Deployment: Docker + reverse proxy (nginx)

**Estimated Effort**: 5-7 days (API: 2-3 days, Dashboard: 3-4 days) | **Impact**: ⭐⭐⭐⭐⭐

---

### 2.3 Proxy Rotation System
**Why**: Bypass rate limiting, handle IP blocks

**What to Build**:
```python
# ticketCrawler/proxies/proxy_manager.py
class ProxyRotator:
    - add_proxy(url) → None
    - get_next_proxy() → Proxy
    - mark_failed(proxy) → None
    - mark_successful(proxy) → None
    - get_health_status() → Dict
    
    Proxy Types:
    - Manual list (ProxyMesh, BrightData, etc.)
    - Tor SOCKS5
    - Residential (optional)
    
# ticketCrawler/proxies/strategies.py
Rotation Strategies:
    - Round-robin: Use each proxy in order
    - Random: Pick random proxy
    - Weighted: Prefer healthy proxies
    - Per-domain: Different proxy per site
```

**Configuration**:
```json
{
  "proxy_config": {
    "type": "manual",
    "proxies": [
      "http://proxy1.example.com:8080",
      "http://proxy2.example.com:8080"
    ],
    "rotation_strategy": "round_robin",
    "max_failures": 3,
    "timeout": 10
  }
}
```

**Integration**:
- RefactoredTicketsSpider: Use proxy for each request
- Selenium: Pass proxy to ChromeDriver
- Retry: Switch proxy on failure
- Logging: Track proxy usage

**Estimated Effort**: 2-3 days | **Impact**: ⭐⭐⭐

---

## 🧠 Phase 3: Intelligence (Weeks 5-6)

### 3.1 ML-Based Price Prediction
**Why**: Alert users only for good deals

**What to Build**:
```python
# ticketCrawler/ml/price_predictor.py
class PricePredictor:
    - train_model(historical_data) → Model
    - predict_good_price(event_id) → float
    - is_good_deal(price, event_id) → bool
    - get_confidence() → float
    
Historical Data Tracked:
    - Event ID
    - Price (date)
    - Supply (tickets available)
    - Demand (time to event)
    
ML Model Options:
    - Time series (ARIMA, Prophet)
    - XGBoost (for feature importance)
    - Neural network (if lots of data)
```

**Features**:
- Track price trends over time
- Predict optimal buying time
- Classify: Good/OK/Bad/Overpriced
- Only alert on good deals
- Learn from user purchases

**Storage**:
- Database: Historical price data
- Model file: Serialized trained model
- Metadata: Confidence intervals

**Estimated Effort**: 3-5 days | **Impact**: ⭐⭐⭐

---

### 3.2 Ticket Availability Patterns
**Why**: Predict when new tickets appear

**What to Build**:
```python
# ticketCrawler/ml/pattern_analyzer.py
class PatternAnalyzer:
    - analyze_availability(event_id) → Pattern
    - predict_next_drop() → datetime
    - get_high_probability_times() → List[TimeSlot]
    
Patterns Detected:
    - Time of day (e.g., "New tickets at 3 PM")
    - Day of week
    - Before event date triggers
    - Seller behavior patterns
    
Output: "Tickets likely appear on Fridays 2-4 PM"
```

**Integration**:
- Schedule crawls during predicted high-probability times
- Alert users: "New tickets likely in 1 hour"
- Reduce unnecessary crawls during low-probability times

**Estimated Effort**: 2-3 days | **Impact**: ⭐⭐

---

### 3.3 Duplicate Detection & Deduplication
**Why**: Identify same tickets from different sellers

**What to Build**:
```python
# ticketCrawler/ml/deduplicator.py
class Deduplicator:
    - is_duplicate(ticket1, ticket2) → bool
    - find_duplicates(ticket_list) → List[Duplicates]
    - find_best_offer(duplicates) → Ticket
    
Matching Criteria:
    - Event name/date/venue
    - Price range (within 10%)
    - Seat location (if available)
    - Seller reputation
    
Output: Best offer highlighted, duplicates grouped
```

**Estimated Effort**: 2-3 days | **Impact**: ⭐⭐

---

## 🤖 Phase 4: Advanced Features (Weeks 7-8)

### 4.1 Telegram Bot Interface
**Why**: Mobile-friendly control via Telegram

**What to Build**:
```python
# ticketCrawler/telegram_bot/bot.py
Commands:
    /start                   → Setup guide
    /crawl dutch_tickets     → Start crawl
    /jobs                    → List scheduled jobs
    /tickets                 → Show found tickets
    /config                  → Update filters
    /recent_prices           → Price trends
    /subscribe dutch_tickets → Get alerts
    /unsubscribe             → Stop alerts
    
Features:
    - Real-time crawl status
    - Inline keyboard navigation
    - Ticket links in messages
    - Filter setup via commands
    - Photo search (if seat maps available)
```

**Tech**:
- python-telegram-bot library
- Webhook or polling mode
- User preference storage

**Estimated Effort**: 2-3 days | **Impact**: ⭐⭐⭐

---

### 4.2 Multi-Browser Concurrency
**Why**: Crawl multiple sites simultaneously

**What to Build**:
```python
# ticketCrawler/concurrent/browser_pool.py
class BrowserPool:
    - acquire_browser() → WebDriver
    - release_browser(driver) → None
    - get_available_count() → int
    - set_pool_size(size) → None
    
# ticketCrawler/concurrent/crawler_executor.py
Parallel Crawling:
    - ThreadPoolExecutor for multiple browsers
    - Queue for site management
    - Resource pooling
    - Deadlock prevention
```

**Configuration**:
```json
{
  "concurrency": {
    "max_browsers": 3,
    "browser_pool_size": 5,
    "timeout_per_crawl": 300
  }
}
```

**Performance**:
- Single site: ~60-120 seconds per crawl
- 3 concurrent: ~60-120 seconds for all sites
- Estimated 5-10x speedup

**Estimated Effort**: 4-5 days | **Impact**: ⭐⭐⭐⭐

---

### 4.3 Smart Captcha Handling
**Why**: Unattended operation on protected sites

**Options** (in priority order):
1. **Selenium-Stealth** (free, lightweight)
   - Reduced bot detection
   - No API required
   - 80% success rate

2. **Manual Flow + Notification**
   - Send Telegram: "Solve captcha in browser"
   - Pause crawl until solved
   - Resume automatically
   - Best for low-frequency sites

3. **2Captcha or Anti-Captcha** (paid)
   - Automatic solving
   - $0.50 - $2 per captcha
   - Good for high-traffic sites

**Implementation**:
```python
# ticketCrawler/captcha/solver.py
class CaptchaSolver:
    - needs_captcha(driver) → bool
    - solve_automatic(driver) → bool
    - notify_user(method) → None
    - wait_for_solution(timeout) → bool
```

**Estimated Effort**: 1-3 days (depends on option) | **Impact**: ⭐⭐

---

### 4.4 Multi-Account Support
**Why**: Increase rate limits and success rate

**What to Build**:
```python
# ticketCrawler/accounts/account_pool.py
class AccountPool:
    - add_account(site, email, password, config) → account_id
    - get_next_account(site) → Account
    - mark_rate_limited(account) → None
    - mark_healthy(account) → None
    - get_account_status(site) → List[AccountStatus]
    
# ticketCrawler/accounts/health_monitor.py
Account Health:
    - Last used
    - Error count
    - Rate limit status
    - Auth failures
    - Success rate
```

**Features**:
- Account rotation per request
- Health monitoring
- Auto-disable bad accounts
- Load balancing
- Prevent simultaneous use

**Requirements**:
- Multiple accounts per site
- Credentials storage (encrypted)
- Account monitoring

**Estimated Effort**: 3-4 days | **Impact**: ⭐⭐⭐⭐

---

### 4.5 Advanced Analytics & Reporting
**Why**: Insights into crawling performance

**What to Build**:
```python
# ticketCrawler/analytics/metrics.py
Dashboards:
    - Tickets found per hour
    - Success rate by site
    - Average response time
    - Price trends
    - Most common seat types
    - Revenue potential (price × quantity)
    
Reports:
    - Daily summary (email)
    - Weekly analytics
    - Monthly ROI analysis
    - Trend detection
```

**Visualizations**:
- Charts: Chart.js or Plotly
- Heatmaps: Ticket availability over time
- Trends: Price changes week-over-week
- Comparisons: Site performance

**Estimated Effort**: 3-4 days | **Impact**: ⭐⭐⭐

---

## 🌍 Phase 5: Enterprise Scale (Optional)

### 5.1 Distributed Crawling
**Why**: Scale to 100+ concurrent sites

**Architecture**:
```
┌─────────────────┐
│  Central Queue  │  (RabbitMQ/Kafka)
├─────────────────┤
│ Site Jobs       │
│ Scheduled       │
└────────┬────────┘
         │
    ┌────┴────┬──────┬──────┐
    ↓         ↓      ↓      ↓
 Crawler   Crawler Crawler Crawler
  Node 1    Node 2  Node 3  Node 4
    │         │      │      │
    └─────┬────┴──┬───┴──┬───┘
          ↓       ↓      ↓
      ┌───────────────────┐
      │  Central Database │
      │   (PostgreSQL)    │
      └───────────────────┘
          ↓
    ┌───────────────┐
    │  Redis Cache  │
    │  (URL dedup)  │
    └───────────────┘
```

**Tech**: RabbitMQ, Redis, PostgreSQL, Kubernetes
**Estimated Effort**: 2-3 weeks | **Impact**: ⭐⭐⭐⭐⭐

---

### 5.2 Multi-Crawler Coordination
**Why**: Share state across distributed crawlers

**Coordination**:
```python
# ticketCrawler/distributed/coordinator.py
- Shared URL cache
- Job coordination
- Result aggregation
- Failure handling
- Load balancing
```

**Estimated Effort**: 1-2 weeks | **Impact**: ⭐⭐⭐⭐

---

## 📊 Implementation Timeline Summary

| Phase | Feature | Duration | Priority | Impact |
|-------|---------|----------|----------|--------|
| **1** | URL Deduplication | 1-2 days | 🔴 High | ⭐⭐⭐⭐ |
| **1** | APScheduler | 1-2 days | 🔴 High | ⭐⭐⭐⭐ |
| **1** | SQLite Database | 2-3 days | 🔴 High | ⭐⭐⭐⭐ |
| **1** | Error Handling | 1-2 days | 🟠 Med | ⭐⭐⭐ |
| **2** | Docker | 2-3 days | 🟠 Med | ⭐⭐⭐⭐ |
| **2** | API/Dashboard | 5-7 days | 🟡 Low | ⭐⭐⭐⭐⭐ |
| **2** | Proxy Rotation | 2-3 days | 🟠 Med | ⭐⭐⭐ |
| **3** | Price Prediction | 3-5 days | 🟡 Low | ⭐⭐⭐ |
| **3** | Pattern Analysis | 2-3 days | 🟡 Low | ⭐⭐ |
| **3** | Deduplication | 2-3 days | 🟡 Low | ⭐⭐ |
| **4** | Telegram Bot | 2-3 days | 🟡 Low | ⭐⭐⭐ |
| **4** | Multi-Browser | 4-5 days | 🟡 Low | ⭐⭐⭐⭐ |
| **4** | Captcha Handling | 1-3 days | 🟡 Low | ⭐⭐ |
| **4** | Multi-Account | 3-4 days | 🟡 Low | ⭐⭐⭐⭐ |
| **4** | Analytics | 3-4 days | 🟡 Low | ⭐⭐⭐ |
| **5** | Distributed | 2-3 weeks | 🟣 Rare | ⭐⭐⭐⭐⭐ |

**Total Without Phase 5**: ~4-6 weeks (with full implementation)

---

## 🎯 Recommended Quick Start

**Week 1: Foundation**
```bash
Day 1: URL Deduplication
Day 2: APScheduler Integration  
Day 3: SQLite Database
Day 4: Error Handling + Testing
```

**Week 2-3: Deployment Ready**
```bash
Day 5-6: Docker + Compose
Day 7-11: REST API + Dashboard
Day 12: Proxy Rotation
```

**After Deployment: Enhancement**
```bash
Week 4+: Price Prediction, Telegram Bot, Analytics
```

---

## ✅ Excluded (As Per Request)

- ❌ Purchase Automation
- ❌ Payment Processing
- ❌ Card Tokenization
- ❌ PCI Compliance

**System ends with**: Ticket links sent to customer → Human reviews → Customer decides to purchase

---

## 📋 Next Steps

1. **Review this roadmap** and prioritize features
2. **Choose starting point** (recommend Phase 1, Item 1.1 URL Deduplication)
3. **Set up development branch** on GitHub
4. **Create issues** for each feature in this roadmap
5. **Begin implementation** with full commit history

---

Would you like me to:
- [ ] Start with Phase 1.1 (URL Deduplication)?
- [ ] Start with Phase 1.2 (APScheduler)?
- [ ] Start with Phase 2.2 (API/Dashboard)?
- [ ] Create detailed implementation guides for specific features?
- [ ] Set up GitHub issues from this roadmap?
