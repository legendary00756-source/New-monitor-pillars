# duplicate_tracker.py - Global duplicate tracker
import re

class DuplicateTracker:
    def __init__(self):
        self.seen_urls = set()
        self.seen_title_stems = set()
    
    def is_duplicate(self, url, headline):
        url_norm = self.normalize_url(url)
        stem = self.title_stem(headline)
        
        if url_norm in self.seen_urls:
            return True
        if stem in self.seen_title_stems:
            return True
            
        self.seen_urls.add(url_norm)
        self.seen_title_stems.add(stem)
        return False
    
    def normalize_url(self, url):
        if not url: 
            return ""
        return url.split('?')[0].rstrip('/')
    
    def title_stem(self, text):
        if not text: 
            return ""
        return " ".join(re.findall(r'\w+', text.lower())[:6])
    
    def reset(self):
        self.seen_urls.clear()
        self.seen_title_stems.clear()

# Global instance
GLOBAL_DUPLICATE_TRACKER = DuplicateTracker()