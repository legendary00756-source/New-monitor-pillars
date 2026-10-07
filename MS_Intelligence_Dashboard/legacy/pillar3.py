# pillar3.py - Pillar 3 (Tech Hiring) functions
import time
import logging
import feedparser
import re
from urllib.parse import quote_plus, urlparse
from config import *
from utils import *
from duplicate_tracker import GLOBAL_DUPLICATE_TRACKER
from ai_summaries import add_ai_summaries_p3

logger = logging.getLogger(__name__)

def search_field_google_news_p3(field_name, keywords):
    """Search Google News for tech hiring by field"""
    results = []
    
    for keyword in keywords[:12]:
        try:
            query = f'"{keyword}" UAE'
            rss_url = f"https://news.google.com/rss/search?q={quote_plus(query)}+when:1d&hl=en-US&gl=AE&ceid=AE:en"
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries[:20]:
                if not is_within_24_hours(entry.get("published", "")):
                    continue
                
                headline = clean_text(entry.get("title", ""))
                summary = clean_text(entry.get("summary", ""))
                url = entry.get("link", "")
                
                # Skip LinkedIn URLs in this function
                if "linkedin.com" in url:
                    continue
                
                # Check global duplicates
                if GLOBAL_DUPLICATE_TRACKER.is_duplicate(url, headline):
                    continue
                
                content = (headline + " " + summary).lower()
                if not any(uae_word in content for uae_word in UAE_KEYWORDS_P3):
                    continue
                
                hiring_terms = ['hiring', 'job', 'vacancy', 'position', 'role', 'opportunity', 'opening']
                if not any(term in content for term in hiring_terms):
                    continue
                
                results.append({
                    "headline": headline,
                    "summary": summary[:800],
                    "url": url,
                    "published": entry.get("published", ""),
                    "source": "Google News",
                    "field": field_name,
                    "type": "Tech Hiring",
                    "pillar": "P3_TECH"
                })
            
            time.sleep(0.2)
                
        except Exception as e:
            logger.debug(f"Error searching {field_name}: {str(e)[:50]}")
            continue
    
    return results

def search_field_linkedin_p3(field_name, keywords):
    """Search LinkedIn for tech hiring by field"""
    results = []
    
    for keyword in keywords[:8]:
        try:
            query = f'site:linkedin.com/posts "{keyword}" UAE'
            rss_url = f"https://news.google.com/rss/search?q={quote_plus(query)}+when:2d&hl=en-US&gl=AE&ceid=AE:en"
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries[:15]:
                if not is_within_24_hours(entry.get("published", "")):
                    continue
                
                headline = clean_text(entry.get("title", ""))
                summary = clean_text(entry.get("summary", ""))
                url = entry.get("link", "")
                
                # Only process LinkedIn URLs
                if "linkedin.com" not in url:
                    continue
                
                # Check global duplicates
                if GLOBAL_DUPLICATE_TRACKER.is_duplicate(url, headline):
                    continue
                
                content = (headline + " " + summary).lower()
                hiring_indicators = ['hiring', 'job', 'opportunity', 'vacancy', 'position', 'role']
                
                if any(indicator in content for indicator in hiring_indicators):
                    results.append({
                        "headline": headline,
                        "summary": summary[:800],
                        "url": url,
                        "published": entry.get("published", ""),
                        "source": "LinkedIn",
                        "field": field_name,
                        "type": "Tech Hiring",
                        "pillar": "P3_TECH"
                    })
            
            time.sleep(0.3)
                
        except Exception as e:
            logger.debug(f"Error searching LinkedIn {field_name}: {str(e)[:50]}")
            continue
    
    return results

def search_market_news_p3():
    """Search for market news in P3"""
    results = []
    
    for keyword in MARKET_KEYWORDS_P3[:25]:
        try:
            queries = [f'UAE {keyword}', f'Dubai {keyword}']
            
            for query in queries[:2]:
                rss_url = f"https://news.google.com/rss/search?q={quote_plus(query)}+when:1d&hl=en-US&gl=AE&ceid=AE:en"
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries[:25]:
                    if not is_within_24_hours(entry.get("published", "")):
                        continue
                    
                    headline = clean_text(entry.get("title", ""))
                    summary = clean_text(entry.get("summary", ""))
                    url = entry.get("link", "")
                    
                    # Check global duplicates
                    if GLOBAL_DUPLICATE_TRACKER.is_duplicate(url, headline):
                        continue
                    
                    # Must be from trusted source
                    try:
                        domain = urlparse(url).netloc.lower()
                        if not any(trusted in domain for trusted in TRUSTED_HOSTS_P3):
                            continue
                    except:
                        continue
                    
                    content = (headline + " " + summary).lower()
                    if not any(uae_word in content for uae_word in UAE_KEYWORDS_P3):
                        continue
                    
                    market_terms = ['policy', 'law', 'regulation', 'announce', 'launch', 'opening', 'firm', 'agency', 'search']
                    if not any(term in content for term in market_terms):
                        continue
                    
                    # Skip pure tech hiring articles
                    if any(tech_term in content for tech_term in ['AI', 'cybersecurity', 'cloud', 'devops', 'fintech', 'blockchain']):
                        if 'hiring' in content or 'job' in content:
                            continue
                    
                    # Categorize the article
                    category = "Policy Update"
                    if any(term in content for term in ['executive search', 'headhunting', 'recruitment agency', 'talent consultancy']):
                        category = "Executive Search Firm"
                    elif any(term in content for term in ['salary', 'wage', 'compensation', 'benefits']):
                        category = "Compensation Update"
                    elif any(term in content for term in ['working hours', 'leave', 'remote work']):
                        category = "Work Policy"
                    
                    results.append({
                        "headline": headline,
                        "summary": summary[:800],
                        "url": url,
                        "published": entry.get("published", ""),
                        "source": feed.source.get('title', 'Google News') if hasattr(feed, 'source') else 'Google News',
                        "type": "Market News",
                        "category": category,
                        "pillar": "P3_MARKET"
                    })
                
                time.sleep(0.2)
                
        except Exception as e:
            logger.debug(f"Error searching market - {keyword}: {str(e)[:50]}")
            continue
    
    return results

# pillar3.py - Fix progress reporting

# In the fetch_tech_hiring_news_p3() function:
def fetch_tech_hiring_news_p3():
    """Main function to fetch tech hiring news"""
    logger.info("🔍 Fetching Tech Hiring News...")
    all_articles = []
    
    for field_name, keywords in TECH_FIELDS_P3.items():
        logger.info(f"  Searching {field_name}...")
        
        google_results = search_field_google_news_p3(field_name, keywords)
        linkedin_results = search_field_linkedin_p3(field_name, keywords)
        
        field_articles = google_results + linkedin_results
        
        seen_urls = set()
        unique_field_articles = []
        
        for article in field_articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_field_articles.append(article)
        
        logger.info(f"    Total unique: {len(unique_field_articles)} articles")
        all_articles.extend(unique_field_articles)
        
        time.sleep(0.5)
    
    # Add AI summaries
    all_articles = add_ai_summaries_p3(all_articles, GROQ_API_KEY_P3)
    
    logger.info(f"✅ Tech Hiring total: {len(all_articles)} articles")
    return all_articles

# In the fetch_market_news_p3() function:
def fetch_market_news_p3():
    """Main function to fetch market news for P3"""
    logger.info("🔍 Fetching Market News...")
    market_articles = search_market_news_p3()
    
    seen_urls = set()
    unique_market_articles = []
    
    for article in market_articles:
        if article['url'] not in seen_urls:
            seen_urls.add(article['url'])
            unique_market_articles.append(article)
    
    # Add AI summaries
    unique_market_articles = add_ai_summaries_p3(unique_market_articles, GROQ_API_KEY_P3)
    
    logger.info(f"✅ Market News: {len(unique_market_articles)} articles")
    return unique_market_articles

    # Add AI summaries
    unique_market_articles = add_ai_summaries_p3(unique_market_articles, GROQ_API_KEY_P3)
    
    prog(f"✅ Market News: {len(unique_market_articles)} articles")
    return unique_market_articles