import os
from pathlib import Path
# config.py - Configuration and constants

# API Keys
GROQ_API_KEY_P1 = os.getenv("GROQ_API_KEY_P1", "")
GROQ_API_KEY_P2 = os.getenv("GROQ_API_KEY_P2", "")
GROQ_API_KEY_P3 = os.getenv("GROQ_API_KEY_P3", "")
GROQ_API_KEY_E7 = os.getenv("GROQ_API_KEY_E7", "")

# Excel files
EXCEL_FILE_P1 = str(Path(__file__).resolve().parent / 'entities.xlsx')
EXCEL_FILE_P2 = str(Path(__file__).resolve().parent / 'entities (1).xlsx')

# Email configuration
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")
RECIPIENT_EMAIL = [x.strip() for x in os.getenv("RECIPIENT_EMAIL", "").split(",") if x.strip()]
OUTPUT_DIR = str(Path(__file__).resolve().parent / 'reports')

# News API Keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
NEWSDATA_KEY = os.getenv("NEWSDATA_KEY", "")
MEDIASTACK_KEY = os.getenv("MEDIASTACK_KEY", "")
CURRENTS_KEY = os.getenv("CURRENTS_KEY", "")

# Global settings
LOOKBACK_HOURS = 24
SUMMARY_LENGTH = 95
REL_THRESHOLD = 0.75
LOG_FILE = "uae_intel.log"
SEEN_OLD_FILE = "seen_old.json"

# TRUSTED HOSTS
TRUSTED_HOSTS_P1 = {
    "www.arabianbusiness.com", "gulfbusiness.com", "www.thenationalnews.com",
    "www.zawya.com", "www.khaleejtimes.com", "www.reuters.com", "www.reutersagency.com",
    "feeds.a.dj.com", "www.wealthbriefing.com", "www.privatebankerinternational.com",
    "international-adviser.com", "ifamagazine.com", "www.hubbis.com", "www.ft.com",
    "economictimes.indiatimes.com", "www.livemint.com", "www.business-standard.com",
    "www.moneycontrol.com", "www.regulationasia.com", "www.complianceweek.com",
    "www.step.org", "www.ifcreview.com", "familyofficehub.io", "www.campdenfb.com",
    "www.imf.org", "www.oecd.org", "linkedin.com", "news.google.com"
}

# RSS feeds for P1/P2
RSS_FEEDS_P1 = [
    "https://www.arabianbusiness.com/feed",
    "https://www.arabianbusiness.com/industries/banking-finance/feed",
    "https://gulfbusiness.com/feed/",
    "https://www.thenationalnews.com/business/rss",
    "https://www.zawya.com/en/rss",
    "https://www.zawya.com/en/rss/business",
    "https://www.khaleejtimes.com/rss/business",
    "https://www.reuters.com/rssFeed/businessNews",
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
    "https://www.wealthbriefing.com/rss/me/all.aspx",
    "https://www.wealthbriefing.com/rss/global/all.aspx",
    "https://www.privatebankerinternational.com/feed/",
    "https://international-adviser.com/feed/",
    "https://ifamagazine.com/feed/",
    "https://www.hubbis.com/articles/rss",
    "https://www.ft.com/companies/financial-services?format=rss",
    "https://www.ft.com/asset-management?format=rss",
    "https://www.ft.com/wealth?format=rss",
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://economictimes.indiatimes.com/wealth/rssfeeds/837555174.cms",
    "https://www.livemint.com/rss/money",
    "https://www.business-standard.com/rss/markets-106.rss",
    "https://www.moneycontrol.com/rss/latestnews.xml",
    "https://www.regulationasia.com/feed/",
    "https://www.complianceweek.com/rss",
    "https://www.step.org/rss.xml",
    "https://www.ifcreview.com/feed/",
    "https://familyofficehub.io/feed/",
    "https://www.campdenfb.com/rss.xml",
    "https://www.imf.org/external/np/exr/what/rss.aspx",
    "https://www.oecd.org/topics/finance/rss.xml",
]

# Use same RSS feeds for P2
RSS_FEEDS_P2 = RSS_FEEDS_P1.copy()

# RSS feeds for E7 (Real Estate)
# E7 - Real Estate Configuration (Updated with new constants)

# Expanded RSS feeds for E7 (from provided code)
RSS_FEEDS_E7 = [
    # Core Business/Real Estate
    "https://www.arabianbusiness.com/feed",
    "https://www.arabianbusiness.com/industries/banking-finance/feed",
    "https://gulfbusiness.com/feed/",
    "https://www.thenationalnews.com/business/rss",
    "https://www.zawya.com/en/rss",
    "https://www.zawya.com/en/rss/business",
    "https://www.zawya.com/en/rss/economy",
    "https://www.zawya.com/en/rss/real-estate",
    "https://www.khaleejtimes.com/rss/business",
    "https://www.khaleejtimes.com/rss/property",
    "https://www.emirates247.com/rss/real-estate",
    "https://www.emirates247.com/rss/business",
    "https://www.constructionweekonline.com/rss",
    "https://www.meconstructionnews.com/feed/",
    "https://www.propertyfinder.ae/blog/feed/",
    "https://www.bayut.com/blog/feed/",
    "https://www.dubizzle.com/blog/feed/",
    
    # Market News & Press Releases (NEW ADDITIONS)
    "https://www.openpr.com/rss/region_uae.xml",
    "https://www.prnewswire.com/rss/real-estate-news.rss",
    "https://www.globenewswire.com/RssFeed/industry/3003/Real%20Estate/feedTitle/GlobeNewswire%20-%20Real%20Estate",
    
    # International with UAE coverage
    "https://www.reuters.com/rssFeed/businessNews",
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
    "https://www.ft.com/companies/financial-services?format=rss",
    "https://www.ft.com/asset-management?format=rss",
    "https://www.ft.com/wealth?format=rss",
    "https://www.ft.com/real-estate?format=rss",
    "https://www.bloomberg.com/real-estate/rss.xml",
    "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "https://www.cnbc.com/id/10000115/device/rss/rss.html",
    
    # Wealth/Finance Focus
    "https://www.wealthbriefing.com/rss/me/all.aspx",
    "https://www.wealthbriefing.com/rss/global/all.aspx",
    "https://www.privatebankerinternational.com/feed/",
    "https://international-adviser.com/feed/",
    "https://ifamagazine.com/feed/",
    "https://www.hubbis.com/articles/rss",
    
    # Asian Markets
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://economictimes.indiatimes.com/wealth/rssfeeds/837555174.cms",
    "https://www.livemint.com/rss/money",
    "https://www.business-standard.com/rss/markets-106.rss",
    "https://www.moneycontrol.com/rss/latestnews.xml",
    "https://www.scmp.com/rss/91/feed",  # South China Morning Post
    
    # Regulation/Compliance
    "https://www.regulationasia.com/feed/",
    "https://www.complianceweek.com/rss",
    "https://www.step.org/rss.xml",
    "https://www.ifcreview.com/feed/",
    
    # Family Office/Investments
    "https://familyofficehub.io/feed/",
    "https://www.campdenfb.com/rss.xml",
    
    # Economic Institutions
    "https://www.imf.org/external/np/exr/what/rss.aspx",
    "https://www.oecd.org/topics/finance/rss.xml",
    "https://www.worldbank.org/en/news/all/rss.xml",
    
    # UAE Government/Specific
    "https://www.dubailand.gov.ae/en/news/rss/",
    "https://www.dm.gov.ae/en/rss/news/",
    "https://www.dewa.gov.ae/en/about-dewa/news-and-media/rss",
    "https://www.rta.ae/wps/portal/rta/ae/home/rss-feed",
    "https://www.adgm.com/media/rss",
    "https://www.difc.ae/news/rss/",
    
    # Real Estate Portals
    "https://blog.propertyfinder.ae/feed/",
    "https://www.zoomproperty.com/en/blog/feed",
    "https://www.housefinder.ae/blog/feed/",
    
    # Construction/Development
    "https://www.bigprojectme.com/feed/",
    "https://www.middleeastarchitect.com/feed",
    "https://www.cpimiddleeast.com/feed",
    
    # Luxury Real Estate
    "https://www.luxhabitat.ae/blog/feed/",
    "https://www.ellingtonproperties.com/feed/",
    "https://www.damacproperties.com/en/news/feed/",
    
    # Local News Portals
    "https://www.albawaba.com/business/rss.xml",
    "https://www.albawaba.com/real-estate/rss.xml",
    "https://www.amcnews.com/en/rss/news",
    "https://wam.ae/en/rss.xml",
    
    # Industry Associations
    "https://www.uae-reea.com/feed/",
    "https://www.dubaiassociationcentre.ae/news/rss/",
    
    # Additional Regional
    "https://www.arabnews.com/rss.xml",
    "https://www.middleeasteye.net/rss",
    "https://www.al-monitor.com/rss",
    
    # Property Tech
    "https://www.proptechmiddleeast.com/feed/",
    "https://www.menaherald.com/feed/",
    
    # Sustainability/Green Building
    "https://www.edgebuildings.com/feed/",
    "https://www.usgbc.org/rss/all/feed",
]


# Market queries
MARKET_QUERIES_P1 = [
    "UAE wealth OR Dubai family office",
    '"United Arab Emirates" investors OR finance',
    "Dubai billionaires OR UHNWI",
    "ADGM OR DIFC funds OR asset management",
    "UAE private banking OR regulation"
]

MARKET_QUERIES_P2 = MARKET_QUERIES_P1.copy()

GOOGLE_NEWS_SOURCES_P1 = [
    "Bloomberg UAE wealth", "Bloomberg Middle East finance", "Forbes Middle East wealth",
    "Forbes billionaires UAE", "FT Wealth UAE", "FT asset management UAE",
    "Reuters wealth management UAE", "Reuters Middle East finance", "Hubbis private banking",
    "family office UAE", "UHNW UAE", "DIFC regulation", "ADGM regulation", "QFC Qatar finance",
    "Dubai investor market", "Abu Dhabi investment"
]

GOOGLE_NEWS_SOURCES_P2 = GOOGLE_NEWS_SOURCES_P1.copy()

# Keywords
UAE_KEYWORDS_P1 = ['uae', 'qatar', 'qfc', 'dubai', 'rakicc', 'rak icc', 'dfsa', 'fsra', 'abu dhabi',
                   'adgm', 'difc', 'economy', 'emirates', 'sharjah', 'ras al khaimah', "Abu Dhabi's International Financial Centre", 'Abu Dhabi Global Market', ' Dubai International Financial Centre', 'Qatar Financial Centre']

UAE_KEYWORDS_P2 = UAE_KEYWORDS_P1.copy()

WEALTH_KEYWORDS_P1 = ['wealth', 'private banking', 'family office', 'fund', 'asset', 'investment', 'capital',
                      'ipo', 'm&a', 'acquisition', 'investor', 'golden visa', 'relocation', 'residency', 'fdi',
                      'real estate', 'property', 'finance', 'economic', 'market', 'billionaire', 'hnwi', 'uhnwi',
                      'portfolio', 'venture', 'private equity', 'tax', 'regulation']

WEALTH_KEYWORDS_P2 = WEALTH_KEYWORDS_P1.copy()

FINANCE_SIGNALS_P1 = ['difc', 'adgm', 'fsra', 'dfsa', 'regulation', 'regulatory', 'license', 'licence',
                      'authorised firm', 'authorised', 'regulated activity', 'financial licence', 'registration',
                      'approval', 'supervision', 'regulatory framework', 'spv', 'special purpose vehicle',
                      'holding company', 'foundation', 'private foundation', 'trust', 'fiduciary', 'trustee',
                      'company formation', 'entity setup', 'corporate services', 'fund', 'fund manager',
                      'fund management', 'asset manager', 'asset management', 'portfolio management',
                      'capital market', 'investment firm', 'broker dealer', 'custody', 'custodian', 'clearing',
                      'securities', 'capital raising', 'listing', 'family office', 'wealth management',
                      'private banking', 'financial advisor', 'investment advisor', 'private equity',
                      'venture capital', 'vc', 'pe', 'angel investor', 'fintech', 'regtech', 'paytech', 'insurtech',
                      'financial centre', 'financial services', 'financial institution', 'credit provider',
                      'lending', 'loan', 'payments', 'psp', 'msb', 'remittance', 'money service', 'islamic finance',
                      'shariah', 'sukuk', 'aml', 'kyc', 'compliance', 'governance', 'risk management', 'tax', 'policy',
                      'economic', 'fdi', 'foreign investment', 'economic substance', 'transfer pricing',
                      'real estate investment', 'property investment']

FINANCE_SIGNALS_P2 = FINANCE_SIGNALS_P1.copy()

ALL_EXCLUSIONS_P1 = set(['football','hiring', 'cricket', 'real estate','sports', 'movie', 'film', 'entertainment', 'bollywood', 'hollywood',
                         'airbus', 'boeing', 'popcorn', 'a320', 'a380', 'helicopter', 'evtol', 'evtols', 'rolls-royce',
                         'mro', 'manufacturing', 'factory', 'production line', 'air mobility', 'aircraft', 'truck', 'trucks',
                         'rta', 'traffic', 'accident', 'road', 'journey time', 'speed', 'vehicle', 'highway', 'parking', 'toll',
                         'logistics', 'hiring', 'party', 'dance', 'layoff', 'layoffs', 'redundancy', 'end-of-service',
                         'severance', 'sacked', 'fired', 'prank', 'job cuts', 'retrenchment', 'job losses', 'laid off',
                         'termination', 'payout', 'sailgp', 'sail gp', 'regatta', 'yacht', 'boat race', 'marina', 'lifestyle',
                         'season finale', 'fan zone', 'sports event', 'festival', 'concert','Croissants','traffic', 'hiring'])

ALL_EXCLUSIONS_P2 = ALL_EXCLUSIONS_P1.copy()

# P3 - Tech Hiring Configuration
TECH_FIELDS_P3 = {
    "AI/Data": [
        'AI engineer', 'machine learning engineer', 'ML engineer', 'data scientist',
        'data analyst', 'data engineer', 'computer vision engineer', 'CV engineer',
        'NLP engineer', 'natural language processing', 'deep learning engineer',
        'MLOps engineer', 'AI researcher', 'data architect', 'BI developer',
        'hiring AI', 'hiring data scientist', 'AI job UAE', 'data science job Dubai',
    ],
    
    "Cybersecurity": [
        'SOC analyst', 'security analyst', 'cybersecurity engineer', 'security engineer',
        'cloud security engineer', 'security architect', 'penetration tester',
        'ethical hacker', 'security consultant', 'compliance analyst', 'GRC analyst',
        'CISO', 'hiring cybersecurity UAE', 'security job Dubai', 'SOC job Abu Dhabi',
    ],
    
    "Cloud & DevOps": [
        'DevOps engineer', 'cloud engineer', 'site reliability engineer', 'SRE',
        'platform engineer', 'cloud architect', 'AWS engineer', 'Azure engineer',
        'GCP engineer', 'Kubernetes engineer', 'Docker engineer', 'CI/CD engineer',
        'hiring DevOps UAE', 'DevOps job Dubai', 'cloud job Abu Dhabi', 'AWS job UAE',
    ],
    
    "Fintech": [
        'fintech developer', 'blockchain developer', 'solidity developer',
        'smart contract developer', 'crypto developer', 'payments engineer',
        'full-stack developer', 'quantitative developer', 'trading systems developer',
        'hiring fintech UAE', 'fintech job Dubai', 'blockchain job Abu Dhabi',
        'payments job UAE', 'crypto job Dubai',
    ]
}

MARKET_KEYWORDS_P3 = [
    'employment policy', 'labor policy', 'work policy', 'employee rights',
    'employer obligations', 'working conditions', 'workplace regulations',
    'hiring policy', 'recruitment policy', 'staffing policy', 'talent acquisition policy',
    'executive search firm', 'headhunting firm', 'recruitment agency',
    'talent consultancy', 'search firm', 'executive recruiter',
    'opening office UAE', 'new office Dubai', 'expansion Abu Dhabi',
    'MoHRE', 'Ministry of Human Resources', 'UAE cabinet', 'government announcement',
    'labor law', 'employment law', 'visa policy', 'work permit',
]

UAE_KEYWORDS_P3 = ['uae', 'united arab emirates', 'dubai', 'abu dhabi', 'emirates', 'middle east', 'gcc']
EXCLUSIONS_P3 = ['sports', 'entertainment', 'movie', 'music', 'celebrity', 'weather', 'crime']

TRUSTED_HOSTS_P3 = {
    "gulfnews.com", "www.thenationalnews.com", "www.khaleejtimes.com",
    "www.zawya.com", "www.wam.ae", "www.mohre.gov.ae", "u.ae",
    "www.arabianbusiness.com", "gulfbusiness.com", "www.reuters.com",
    "www.ft.com", "www.cnbc.com", "www.bloomberg.com",
    "hrme.economictimes.indiatimes.com", "www.humanresourcesonline.net",
    "www.hcamag.com", "www.recruitment-international.com",
    "linkedin.com", "www.linkedin.com", "news.google.com",
}

# E7 - Real Estate Configuration
UNWANTED_KEYWORDS_E7 = [
    'hiring', 'career', 'job', 'vacancy', 'recruitment', 'recruit', 
    'apply now', 'apply online', 'work with us', 'join our team'
]

MARKET_KEYWORDS_E7 = [
    'rent','real estate','property', 'rental', 'lease', 'yield', 'price', 'pricing', 'valuation',
    'market value', 'capital appreciation', 'bubble', 'correction',
    'index', 'reidin', 'mortgage', 'loan', 'finance', 'interest rate',
    'affordable housing', 'luxury segment', 'super-prime', 'prime areas',
    'supply', 'demand', 'inventory', 'vacancy rate', 'occupancy',
    'regulation', 'rera', 'dld', 'rent cap', 'rental index',
    'service charge', 'maintenance fee', 'housing supply', 'housing demand',
    'property tax', 'transaction', 'deal', 'sales volume', 'market report',
    'trend', 'forecast', 'outlook', 'analysis', 'research', 'survey',
    'investor sentiment', 'buyer', 'seller', 'landlord', 'tenant',
    'short-term rental', 'long-term rental', 'commercial rent',
    'residential rent', 'office space', 'retail space', 'warehouse',
    'industrial', 'logistics', 'hospitality', 'hotel', 'tourism',
    'economic growth', 'gdp', 'population growth', 'inflation',
    'infrastructure', 'transport', 'metro', 'road', 'airport', 'port',
    'facilitating', 'transactions', 'deals', 'cross-border', 'advisory',
    'market size', 'valued at', 'valuation', 'forecast', 'projected',
    'growth trajectory', 'cagr', 'report', 'analysis', 'mordor',
    'outbound', 'investment', 'facilitated', 'crore', 'billion',
    'market overview', 'key players', 'segmentation', 'million',
    'size', 'worth', 'valued', 'expands', 'desk', 'facilitate',
    'press release', 'prnewswire', 'openpr', 'globenewswire',
    'propertypistol', 'mordor intelligence', 'market intelligence',
    'reaches', 'reach', 'to reach', 'expected to', 'projection',
    'study', 'findings', 'according to', 'research firm'
]

DEVELOPER_KEYWORDS_E7 = [
    'emaar', 'nakheel', 'aldar', 'sobha', 'damac', 'meydan', 'nshama',
    'dubai properties', 'wasl', 'mashreq', 'adcb', 'fab', 'emirates nbd',
    'dubai holding', 'mubadala', 'investment corporation of dubai',
    'abudhabi investment authority', 'al futtaim', 'al ghurair',
    'al tayer', 'majid al futtaim', 'lulu group', 'al habtoor',
    'developer', 'development', 'project', 'launch', 'announce',
    'new project', 'masterplan', 'phase', 'completion', 'handover',
    'groundbreaking', 'construction', 'contract', 'tender', 'bid',
    'award', 'joint venture', 'jv', 'partnership', 'collaboration',
    'memorandum of understanding', 'mou', 'agreement', 'deal',
    'acquisition', 'merger', 'takeover', 'stake', 'investment',
    'funding', 'finance', 'loan', 'syndication', 'bond', 'sukuk',
    'ipo', 'listing', 'dividend', 'profit', 'revenue', 'earnings',
    'results', 'financials', 'ceo', 'md', 'director', 'appointment',
    'resignation', 'management', 'board', 'shareholder', 'dividend',
    'vision', 'strategy', 'expansion', 'growth', 'international',
    'global', 'regional', 'middle east', 'gcc', 'saudi', 'qatar',
    'oman', 'bahrain', 'kuwait', 'egypt', 'morocco', 'turkey',
    'india', 'china', 'uk', 'usa', 'europe', 'asia', 'africa'
]

GEO_KEYWORDS_E7 = [
    'uae', 'dubai', 'abu dhabi', 'sharjah', 'ajman', 'umm al quwain',
    'ras al khaimah', 'fujairah', 'emirates', 'adgm', 'difc',
    'dubai international financial centre', 'abudhabi global market',
    'dubai marina', 'palm jumeirah', 'downtown dubai', 'business bay',
    'jumeirah village circle', 'jvc', 'jumeirah', 'al reem island',
    'saadiyat island', 'yas island', 'dubai hills', 'arabian ranches',
    'damac hills', 'akoya', 'meydan', 'city walk', 'bluewaters',
    'port de la mer', 'emaar beachfront', 'jebel ali', 'dubai south',
    'dubai land', 'dubai silicon oasis', 'international city',
    'dubai sports city', 'motor city', 'production city',
    'academic city', 'dubai healthcare city', 'dubai media city',
    'dubai internet city', 'dubai knowledge park', 'dubai design district',
    'd3', 'dubai creek harbour', 'al seef', 'al quoz', 'al barsha',
    'al satwa', 'deira', 'bur dubai', 'karama', 'mirdif'
]

UAE_REAL_PLAYERS_E7 = [
    "emaar", "nakheel", "aldar", "sobha", "damac", "meydan", "nshama",
    "dubai-properties", "emaar-developments", "aldar-properties",
    "nakheel-official", "damac-properties", "sobha-realty", "meydan-group",
    "jumeirah-group", "emaar-hospitality", "emaar-malls", "nakheel-retail",
    "aldar-investment", "dubai-holding", "wasl-properties", "mashreq-bank",
    "adcb", "fabuae", "emirates-nbd", "rakbank", "dubailand",
    "dubai-south", "dewa", "rta-dubai", "adgm", "difc",
    "elliotti-properties", "betterhomes", "luxhabitat", "allsopp-allsopp",
    "properties-in-the-city", "provident-estate", "haus-and-haus",
    "fäm-properties", "ax-capital", "aqua-properties"
]
