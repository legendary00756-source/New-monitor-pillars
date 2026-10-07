# main.py - Fix logging encoding
#!/usr/bin/env python3
# UAE UNIFIED INTELLIGENCE SYSTEM - Single PDF Output

import time
import logging
import sys
from datetime import datetime

# Import modules
from config import *
from utils import *
from duplicate_tracker import GLOBAL_DUPLICATE_TRACKER
from pillar1 import fetch_all_entity_news_p1, fetch_market_news_p1
from pillar2 import fetch_all_entity_news_p2, fetch_market_news_p2
from pillar3 import fetch_tech_hiring_news_p3, fetch_market_news_p3
from e7_real_estate import fetch_all_real_estate_news_e7
from pdf_generator import create_unified_pdf_with_e7
from email_sender import send_unified_email_with_e7

# =============================================================================
# LOGGING SETUP - FIXED ENCODING
# =============================================================================

# Remove emoji from log messages or use proper encoding
class SafeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            # Remove or replace emojis for Windows compatibility
            msg = msg.replace('✅', '[OK]').replace('❌', '[ERROR]').replace('⚠️', '[WARN]')
            msg = msg.replace('⏳', '[WAIT]').replace('🔍', '[SEARCH]').replace('🏢', '[RE]')
            msg = msg.replace('📰', '[RSS]').replace('👔', '[LINKEDIN]').replace('🏷️', '[CATEGORY]')
            msg = msg.replace('🤖', '[AI]').replace('💻', '[TECH]').replace('📊', '[STATS]')
            msg = msg.replace('📈', '[MARKET]').replace('📋', '[POLICY]').replace('🏠', '[PROPERTY]')
            msg = msg.replace('🚀', '[START]').replace('📁', '[FILE]')
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        SafeStreamHandler()
    ]
)
logger = logging.getLogger("unified_intel")

def prog(msg):
    """Print progress messages with timestamp"""
    # Clean emojis for Windows console
    clean_msg = msg
    emoji_map = {
        '✅': '[OK]', '❌': '[ERROR]', '⚠️': '[WARN]', '⏳': '[WAIT]',
        '🔍': '[SEARCH]', '🏢': '[RE]', '📰': '[RSS]', '👔': '[LINKEDIN]',
        '🏷️': '[CATEGORY]', '🤖': '[AI]', '💻': '[TECH]', '📊': '[STATS]',
        '📈': '[MARKET]', '📋': '[POLICY]', '🏠': '[PROPERTY]', '🏢': '[DEV]',
        '🚀': '[START]', '📁': '[FILE]'
    }
    for emoji, text in emoji_map.items():
        clean_msg = clean_msg.replace(emoji, text)
    
    print(f"\033[96m[{datetime.now().strftime('%H:%M:%S')}]\033[0m {clean_msg}")

# =============================================================================
# MAIN FUNCTION - INCLUDING E7
# =============================================================================

def main_with_e7():
    print("\n" + "="*70)
    print("[START] UNIFIED INTELLIGENCE SYSTEM")
    print("Including P1, P2, P3, and E7 (Real Estate)")
    print("Single PDF Output - No Duplicates")
    print("="*70 + "\n")
    
    total_start = time.time()
    
    # Reset global duplicate tracker
    GLOBAL_DUPLICATE_TRACKER.reset()
    
    all_data = {}
    stats = {}
    
    # ===== PILLAR 1 EXECUTION =====
    prog("[WAIT] Executing Pillar 1 (Wealth Intelligence)...")
    try:
        p1_entity = fetch_all_entity_news_p1()
        p1_market = fetch_market_news_p1()
        
        p1_entity_count = sum(len(articles) for articles in p1_entity.values())
        p1_market_count = len(p1_market)
        
        all_data['p1_entity'] = p1_entity
        all_data['p1_market'] = p1_market
        stats['p1_entity'] = p1_entity_count
        stats['p1_market'] = p1_market_count
        
        prog(f"[OK] Pillar 1: {p1_entity_count} entity articles, {p1_market_count} market articles")
    except Exception as e:
        logger.error(f"Pillar 1 failed: {e}")
        all_data['p1_entity'] = {}
        all_data['p1_market'] = []
    
    # ===== PILLAR 2 EXECUTION =====
    prog("[WAIT] Executing Pillar 2 (Wealth Intelligence - Different Excel)...")
    try:
        p2_entity = fetch_all_entity_news_p2()
        p2_market = fetch_market_news_p2()
        
        p2_entity_count = sum(len(articles) for articles in p2_entity.values())
        p2_market_count = len(p2_market)
        
        all_data['p2_entity'] = p2_entity
        all_data['p2_market'] = p2_market
        stats['p2_entity'] = p2_entity_count
        stats['p2_market'] = p2_market_count
        
        prog(f"[OK] Pillar 2: {p2_entity_count} entity articles, {p2_market_count} market articles")
    except Exception as e:
        logger.error(f"Pillar 2 failed: {e}")
        all_data['p2_entity'] = {}
        all_data['p2_market'] = []
    
    # ===== PILLAR 3 EXECUTION =====
    prog("[WAIT] Executing Pillar 3 (Tech Hiring Intelligence)...")
    try:
        p3_tech = fetch_tech_hiring_news_p3()
        p3_market = fetch_market_news_p3()
        
        all_data['p3_tech'] = p3_tech
        all_data['p3_market'] = p3_market
        stats['p3_tech'] = len(p3_tech)
        stats['p3_market'] = len(p3_market)
        
        prog(f"[OK] Pillar 3: {len(p3_tech)} tech articles, {len(p3_market)} market articles")
    except Exception as e:
        logger.error(f"Pillar 3 failed: {e}")
        all_data['p3_tech'] = []
        all_data['p3_market'] = []
    
    # ===== E7 EXECUTION =====
    prog("[WAIT] Executing E7 (Real Estate Intelligence)...")
    try:
        e7_data = fetch_all_real_estate_news_e7()
        
        all_data['e7_market'] = e7_data.get("market", [])
        all_data['e7_developer'] = e7_data.get("developer", [])
        stats['e7_market'] = len(all_data['e7_market'])
        stats['e7_developer'] = len(all_data['e7_developer'])
        
        prog(f"[OK] E7 Real Estate: {stats['e7_market']} market, {stats['e7_developer']} developer articles")
    except Exception as e:
        logger.error(f"E7 failed: {e}")
        all_data['e7_market'] = []
        all_data['e7_developer'] = []
    
    # Calculate total stats
    stats['total'] = sum(stats.values())
    
    # ===== CREATE UNIFIED PDF =====
    prog("[WAIT] Creating unified PDF (with E7)...")
    pdf_path = create_unified_pdf_with_e7(all_data)
    
    if pdf_path:
        prog(f"[OK] PDF created: {pdf_path}")
        
        # Debug: Check if file exists
        import os
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            prog(f"[FILE] PDF file size: {file_size:,} bytes")
            
            # ===== SEND EMAIL =====
            prog("[WAIT] Sending email...")
            email_sent = send_unified_email_with_e7(pdf_path, stats)
            
            if email_sent:
                prog("[OK] Email sent successfully")
            else:
                prog("[WARN] Email sending failed")
        else:
            prog("[ERROR] PDF file does not exist at path")
    else:
        prog("[ERROR] PDF creation failed")
    
    # Final summary
    total_time = time.time() - total_start
    
    print("\n" + "="*70)
    print("[STATS] EXECUTION SUMMARY")
    print("="*70)
    print(f"Total Articles: {stats['total']}")
    print(f"Pillar 1 Entities: {stats.get('p1_entity', 0)}")
    print(f"Pillar 1 Market: {stats.get('p1_market', 0)}")
    print(f"Pillar 2 Entities: {stats.get('p2_entity', 0)}")
    print(f"Pillar 2 Market: {stats.get('p2_market', 0)}")
    print(f"Tech Hiring: {stats.get('p3_tech', 0)}")
    print(f"Tech Market: {stats.get('p3_market', 0)}")
    print(f"Real Estate Market: {stats.get('e7_market', 0)}")
    print(f"Real Estate Developer: {stats.get('e7_developer', 0)}")
    print(f"Total Time: {total_time:.1f} seconds")
    print(f"PDF Location: {pdf_path if pdf_path else 'Not created'}")
    print("="*70)
    
    return pdf_path, stats

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    try:
        pdf_path, stats = main_with_e7()
        
        # Wait a moment before exiting
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("\n\n[WARN] Process interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {e}")
        logger.exception("Main execution failed")