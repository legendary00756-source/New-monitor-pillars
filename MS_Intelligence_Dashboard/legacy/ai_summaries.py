# ai_summaries.py - AI summary generation functions
import time
import logging
from groq import Groq

logger = logging.getLogger(__name__)

def generate_article_summary(headline, original_summary, client, target_words=95, pillar="General"):
    """AI summary for general articles"""
    try:
        prompt = f"""You are a senior financial analyst for a premier intelligence firm. Create a {target_words}-word executive summary (85-105 words) of this news article.

Headline: {headline}
Original Summary: {original_summary}

Focus on:
1. Key business/financial implications
2. Market impact and trends
3. Regulatory/jurisdictional relevance
4. Actionable insights for decision-makers

Output only the summary text, no formatting."""
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.4
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI summary error: {e}")
        return original_summary[:target_words*2]

def generate_tech_summary(headline, original_summary, field, client, target_words=95):
    """AI summary for tech hiring articles"""
    try:
        prompt = f"""You are a senior tech recruiter in UAE. Create a {target_words}-word executive summary of this tech hiring news.

FIELD: {field}
HEADLINE: {headline}
CONTENT: {original_summary[:500]}

Focus on:
1. Specific roles/technologies mentioned
2. Hiring demand level in UAE market
3. Key companies/industries involved
4. Salary/compensation trends if mentioned
5. Market implications for tech recruitment

Output only the summary text."""
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.4
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI tech summary error: {e}")
        return f"UAE {field} hiring update: {original_summary[:300]}..."

def generate_market_summary(headline, original_summary, category, client, target_words=95):
    """AI summary for market news articles"""
    try:
        prompt = f"""You are a UAE market analyst. Create a {target_words}-word executive summary of this market news.

CATEGORY: {category}
HEADLINE: {headline}
CONTENT: {original_summary[:500]}

Focus on:
1. Key policy/business changes announced
2. Effective dates and implementation timeline
3. Impact on employers/employees in UAE
4. Compliance requirements if any
5. Market implications

Output only the summary text."""
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.4
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI market summary error: {e}")
        return f"{category} update in UAE: {original_summary[:300]}..."

def generate_real_estate_summary(headline, original_summary, category, client, target_words=95):
    """AI summary for real estate articles"""
    try:
        if category == "market":
            focus = "market trends, pricing, regulations, supply-demand dynamics"
        else:
            focus = "project details, developer strategy, investment opportunities, timelines"
        
        prompt = f"""You are a senior real estate analyst in UAE. Create a {target_words}-word executive summary.

CATEGORY: {category.upper()}
HEADLINE: {headline}
CONTENT: {original_summary[:500]}

Focus on:
1. {focus}
2. Price/rent impact analysis
3. Investment implications
4. Short-term vs long-term outlook
5. Key players involved

Output only the summary text."""
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI real estate summary error: {e}")
        return f"UAE real estate {category} update: {original_summary[:300]}..."

def add_ai_summaries_p1(articles, api_key):
    """Add AI summaries to P1 articles"""
    if not api_key:
        logger.warning("No Groq API key for P1, skipping AI summaries")
        return articles
    
    try:
        client = Groq(api_key=api_key)
        
        for article in articles:
            try:
                ai_summary = generate_article_summary(
                    article["headline"],
                    article.get("summary", ""),
                    client,
                    95,
                    "P1_Wealth"
                )
                article["ai_summary"] = ai_summary
                time.sleep(0.3)
            except Exception as e:
                logger.warning(f"AI summary error for P1 article: {e}")
                article["ai_summary"] = article.get("summary", "")
    except Exception as e:
        logger.error(f"AI summary generation failed for P1: {e}")
    
    return articles

def add_ai_summaries_p2(articles, api_key):
    """Add AI summaries to P2 articles"""
    if not api_key:
        logger.warning("No Groq API key for P2, skipping AI summaries")
        return articles
    
    try:
        client = Groq(api_key=api_key)
        
        for article in articles:
            try:
                ai_summary = generate_article_summary(
                    article["headline"],
                    article.get("summary", ""),
                    client,
                    95,
                    "P2_Wealth"
                )
                article["ai_summary"] = ai_summary
                time.sleep(0.3)
            except Exception as e:
                logger.warning(f"AI summary error for P2 article: {e}")
                article["ai_summary"] = article.get("summary", "")
    except Exception as e:
        logger.error(f"AI summary generation failed for P2: {e}")
    
    return articles

def add_ai_summaries_p3(articles, api_key):
    """Add AI summaries to P3 articles"""
    if not api_key:
        logger.warning("No Groq API key for P3, skipping AI summaries")
        return articles
    
    try:
        client = Groq(api_key=api_key)
        
        for article in articles:
            try:
                if article.get("type") == "Tech Hiring":
                    ai_summary = generate_tech_summary(
                        article["headline"],
                        article.get("summary", ""),
                        article.get("field", "General Tech"),
                        client,
                        95
                    )
                else:  # Market News
                    ai_summary = generate_market_summary(
                        article["headline"],
                        article.get("summary", ""),
                        article.get("category", "Market Update"),
                        client,
                        95
                    )
                article["ai_summary"] = ai_summary
                time.sleep(0.3)
            except Exception as e:
                logger.warning(f"AI summary error for P3 article: {e}")
                article["ai_summary"] = article.get("summary", "")
    except Exception as e:
        logger.error(f"AI summary generation failed for P3: {e}")
    
    return articles

def add_ai_summaries_e7(articles, category, api_key):
    """Add AI summaries to E7 articles"""
    if not api_key:
        logger.warning("No Groq API key for E7, skipping AI summaries")
        return articles
    
    try:
        client = Groq(api_key=api_key)
        
        for article in articles:
            try:
                ai_summary = generate_real_estate_summary(
                    article["headline"],
                    article.get("summary", ""),
                    category,
                    client,
                    95
                )
                article["ai_summary"] = ai_summary
                time.sleep(0.3)
            except Exception as e:
                logger.warning(f"AI summary error for E7 article: {e}")
                article["ai_summary"] = article.get("summary", "")
    except Exception as e:
        logger.error(f"AI summary generation failed for E7: {e}")
    
    return articles