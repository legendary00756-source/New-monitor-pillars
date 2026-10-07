# pillar1.py - Pillar 1 functions
import pandas as pd
import time
import logging
import feedparser
from urllib.parse import quote_plus
from config import *
from utils import *
from duplicate_tracker import GLOBAL_DUPLICATE_TRACKER
from ai_summaries import add_ai_summaries_p1

logger = logging.getLogger(__name__)

def load_jurisdictions_p1():
    """Load entity names from Excel file for P1"""
    try:
        df = pd.read_excel(EXCEL_FILE_P1)
        names = df.iloc[:, 0].dropna().astype(str).tolist()
    except Exception as e:
        logger.error(f"Error reading Excel for P1: {e}")
        names = []
    mapping = {name.lower().strip(): name.strip() for name in names}
    return names, mapping

JURISDICTION_NAMES_P1, JURISDICTION_MAP_P1 = load_jurisdictions_p1()

def score_market_item_p1(headline, summary, url=""):
    """Score market items for P1"""
    txt = ((headline or "") + " " + (summary or "")).lower()
    
    # Exclusions
    if any(ex in txt for ex in ALL_EXCLUSIONS_P1): 
        return False
    
    # Must contain UAE keywords
    if not any(k in txt for k in UAE_KEYWORDS_P1): 
        return False
    
    # Special case for DIFC/ADGM licensing
    if any(k in txt for k in ['difc', 'adgm']) and any(w in txt for w in ['license', 'licence', 'regulation', 'regulatory', 'authorised']):
        return True
    
    # Score finance, wealth, and policy keywords
    finance = sum(1 for k in FINANCE_SIGNALS_P1 if k in txt)
    wealth  = sum(1 for k in WEALTH_KEYWORDS_P1 if k in txt)
    policy  = sum(1 for k in ['policy','regulation','tax','economic','fdi','inflation','gdp','interest rate','central bank'] if k in txt)
    
    if finance == 0 and wealth == 0 and policy == 0: 
        return False
    
    return (finance * 3 + wealth * 2 + policy * 2) >= 5

def _newsapi_market(q):
    """Fetch market news from NewsAPI"""
    if not NEWS_API_KEY: 
        return []
    
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": q, 
        "language": "en", 
        "pageSize": 80,
        "from": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        "sortBy": "publishedAt", 
        "apiKey": NEWS_API_KEY
    }
    
    try:
        r = SESSION.get(url, params=params, timeout=15).json()
        articles = []
        
        for a in r.get("articles", []):
            if is_recent_publication_only(a.get("publishedAt", ""), a.get("url", "")):
                articles.append({
                    "headline": clean_text(a.get("title", "")),
                    "summary": clean_text(a.get("description", ""))[:900],
                    "url": a.get("url", ""),
                    "published": a.get("publishedAt", ""),
                    "source": a.get("source", {}).get("name", "NewsAPI")
                })
        return articles
    except Exception as e:
        logger.error(f"NewsAPI error: {e}")
        return []

def fetch_google_news_market_p1(query):
    """Fetch Google News for market queries"""
    rss = f"https://news.google.com/rss/search?q={quote_plus(query)}+when:1d&hl=en-US&gl=AE&ceid=AE:en"
    feed = feedparser.parse(rss)
    results = []
    
    for e in feed.entries[:50]:
        pub_date = e.get("published", "")
        if not is_recent_publication_only(pub_date, e.get("link", "")): 
            continue
        
        headline = clean_text(e.get("title", ""))
        summary = clean_text(e.get("summary", ""))
        url_link = clean_google_linkedin(e.get("link", ""))
        
        if not score_market_item_p1(headline, summary, url_link): 
            continue
        
        if not trusted_url_p1(url_link, TRUSTED_HOSTS_P1): 
            continue
            
        results.append({
            "headline": headline,
            "summary": summary[:900],
            "url": url_link,
            "published": pub_date,
            "source": "Google News"
        })
    return results

def fetch_market_news_p1():
    """Main function to fetch P1 market news"""
    pool, seen_stems, out = [], set(), []
    
    # RSS feeds
    for url in RSS_FEEDS_P1:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:60]:
                pub_date = e.get("published", e.get("updated", ""))
                if not is_recent_publication_only(pub_date, e.get("link", "")): 
                    continue
                
                headline = clean_text(e.get("title", ""))
                summary  = clean_text(e.get("summary", e.get("description", "")))
                url_link = e.get("link", "")
                
                if not score_market_item_p1(headline, summary, url_link): 
                    continue
                
                if not trusted_url_p1(url_link, TRUSTED_HOSTS_P1): 
                    continue
                
                # Check global duplicates
                if GLOBAL_DUPLICATE_TRACKER.is_duplicate(url_link, headline):
                    continue
                    
                pool.append({
                    "headline": headline, 
                    "summary": summary[:900],
                    "url": url_link, 
                    "published": pub_date,
                    "source": e.get("source", {}).get("title", url),
                    "pillar": "P1_MARKET"
                })
        except Exception as ex: 
            logger.debug(f"RSS market fetch error: {ex}")
        time.sleep(0.18)

    # NewsAPI
    for q in MARKET_QUERIES_P1:
        if NEWS_API_KEY:
            try: 
                articles = _newsapi_market(q)
                for a in articles:
                    if GLOBAL_DUPLICATE_TRACKER.is_duplicate(a["url"], a["headline"]):
                        continue
                    a["pillar"] = "P1_MARKET"
                    pool.append(a)
            except Exception as ex: 
                logger.debug(f"NewsAPI market error: {ex}")
        time.sleep(0.1)

    # Google News Sources
    for q in GOOGLE_NEWS_SOURCES_P1:
        try: 
            articles = fetch_google_news_market_p1(q)
            for a in articles:
                if GLOBAL_DUPLICATE_TRACKER.is_duplicate(a["url"], a["headline"]):
                    continue
                a["pillar"] = "P1_MARKET"
                pool.append(a)
        except Exception as ex: 
            logger.debug(f"Google News market error: {ex}")
        time.sleep(0.2)

    # Deduplicate and sort
    for a in sorted(pool, key=lambda x: parse_relaxed_date(x["published"]) or datetime.min, reverse=True):
        stem = title_stem(a["headline"])
        if stem in seen_stems: 
            continue
        seen_stems.add(stem)
        out.append(a)
        if len(out) >= 40: 
            break
    
    # Add AI summaries
    out = add_ai_summaries_p1(out, GROQ_API_KEY_P1)
    
    return out

def fetch_linkedin_posts_p1(company):
    """Fetch LinkedIn posts for a company"""
    results, final = [], []
    queries = [
        f'"{company}" site:linkedin.com/posts',
        f'"{company}" "announced" site:linkedin.com/posts',
        f'"{company}" "launched" site:linkedin.com/posts',
        f'"{company}" site:linkedin.com'
    ]
    
    for q in queries:
        rss = f"https://news.google.com/rss/search?q={quote_plus(q)}+when:2d&hl=en-US&gl=AE&ceid=AE:en"
        feed = feedparser.parse(rss)
        
        for e in feed.entries[:40]:
            pub_date = e.get("published", "")
            if not is_recent_publication_only(pub_date, e.get("link", "")):
                continue
                
            results.append({
                "headline": clean_text(e.get("title", "")),
                "summary": clean_text(e.get("summary", ""))[:1000],
                "url": clean_google_linkedin(e.get("link", "")),
                "published": pub_date,
                "source": "LinkedIn"
            })
    
    # Deduplicate
    for item in results:
        if not any(similar(item["headline"], x["headline"]) > 0.85 for x in final):
            final.append(item)
    return final

def fetch_google_news_p1(company):
    """Fetch Google News for a company"""
    out = []
    query = f'"{company}"'
    rss = f"https://news.google.com/rss/search?q={quote_plus(query)}+when:1d&hl=en-US&gl=AE&ceid=AE:en"
    feed = feedparser.parse(rss)
    
    for e in feed.entries[:40]:
        pub_date = e.get("published", "")
        if not is_recent_publication_only(pub_date, e.get("link", "")): 
            continue
            
        out.append({
            "headline": clean_text(e.get("title", "")),
            "summary": clean_text(e.get("summary", "")),
            "url": e.get("link", ""),
            "published": pub_date,
            "source": "Google News"
        })
    return out

def fetch_all_entity_news_p1():
    """Main function to fetch all entity news for P1"""
    try:
        df = pd.read_excel(EXCEL_FILE_P1)
        companies = df.iloc[:, 0].dropna().astype(str).tolist()
    except Exception as e:
        logger.error(f"Error reading Excel for P1: {e}")
        return {}
    
    entity_map = {}
    for name in companies:
        items = []
        
        try:
            items += fetch_linkedin_posts_p1(name)
        except Exception as e:
            logger.debug(f"LinkedIn error for {name}: {e}")
        
        try:
            items += fetch_google_news_p1(name)
        except Exception as e:
            logger.debug(f"Google News error for {name}: {e}")
        
        final = []
        for x in items:
            # Check global duplicates
            if GLOBAL_DUPLICATE_TRACKER.is_duplicate(x["url"], x["headline"]):
                continue
                
            # Deduplicate within this entity
            if not any(similar(x["headline"], y["headline"]) > 0.85 for y in final):
                x["pillar"] = "P1_ENTITY"
                final.append(x)
        
        if final:
            # Add AI summaries
            final = add_ai_summaries_p1(final, GROQ_API_KEY_P1)
            entity_map[name] = final
        
        time.sleep(0.3)
    
    return entity_map