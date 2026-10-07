# utils.py - Utility functions
import re
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin, quote_plus
import requests
from bs4 import BeautifulSoup
import dateutil.parser
from difflib import SequenceMatcher

SESSION = requests.Session()
SESSION.headers.update({"User-Agent":"Mozilla/5.0 (compatible; NewsBot/1.0)"})

def clean_text(html_text):
    """Extract clean text from HTML"""
    if not html_text: 
        return ""
    return ' '.join(BeautifulSoup(html_text, "html.parser").get_text().split())

def parse_relaxed_date(date_str):
    """Parse date strings with flexible format"""
    if not date_str: 
        return None
    try:
        if any(k in date_str.lower() for k in ["minute", "hour"]):
            match = re.search(r'(\d+)\s*hour', date_str.lower())
            if match:
                hours_ago = int(match.group(1))
            else:
                match = re.search(r'(\d+)\s*minute', date_str.lower())
                if match:
                    hours_ago = int(match.group(1)) / 60
                else:
                    hours_ago = 2
            return datetime.now() - timedelta(hours=hours_ago)
        
        dt = dateutil.parser.parse(date_str)
        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception as e:
        return None

def is_within_24_hours(pub_date_str):
    """Check if publication date is within 24 hours"""
    if not pub_date_str: 
        return False
    pub_dt = parse_relaxed_date(pub_date_str)
    if not pub_dt:
        return False
    time_diff = datetime.now() - pub_dt
    return time_diff.total_seconds() <= 86400

def is_recent_publication_only(pub_date_str, article_url=""):
    """Check if article is recent with additional URL validation"""
    if not pub_date_str: 
        return False
    if not is_within_24_hours(pub_date_str):
        return False
    
    if article_url:
        match = re.search(r'/article/(\d+)/', article_url)
        if match:
            article_id = int(match.group(1))
            if article_id < 50000:
                return False
    return True

def similar(a, b):
    """Calculate similarity ratio between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def clean_google_linkedin(url):
    """Clean Google News LinkedIn URLs"""
    if "linkedin.com/" in url:
        start = url.find("https://")
        if start != -1: 
            return url[start:].split("&")[0]
    return url

def title_stem(text):
    """Create a title stem for deduplication"""
    if not text: 
        return ""
    return " ".join(re.findall(r'\w+', text.lower())[:6])

def normalize_url(url):
    """Normalize URL for deduplication"""
    if not url: 
        return ""
    return url.split('?')[0].rstrip('/')

def get_time_ago(pub_date_str):
    """Get human-readable time ago string"""
    pub_dt = parse_relaxed_date(pub_date_str)
    if not pub_dt:
        return "Recent"
    
    time_ago = datetime.now() - pub_dt
    hours_ago = int(time_ago.total_seconds() // 3600)
    
    if hours_ago < 1:
        return "Less than an hour ago"
    elif hours_ago == 1:
        return "1 hour ago"
    elif hours_ago < 24:
        return f"{hours_ago} hours ago"
    else:
        days_ago = hours_ago // 24
        return f"{days_ago} days ago"

def trusted_url_p1(url, TRUSTED_HOSTS):
    """Check if URL is from trusted host"""
    if not url: 
        return False
    try:
        host = urlparse(url).netloc.lower()
        return host in TRUSTED_HOSTS
    except: 
        return False