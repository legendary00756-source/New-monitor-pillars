# e7_real_estate.py - Updated with comprehensive real estate logic
import time
import logging
import feedparser
import re
from urllib.parse import quote_plus, urlparse
from config import *
from utils import *
from duplicate_tracker import GLOBAL_DUPLICATE_TRACKER
from ai_summaries import add_ai_summaries_e7

logger = logging.getLogger(__name__)

# =============================================================================
# CONTENT FILTERING FUNCTIONS
# =============================================================================

def filter_unwanted_content(headline, summary):
    """Filter out hiring posts and unwanted content"""
    text = (headline + " " + summary).lower()
    
    # Check for unwanted keywords
    for keyword in UNWANTED_KEYWORDS_E7:
        if keyword.lower() in text:
            return False
    
    # Additional hiring pattern matching
    hiring_patterns = [
        r'\bhiring\b', r'\bcareer\b', r'\bjob\b', r'\bvacancy\b',
        r'\brecruitment\b', r'\brecruit\b', r'\bapply now\b',
        r'\bjoin our team\b', r'\bwork with us\b', r'\bwe are hiring\b',
        r'\bnow hiring\b', r'\bjob opening\b', r'\bcareer opportunity\b',
        r'\bjob vacancy\b', r'\bvacant position\b', r'\blooking for\b',
        r'\bwanted\b', r'\bimmediate opening\b', r'\burgent hiring\b'
    ]
    
    for pattern in hiring_patterns:
        if re.search(pattern, text):
            return False
    
    # Check if it's actually about real estate
    real_estate_indicators = ['real estate', 'property', 'villa', 'apartment', 
                             'development', 'project', 'investment', 'market',
                             'rent', 'sale', 'buy', 'purchase', 'developer',
                             'housing', 'residential', 'commercial', 'office',
                             'retail', 'industrial', 'logistics', 'warehouse']
    
    has_real_estate_content = any(indicator in text for indicator in real_estate_indicators)
    
    return has_real_estate_content

def categorize_article(headline, summary, url):
    """Categorize article as Market or Developer update"""
    text = (headline + " " + summary).lower()
    
    # Developer articles
    developer_score = 0
    for keyword in DEVELOPER_KEYWORDS_E7:
        if keyword in text:
            developer_score += 1
    
    # Check for developer names in URL
    url_lower = url.lower()
    for developer in UAE_REAL_PLAYERS_E7:
        if developer.replace('-', ' ') in text or developer in url_lower:
            developer_score += 3
    
    # Market articles
    market_score = 0
    for keyword in MARKET_KEYWORDS_E7:
        if keyword in text:
            market_score += 1
    
    # LinkedIn posts are usually developer updates
    if 'linkedin.com' in url:
        developer_score += 2
    
    # Developer press releases
    if any(term in url for term in ['.com/news/', '/press-release', '/announcement']):
        developer_score += 1
    
    if developer_score > market_score:
        return "developer"
    else:
        return "market"

def score_and_filter(headline, summary):
    """Basic filtering for UAE real estate content"""
    txt = ((headline or "") + " " + (summary or "")).lower()
    
    # Must be about UAE
    if not any(k in txt for k in GEO_KEYWORDS_E7):
        return False
    
    # Must NOT be unwanted content
    if not filter_unwanted_content(headline, summary):
        return False
    
    # Must be about real estate
    all_keywords = MARKET_KEYWORDS_E7 + DEVELOPER_KEYWORDS_E7
    score = sum(1 for k in all_keywords if k in txt)
    return score >= 2

# =============================================================================
# NEWS FETCHING FUNCTIONS
# =============================================================================

def fetch_newsdata_io(query):
    """Fetch news from NewsData.io API"""
    articles = []
    if not NEWSDATA_KEY:
        return articles
    
    try:
        url = "https://newsdata.io/api/1/news"
        params = {
            "q": query, 
            "language": "en", 
            "from_date": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'), 
            "apikey": NEWSDATA_KEY
        }
        r = SESSION.get(url, params=params, timeout=15).json()
        
        for a in r.get('results', []):
            pub = a.get('pubDate','')
            if not is_within_24_hours(pub):
                continue
            
            headline = clean_text(a.get('title',''))
            summary  = clean_text(a.get('description',''))
            
            if not score_and_filter(headline, summary):
                continue
            
            # Check global duplicates
            if GLOBAL_DUPLICATE_TRACKER.is_duplicate(a.get('link',''), headline):
                continue
            
            articles.append({
                "headline": headline,
                "summary": summary,
                "url": a.get('link',''),
                "published": pub,
                "source": a.get('source_id','NewsData.io'),
                "pillar": "E7_REAL_ESTATE"
            })
    except Exception as e:
        logger.debug(f"NewsData.io error: {e}")
    
    return articles

def fetch_mediastack(query):
    """Fetch news from Mediastack API"""
    articles = []
    if not MEDIASTACK_KEY:
        return articles
    
    try:
        url = "http://api.mediastack.com/v1/news"
        params = {
            "keywords": query, 
            "countries": "ae", 
            "languages": "en", 
            "date": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'), 
            "limit": 80, 
            "access_key": MEDIASTACK_KEY
        }
        r = SESSION.get(url, params=params, timeout=15).json()
        
        for a in r.get('data', []):
            pub = a.get('published_at','')
            if not is_within_24_hours(pub):
                continue
            
            headline = clean_text(a.get('title',''))
            summary  = clean_text(a.get('description',''))
            
            if not score_and_filter(headline, summary):
                continue
            
            # Check global duplicates
            if GLOBAL_DUPLICATE_TRACKER.is_duplicate(a.get('url',''), headline):
                continue
            
            articles.append({
                "headline": headline,
                "summary": summary,
                "url": a.get('url',''),
                "published": pub,
                "source": a.get('author','Mediastack'),
                "pillar": "E7_REAL_ESTATE"
            })
    except Exception as e:
        logger.debug(f"Mediastack error: {e}")
    
    return articles

def fetch_currentsapi(query):
    """Fetch news from CurrentsAPI"""
    articles = []
    if not CURRENTS_KEY:
        return articles
    
    try:
        url = "https://api.currentsapi.services/v1/search"
        params = {
            "keywords": query, 
            "language": "en", 
            "start_date": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'), 
            "page_size": 80, 
            "apiKey": CURRENTS_KEY
        }
        r = SESSION.get(url, params=params, timeout=15).json()
        
        for a in r.get('news', []):
            pub = a.get('published','')
            if not is_within_24_hours(pub):
                continue
            
            headline = clean_text(a.get('title',''))
            summary  = clean_text(a.get('description',''))
            
            if not score_and_filter(headline, summary):
                continue
            
            # Check global duplicates
            if GLOBAL_DUPLICATE_TRACKER.is_duplicate(a.get('url',''), headline):
                continue
            
            articles.append({
                "headline": headline,
                "summary": summary,
                "url": a.get('url',''),
                "published": pub,
                "source": a.get('author','CurrentsAPI'),
                "pillar": "E7_REAL_ESTATE"
            })
    except Exception as e:
        logger.debug(f"CurrentsAPI error: {e}")
    
    return articles

def fetch_rss_feeds_e7():
    """Fetch real estate news from RSS feeds"""
    articles = []
    
    for feed_url in RSS_FEEDS_E7:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:80]:
                pub = entry.get('published', entry.get('updated', ''))
                if not is_within_24_hours(pub):
                    continue
                    
                headline = clean_text(entry.get('title', ''))
                summary = clean_text(entry.get('summary', entry.get('description', '')))
                
                if not score_and_filter(headline, summary):
                    continue
                
                # Check global duplicates
                if GLOBAL_DUPLICATE_TRACKER.is_duplicate(entry.get('link', ''), headline):
                    continue
                
                articles.append({
                    "headline": headline,
                    "summary": summary,
                    "url": entry.get('link', ''),
                    "published": pub,
                    "source": feed.feed.get('title', feed_url),
                    "pillar": "E7_REAL_ESTATE"
                })
        except Exception as e:
            logger.debug(f"RSS feed error {feed_url}: {e}")
        time.sleep(0.15)
    
    return articles

def fetch_linkedin_realestate_posts_e7(slug):
    """Fetch LinkedIn posts for real estate developers"""
    if not slug:
        return []
    
    try:
        # Using Google News as fallback for LinkedIn posts
        return fetch_linkedin_google_re_posts_e7(slug)
    except Exception as e:
        logger.debug(f"LinkedIn RE RSS error: {slug} | {e}")
        return []

def fetch_linkedin_google_re_posts_e7(name):
    """Fetch LinkedIn posts via Google News for real estate"""
    if not name:
        return []
    
    queries = [
        f'"{name}" UAE site:linkedin.com/posts',
        f'"{name}" "launch" OR "project" OR "development" site:linkedin.com/posts'
    ]
    
    articles = []
    for q in queries:
        try:
            for start in range(1, 2*40, 40):
                rss = f"https://news.google.com/rss/search?q={quote_plus(q)}+when:1d&hl=en-US&gl=AE&ceid=AE:en&start={start}"
                feed = feedparser.parse(rss)
                
                for entry in feed.entries[:40]:
                    pub = entry.get('published', '')
                    if not is_within_24_hours(pub):
                        continue
                        
                    headline = clean_text(entry.get('title', ''))
                    summary = clean_text(entry.get('summary', ''))[:900]
                    
                    if not score_and_filter(headline, summary):
                        continue
                    
                    # Check global duplicates
                    if GLOBAL_DUPLICATE_TRACKER.is_duplicate(entry.get('link', ''), headline):
                        continue
                    
                    articles.append({
                        "headline": headline,
                        "summary": summary,
                        "url": entry.get('link', ''),
                        "published": pub,
                        "source": "LinkedIn",
                        "pillar": "E7_REAL_ESTATE"
                    })
        except Exception as e:
            logger.debug(f"LinkedIn RE Google-RSS error: {name} | {e}")
    
    return articles

def fetch_google_news_e7(query, pages=2):
    """Fetch Google News for real estate"""
    articles = []
    
    try:
        for start in range(1, pages*40, 40):
            q = quote_plus(query)
            rss = f"https://news.google.com/rss/search?q={q}+when:1d&hl=en-US&gl=AE&ceid=AE:en&start={start}"
            feed = feedparser.parse(rss)
            
            for entry in feed.entries[:40]:
                pub = entry.get('published', '')
                if not is_within_24_hours(pub):
                    continue
                    
                headline = clean_text(entry.get('title', ''))
                summary = clean_text(entry.get('summary', ''))
                
                if not score_and_filter(headline, summary):
                    continue
                
                # Check global duplicates
                if GLOBAL_DUPLICATE_TRACKER.is_duplicate(entry.get('link', ''), headline):
                    continue
                
                articles.append({
                    "headline": headline,
                    "summary": summary,
                    "url": entry.get('link', ''),
                    "published": pub,
                    "source": entry.get('source', {}).get('title', 'Google News'),
                    "pillar": "E7_REAL_ESTATE"
                })
    except Exception as e:
        logger.debug(f"Google RSS error: {e}")
    
    return articles

def fetch_all_real_estate_news_e7():
    """Main function to fetch all real estate news - UPDATED WITH NEW LOGIC"""
    logger.info("🏢 Fetching Real Estate News (E7)...")
    
    all_articles = []
    
    # 1. Fetch from RSS feeds (100+ feeds)
    logger.info("  📰 RSS Feeds (100+ sources)...")
    rss_articles = fetch_rss_feeds_e7()
    all_articles.extend(rss_articles)
    logger.info(f"    Found: {len(rss_articles)} articles")
    
    # 2. Fetch from various APIs
    logger.info("  🔍 News APIs...")
    
    # NewsData.io
    newsdata_query = "UAE real estate OR property OR off-plan OR villa OR apartment OR rental OR reit OR developer OR market report OR forecast"
    newsdata_articles = fetch_newsdata_io(newsdata_query)
    all_articles.extend(newsdata_articles)
    logger.info(f"    NewsData.io: {len(newsdata_articles)} articles")
    time.sleep(0.5)
    
    # Mediastack
    mediastack_query = "UAE real estate OR property OR villa OR apartment OR construction OR market"
    mediastack_articles = fetch_mediastack(mediastack_query)
    all_articles.extend(mediastack_articles)
    logger.info(f"    Mediastack: {len(mediastack_articles)} articles")
    time.sleep(0.5)
    
    # CurrentsAPI
    currents_query = "UAE real estate OR property OR development OR investment OR developer OR market size"
    currents_articles = fetch_currentsapi(currents_query)
    all_articles.extend(currents_articles)
    logger.info(f"    CurrentsAPI: {len(currents_articles)} articles")
    time.sleep(0.5)
    
    # 3. Fetch from Google News with enhanced market queries
    logger.info("  🔍 Google News (enhanced queries)...")
    market_queries = [
        '"UAE real estate" market report OR forecast OR analysis',
        '"Dubai property" transactions OR deals OR investment',
        '"UAE luxury real estate" market size OR valuation',
        '"Abu Dhabi property" market OR trends OR outlook',
        '"PropertyPistol" OR "Mordor Intelligence" UAE real estate'
    ]
    
    for query in market_queries:
        articles = fetch_google_news_e7(query, pages=2)
        all_articles.extend(articles)
        logger.info(f"    Query '{query[:30]}...': {len(articles)} articles")
        time.sleep(1)
    
    # 4. Fetch LinkedIn posts for developers
    logger.info("  👔 LinkedIn Developer Posts...")
    for slug in UAE_REAL_PLAYERS_E7[:15]:  # Limit to 15 to avoid rate limiting
        articles = fetch_linkedin_realestate_posts_e7(slug)
        all_articles.extend(articles)
        time.sleep(0.1)
    
    logger.info(f"    LinkedIn: {len(all_articles) - len(rss_articles) - len(newsdata_articles) - len(mediastack_articles) - len(currents_articles)} developer articles")
    
    # 5. Deduplicate by URL and categorize
    logger.info("  🏷️ Categorizing and deduplicating...")
    seen_urls = set()
    market_articles = []
    developer_articles = []
    
    for article in all_articles:
        if article['url'] in seen_urls:
            continue
        seen_urls.add(article['url'])
        
        # Categorize
        category = categorize_article(article["headline"], article["summary"], article["url"])
        article["category"] = category
        
        if category == "market":
            market_articles.append(article)
        else:
            developer_articles.append(article)
    
    # 6. Add AI summaries
    logger.info("  🤖 Adding AI summaries...")
    market_articles = add_ai_summaries_e7(market_articles, "market", GROQ_API_KEY_E7)
    developer_articles = add_ai_summaries_e7(developer_articles, "developer", GROQ_API_KEY_E7)
    
    logger.info(f"✅ Real Estate: {len(market_articles)} market, {len(developer_articles)} developer articles")
    
    # Log sample headlines
    if market_articles:
        logger.info(f"  Sample market headlines:")
        for i, article in enumerate(market_articles[:3], 1):
            logger.info(f"    {i}. {article['headline'][:80]}...")
    
    if developer_articles:
        logger.info(f"  Sample developer headlines:")
        for i, article in enumerate(developer_articles[:3], 1):
            logger.info(f"    {i}. {article['headline'][:80]}...")
    
    return {
        "market": market_articles,
        "developer": developer_articles
    }