# PyTickets - Refactored Multi-Site Ticket Crawler

A flexible, modular Scrapy-based ticket crawler supporting multiple websites with pluggable authentication, filtering, and notifications.

## 🏗️ Architecture Overview

The refactored system is built on a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     Ticket Spider                            │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │   Config       │  │   Site         │  │ Notification │  │
│  │   Loader       │  │   Adapter      │  │ Manager      │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ Authenticator  │  │   Filters      │  │   Logger     │  │
│  │ (Pluggable)    │  │ (Combinable)   │  │ (Structured) │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. **Configuration System** (`config/`)
- `ConfigLoader`: Loads site configurations from JSON files
- `site_configs/`: Per-site configuration files with selectors, auth settings, rate limits
- Environment variable substitution for credentials

#### 2. **Site Adapters** (`adapters/`)
- `BaseAdapter`: Abstract interface for site-specific logic
- `DutchTicketsAdapter`: Implementation for Dutch ticket site
- `AdapterFactory`: Creates adapters from config
- Easily extend with new adapters for other sites

#### 3. **Authentication** (`auth/`)
- `BaseAuthenticator`: Abstract authentication interface
- `FacebookAuthenticator`: OAuth login
- `EmailPasswordAuthenticator`: Direct email/password login
- `OAuthAuthenticator`: Google/Apple/other providers
- `AuthenticatorFactory`: Pluggable auth system

#### 4. **Ticket Filters** (`filters/`)
- `PriceFilter`: Min/max price filtering
- `SeatTypeFilter`: Filter by seat location
- `DateFilter`: Event date range filtering
- `QuantityFilter`: Ticket quantity filtering
- `CombinedFilter`: Apply multiple filters with AND/OR logic
- `FilterFactory`: Easy filter instantiation

#### 5. **Notifications** (`notifications/`)
- `TelegramNotifier`: Send to Telegram
- `EmailNotifier`: Send via Mailgun or SMTP
- `SMSNotifier`: Send SMS via Twilio
- `WebhookNotifier`: Custom HTTP webhooks
- `NotificationManager`: Multi-channel notifications
- `NotificationFactory`: Create notifiers

#### 6. **Utilities** (`utils/`)
- `LoggerFactory`: Structured logging
- `RetryHelper`: Retry with exponential backoff
- `URLHelper`: URL manipulation
- `TextHelper`: Text extraction and parsing
- `DataHelper`: Nested dictionary operations

## 📋 Configuration

### Site Configuration Example

```json
{
  "name": "Dutch Tickets",
  "base_url": "env:ticket_site",
  "auth": {
    "type": "facebook",
    "credentials": {
      "email": "env:fb_email",
      "password": "env:fb_password"
    }
  },
  "selectors": {
    "sold_tickets_link_xpath_offered": "//section[2]/div/article/div[1]/h3/a/@href",
    "ticket_array_xpath": "//body/div[4]/div/div[2]/article",
    "buy_button_class": "btn-buy",
    "success_indicators": ["Pay with iDEAL", "Betaalmethode"]
  },
  "proxy_required": true,
  "rate_limit": {
    "min_delay": 2.5,
    "max_delay": 4.3
  }
}
```

### Environment Variables

```bash
# Basic
export ticket_site="https://example.com/tickets"

# Authentication
export fb_email="your-email@facebook.com"
export fb_password="your-password"

# Notifications
export telegram_token="YOUR_BOT_TOKEN"
export telegram_chat_id="YOUR_CHAT_ID"

# Filtering
export min_price="10.00"
export max_price="100.00"
export seat_types="floor,vip"
```

## 🚀 Usage

### Basic Spider Execution

```bash
# Run spider for Dutch site
scrapy crawl tickets_refactored -a site=dutch_tickets -a url=https://example.com/tickets

# Run with custom site
scrapy crawl tickets_refactored -a site=custom_site -a url=https://custom.com/tickets
```

### Python Code Usage

```python
from ticketCrawler.config.config_loader import ConfigLoader
from ticketCrawler.adapters.factory import AdapterFactory
from ticketCrawler.auth.factory import AuthenticatorFactory
from ticketCrawler.filters.factory import FilterFactory
from ticketCrawler.notifications.manager import NotificationManager

# Load configuration
config_loader = ConfigLoader()
site_config = config_loader.get_config('dutch_tickets')

# Create components
adapter = AdapterFactory.create_adapter('dutch_tickets', site_config)
auth_config = site_config.get('auth', {})
authenticator = AuthenticatorFactory.create_authenticator(auth_config['type'], auth_config)

# Create filters
combined_filter = FilterFactory.create_combined_filter([
    {'type': 'price', 'min_price': 10, 'max_price': 100},
    {'type': 'seat_type', 'seat_types': ['floor', 'vip']},
])

# Setup notifications
manager = NotificationManager()
# Add notifiers...

# Use components for ticket crawling
```

## 🔌 Extending the System

### Add a New Site

1. Create site configuration (`configs/sites/newsite.json`):
```json
{
  "name": "New Site",
  "base_url": "env:newsite_url",
  "auth": {"type": "email_password", ...},
  "selectors": {...},
  "proxy_required": false
}
```

2. Create adapter (`ticketCrawler/adapters/site_adapters/newsite_adapter.py`):
```python
from ticketCrawler.adapters.base_adapter import BaseAdapter

class NewSiteAdapter(BaseAdapter):
    def authenticate(self, browser): ...
    def extract_tickets(self, response): ...
    # ... implement all abstract methods
```

3. Register adapter in factory:
```python
from ticketCrawler.adapters.factory import AdapterFactory
from ticketCrawler.adapters.site_adapters.newsite_adapter import NewSiteAdapter

AdapterFactory.register_adapter('newsite', NewSiteAdapter)
```

4. Run spider:
```bash
scrapy crawl tickets_refactored -a site=newsite -a url=...
```

### Add Custom Filter

```python
from ticketCrawler.filters.base_filter import BaseFilter
from ticketCrawler.filters.factory import FilterFactory

class CustomFilter(BaseFilter):
    def matches(self, ticket):
        # Your filtering logic
        return True

FilterFactory.register_filter('custom', CustomFilter)
```

### Add Notification Channel

```python
from ticketCrawler.notifications.base_notifier import BaseNotifier
from ticketCrawler.notifications.manager import NotificationFactory

class CustomNotifier(BaseNotifier):
    def notify(self, message, **kwargs):
        # Your notification logic
        return True

NotificationFactory.register_notifier('custom', CustomNotifier)
```

## 📊 Features Implemented

- ✅ Multi-site support with pluggable adapters
- ✅ Flexible authentication (Facebook, Email/Password, OAuth)
- ✅ Ticket filtering (price, seat type, date, quantity)
- ✅ Multi-channel notifications (Telegram, Email, SMS, Webhooks)
- ✅ Structured logging with file output
- ✅ Retry logic with exponential backoff
- ✅ Environment variable based configuration
- ✅ Factory patterns for easy extensibility
- ✅ Combined filters with AND/OR logic

## 🔄 Migration from Old System

The old `TicketsSpider` is still available as `tickets.py`. The new refactored spider `RefactoredTicketsSpider` is available as `tickets_refactored.py`.

**Key improvements:**
- Hardcoded values → Configuration files
- Single site → Multi-site support
- Hardcoded auth → Pluggable authentication
- No filtering → Flexible ticket filtering
- Limited notifications → Multi-channel with formatting
- Minimal logging → Structured logging

## 📝 Examples

See `examples.py` for comprehensive usage examples:

```bash
python examples.py
```

Examples include:
1. Basic configuration loading
2. Authentication setup
3. Creating and combining filters
4. Setting up notifications
5. Registering custom adapters
6. Listing available components

## 🛠️ Development

To add new features:

1. **New adapter**: Inherit from `BaseAdapter`, implement all methods
2. **New filter**: Inherit from `BaseFilter`, implement `matches()`
3. **New notifier**: Inherit from `BaseNotifier`, implement `notify()`
4. **New authenticator**: Inherit from `BaseAuthenticator`, implement methods

All components use factories for registration and instantiation, making the system highly extensible.

## 📄 License

See LICENSE file

## 🤝 Contributing

Contributions are welcome! Please:
1. Follow the adapter/filter/notifier pattern
2. Add configuration files for new sites
3. Update examples with new features
4. Test thoroughly before submitting

---

**Happy crawling! 🚀**
