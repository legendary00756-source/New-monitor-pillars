# pillar2.py - Pillar 2 functions
import pandas as pd
import time
import logging
import feedparser
from urllib.parse import quote_plus
from config import *
from utils import *
from duplicate_tracker import GLOBAL_DUPLICATE_TRACKER
from ai_summaries import add_ai_summaries_p2

logger = logging.getLogger(__name__)

def load_jurisdictions_p2():
    """Load entity names from Excel file for P2"""
    try:
        df = pd.read_excel(EXCEL_FILE_P2)
        names = df.iloc[:, 0].dropna().astype(str).tolist()
    except Exception as e:
        logger.error(f"Error reading Excel for P2: {e}")
        names = []
    mapping = {name.lower().strip(): name.strip() for name in names}
    return names, mapping

JURISDICTION_NAMES_P2, JURISDICTION_MAP_P2 = load_jurisdictions_p2()
JURISDICTION_KEYWORDS_P2 = list(JURISDICTION_MAP_P2.keys())

# ADD THIS HELPER FUNCTION TO CHECK UAE CONNECTION
def has_uae_connection(text):
    """Check if text has UAE connection"""
    text_lower = text.lower()
    
    # UAE keywords from config (assuming UAE_KEYWORDS_P2 exists in config)
    uae_keywords = UAE_KEYWORDS_P2 + [
        'uae', 'united arab emirates', 'dubai', 'abu dhabi', 'sharjah',
        'ajman', 'fujairah', 'ras al khaimah', 'umm al quwain', 'emirati',
        'emirates', 'gulf cooperation council', 'gcc', 'middle east',
        'uae-based', 'uae\'s', 'dubai-based', 'abu dhabi-based'
    ]
    
    return any(kw in text_lower for kw in uae_keywords)

def score_market_item_p2(headline, summary):
    text = (headline + " " + summary).lower()
    
    # Exclusions - ADD INDIAN EXCLUSIONS
    INDIAN_EXCLUSIONS = [
        'india', 'indian', 'delhi', 'mumbai', 'chennai', 'bangalore', 
        'kolkata', 'hyderabad', 'pune', 'ahmedabad', 'modi', 'indian government',
        'indian economy', 'indian market', 'bse', 'nse', 'sensex', 'nifty',
        'rupee', 'indian rupee', 'reserve bank of india', 'rbi'
    ]
    
    if any(excl in text for excl in ALL_EXCLUSIONS_P2 + INDIAN_EXCLUSIONS):
        return False
    
    # MUST HAVE UAE CONNECTION
    if not has_uae_connection(text):
        return False
    
    # Score finance and wealth keywords
    score = 0
    for kw in WEALTH_KEYWORDS_P2 + FINANCE_SIGNALS_P2:
        if kw in text:
            score += 1
    
    return score >= 2

# ADD THIS FUNCTION TO FILTER ENTITY NEWS FOR UAE CONNECTION
def filter_uae_entity_news(items, entity_name):
    """Filter entity news to ensure UAE connection"""
    filtered_items = []
    
    for item in items:
        text = (item.get("headline", "") + " " + item.get("summary", "")).lower()
        
        # Check for UAE connection
        if has_uae_connection(text):
            filtered_items.append(item)
        else:
            # Also check if entity name itself suggests UAE connection
            entity_lower = entity_name.lower()
            uae_indicators = ['dubai', 'abu dhabi', 'uae', 'emirates', 'emirati']
            if any(indicator in entity_lower for indicator in uae_indicators):
                # If entity name has UAE indicators, include the news
                filtered_items.append(item)
    
    return filtered_items

def fetch_google_news_market_p2(query):
    """Fetch Google News for market queries"""
    rss = f"https://news.google.com/rss/search?q={quote_plus(query)}+when:1d&hl=en-US&gl=AE&ceid=AE:en"
    feed = feedparser.parse(rss)
    results = []
    
    for e in feed.entries[:50]:
        pub = e.get("published", "")
        if not is_recent_publication_only(pub, e.get("link", "")):
            continue
        
        headline = clean_text(e.get("title", ""))
        summary = clean_text(e.get("summary", ""))
        
        if not score_market_item_p2(headline, summary):
            continue
        
        results.append({
            "headline": headline,
            "summary": summary[:900],
            "url": clean_google_linkedin(e.get("link", "")),
            "published": pub,
            "source": "Google News"
        })
    return results

def fetch_market_news_p2():
    """Main function to fetch P2 market news"""
    pool = []

    # RSS feeds
    for url in RSS_FEEDS_P2:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:60]:
                pub = e.get("published", e.get("updated", ""))
                if not is_recent_publication_only(pub, e.get("link", "")):
                    continue
                
                headline = clean_text(e.get("title", ""))
                summary = clean_text(e.get("summary", e.get("description", "")))
                
                if not score_market_item_p2(headline, summary):
                    continue
                
                # Check global duplicates
                if GLOBAL_DUPLICATE_TRACKER.is_duplicate(e.get("link", ""), headline):
                    continue
                    
                pool.append({
                    "headline": headline,
                    "summary": summary[:900],
                    "url": e.get("link", ""),
                    "published": pub,
                    "source": e.get("source", {}).get("title", url),
                    "pillar": "P2_MARKET"
                })
        except Exception as ex:
            logger.debug(f"RSS market fetch error (P2): {ex}")
        time.sleep(0.18)

    # Google News Sources
    for q in GOOGLE_NEWS_SOURCES_P2:
        try:
            articles = fetch_google_news_market_p2(q)
            for a in articles:
                if GLOBAL_DUPLICATE_TRACKER.is_duplicate(a["url"], a["headline"]):
                    continue
                a["pillar"] = "P2_MARKET"
                pool.append(a)
        except Exception as ex:
            logger.debug(f"Google News market error (P2): {ex}")
        time.sleep(0.2)

    # Deduplicate by title-stem
    seen_stems, out = set(), []
    for a in sorted(pool, key=lambda x: x["published"], reverse=True):
        stem = title_stem(a["headline"])
        if stem in seen_stems:
            continue
        seen_stems.add(stem)
        out.append(a)
        if len(out) >= 40:
            break
    
    # Add AI summaries
    out = add_ai_summaries_p2(out, GROQ_API_KEY_P2)
    
    return out

def fetch_linkedin_posts_p2(company):
    """Fetch LinkedIn posts for a company"""
    results = []
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
            pub = e.get("published", "")
            if not is_recent_publication_only(pub, e.get("link", "")):
                continue
            
            results.append({
                "headline": clean_text(e.get("title", "")),
                "summary": clean_text(e.get("summary", ""))[:1000],
                "url": clean_google_linkedin(e.get("link", "")),
                "published": pub,
                "source": "LinkedIn"
            })
    
    # Deduplicate
    final = []
    for item in results:
        if not any(similar(item["headline"], x["headline"]) > 0.85 for x in final):
            final.append(item)
    return final

def fetch_google_news_p2(company):
    """Fetch Google News for a company"""
    out = []
    query = f'"{company}"'
    rss = f"https://news.google.com/rss/search?q={quote_plus(query)}+when:1d&hl=en-US&gl=AE&ceid=AE:en"
    feed = feedparser.parse(rss)
    
    for e in feed.entries[:40]:
        pub = e.get("published", "")
        headline = clean_text(e.get("title", ""))
        summary = clean_text(e.get("summary", ""))
        
        if not is_recent_publication_only(pub, e.get("link", "")):
            continue
        
        out.append({
            "headline": headline,
            "summary": summary,
            "url": e.get("link", ""),
            "published": pub,
            "source": "Google News"
        })
    return out

def fetch_all_entity_news_p2():
    """Main function to fetch all entity news for P2"""
    try:
        df = pd.read_excel(EXCEL_FILE_P2)
        companies = df.iloc[:, 0].dropna().astype(str).tolist()
    except Exception as e:
        logger.error(f"Error reading Excel for P2: {e}")
        return {}
    
    entity_map = {}
    for name in companies:
        items = []
        
        try:
            items += fetch_linkedin_posts_p2(name)
        except Exception as e:
            logger.debug(f"LinkedIn error for {name} (P2): {e}")
        
        try:
            items += fetch_google_news_p2(name)
        except Exception as e:
            logger.debug(f"Google News error for {name} (P2): {e}")
        
        # FILTER FOR UAE CONNECTION
        items = filter_uae_entity_news(items, name)
        
        final = []
        for x in items:
            # Check global duplicates
            if GLOBAL_DUPLICATE_TRACKER.is_duplicate(x["url"], x["headline"]):
                continue
                
            # Deduplicate within this entity
            if not any(similar(x["headline"], y["headline"]) > 0.85 for y in final):
                x["pillar"] = "P2_ENTITY"
                final.append(x)
        
        if final:
            # Add AI summaries
            final = add_ai_summaries_p2(final, GROQ_API_KEY_P2)
            entity_map[name] = final
        
        time.sleep(0.3)
    
    return entity_map