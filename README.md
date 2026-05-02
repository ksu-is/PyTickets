# Ticket Crawler

This spider, written using the python scrapy framework, periodically crawls a popular dutch ticket trading website to check for available tickets and immediately order them once found. The website uses reCaptcha to prevent refreshing more than a couple of times per minute. To bypass this system, the spider uses a combination of proxy rotation and user agent rotation. 
Each consecutive request is routed past a different proxy IP using one out of the 90 most commonly found user agent strings. Seperated from this crawling process, the bot uses Selenium webdriver to log in using facebook in advance and, when a ticket is found, perform the interaction with the ticket buying page which contains dynamic AJAX content.
Once the ticket has been reserved, it sends a notification via telegram

<br>

### Installation
The scraper uses Scrapy and Selenium for Python, both of which need to be installed on the system prior to running the code.
To install Scrapy, see <https://doc.scrapy.org/en/latest/intro/install.html>  
To install Selenium for Python, see <https://selenium-python.readthedocs.io/installation.html>  
Run the following to complete the installation
```
pip install requests
pip install scrapy-random-useragent
```


### Configuration
The script rotates proxies via the proxymesh service. You can get a free 1 month trial on <https://proxymesh.com>. After you've registered, visit <https://proxymesh.com/account/dashboard/> and choose an authorized host. Combining this with your login credits gives you the string needed for the spider, in the following form:
`<username>:<password>@<country>.proxymesh.com:<port>`

This string, along with your facebook login credentials and the ticket site base url, need to be stored as environment variables before running the script. The following environment variables need to be set: http_proxy, fb_email, fb_password and ticket_site.
To set these on a unix system, the following three lines can be executed in your terminal or stored in your .bash_profile or .bashrc. Make sure to restart your terminal before running the script.

```
export http_proxy=<username>:<password>@fr.proxymesh.com:<port>
export fb_email=<facebook_email>
export fb_password=<facebook_password>
export ticket_site=<site_base_url>
```

You can add or remove user agents from the list stored in useragentsMostCommon.txt, which contains about 100 of the most common user agents at the moment.

**Optional:** Besides spoken audio feedback for reserved tickets, the crawler can also notify you when you're away from your computer via Telegram. It does this by using a [Telegram Bot](https://www.codementor.io/garethdwyer/building-a-telegram-bot-using-python-part-1-goi5fncay) through which you can send messages via HTTP requests to Telegram's API. The code for this is already included in the crawler, you will just need your own personal chat ID, which you can get by starting a conversation with [Telegram's @userinfobot bot](https://telegram.me/userinfobot). You can enter your ID in the chatId variable in spiders/tickets.py, but this step is optional and the crawler will work without altering the code


### Execution
The project contains two spiders, located in the ticketCrawler/spiders directory. tickets.py is the full working version, and can be started by running the following command from the root:
```
scrapy crawl tickets -a url=<url_to_event_page>
```

### Refactored Manual-Purchase Workflow
The newer spider is `tickets_refactored`. It finds matching ticket links, skips URLs that were already seen, saves crawl history to SQLite, sends the ticket link through configured notifications, and then stops. It does not reserve or buy tickets automatically.

```
scrapy crawl tickets_refactored -a site=dutch_tickets -a url=<url_to_event_page>
```

Email is the primary notification channel for manual purchase links:

```
export EMAIL_PROVIDER=smtp
export EMAIL_SENDER=you@example.com
export EMAIL_RECIPIENT=customer@example.com
export SMTP_HOST=smtp.example.com
export SMTP_PORT=587
export SMTP_USER=you@example.com
export SMTP_PASSWORD=<password>
```

Phase 1 persistence can be customized with:

```
export PYTICKETS_DB_PATH=data/pytickets.db
export PYTICKETS_URL_CACHE=data/url_cache.json
export PYTICKETS_URL_CACHE_TTL_DAYS=30
```

Scheduled crawling uses APScheduler:

```
export PYTICKETS_SCHEDULE_SITE=dutch_tickets
export PYTICKETS_SCHEDULE_URL=<url_to_event_page>
export PYTICKETS_SCHEDULE_INTERVAL_HOURS=2
python run_scheduler.py
```

### API and Dashboard
Phase 2 adds a small REST API and operational dashboard:

```
python run_api.py
```

Then open `http://localhost:8000`.

The API exposes health, sites, tickets, crawl runs, jobs, one-off crawl starts,
cache clearing, and notification tests under `/api/...`.

### Supported Sites

Current first-class adapters:

- `dutch_tickets`
- `eventim`
- `ticketmaster`
- `seatgeek`

See `ADDING_NEW_SITE.md` for the adapter/config pattern used to add more sites.

For Ticketmaster, set `TICKETMASTER_API_KEY` to use the official Discovery API.
When the key is present, public Ticketmaster event URLs are automatically
rewritten to the matching Discovery API event endpoint before crawling.

### Demo
![Screen Capture](https://github.com/Nedervino/TicketCrawler/blob/master/screenCapture.gif?raw=true)


### Adjusting to changes in website structure
As the crawler is partially based on following links based on XPaths, which can easily break if changes to the site's layout are made, the scraper might crash if you first run it for an updated website. To adjust to the new correct XPath, use scrapy's shell as described [here](https://doc.scrapy.org/en/latest/topics/shell.html) to debug the faulty xpath in your terminal, e.g.:
```
scrapy shell '<url_to_event_page>' --nolog
>>> response.xpath('//section[1]/div/article/div[1]/h3/a/@href').extract_first()
```
