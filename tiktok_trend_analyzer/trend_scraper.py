from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
import logging
from models.db import db, TrendAnalysis, TrendMetrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TikTokTrendScraper:
    def __init__(self):
        self.base_url = "https://www.tiktok.com/discover"
        self.trending_url = "https://www.tiktok.com/api/discover/trending"
        
    def get_trending_hashtags(self):
        """Hole die aktuell trendenden Hashtags von TikTok"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                
                # Lade die Discover-Seite
                page.goto(self.base_url)
                time.sleep(5)  # Warte auf dynamische Inhalte
                
                # Scrolle für mehr Inhalte
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, 1000)")
                    time.sleep(2)
                
                # Extrahiere Hashtag-Informationen
                trending_data = []
                hashtag_elements = page.query_selector_all(".tiktok-trending-card")
                
                for element in hashtag_elements:
                    try:
                        hashtag = element.query_selector(".hashtag-text").inner_text()
                        views = element.query_selector(".view-count").inner_text()
                        description = element.query_selector(".trend-description").inner_text()
                        
                        # Konvertiere Views-String in Zahl
                        views_num = self._parse_views(views)
                        
                        trending_data.append({
                            "hashtag": hashtag,
                            "views": views_num,
                            "description": description
                        })
                    except Exception as e:
                        logger.error(f"Fehler beim Extrahieren der Hashtag-Daten: {e}")
                
                browser.close()
                return trending_data
        except Exception as e:
            logger.error(f"Fehler beim Scraping: {e}")
            return []
    
    def analyze_trends(self):
        """Analysiere neue Trends und speichere sie in der Datenbank"""
        trends = self.get_trending_hashtags()
        
        for trend in trends:
            # Prüfe, ob der Trend bereits analysiert wurde
            existing = TrendAnalysis.query.filter_by(hashtag=trend['hashtag']).first()
            if existing:
                continue
            
            # Hole detaillierte Metriken
            metrics = self._get_trend_metrics(trend['hashtag'])
            
            # Speichere Metriken
            trend_metrics = TrendMetrics(
                hashtag=trend['hashtag'],
                total_views=trend['views'],
                video_count=metrics['video_count'],
                avg_likes=metrics['avg_likes'],
                avg_comments=metrics['avg_comments'],
                avg_shares=metrics['avg_shares']
            )
            db.session.add(trend_metrics)
            
            # Berechne Engagement und Wachstum
            engagement_rate = self._calculate_engagement_rate(metrics)
            growth_rate = self._calculate_growth_rate(trend['hashtag'])
            
            # Erstelle neue Trend-Analyse
            new_analysis = TrendAnalysis(
                hashtag=trend['hashtag'],
                description=trend['description'],
                views=trend['views'],
                is_auto_discovered=True,
                engagement_rate=engagement_rate,
                growth_rate=growth_rate,
                analysis_result=self._generate_analysis(trend, metrics)
            )
            db.session.add(new_analysis)
        
        db.session.commit()
    
    def _parse_views(self, views_str):
        """Konvertiere Views-String in Zahl"""
        try:
            views_str = views_str.lower().replace(',', '')
            if 'k' in views_str:
                return int(float(views_str.replace('k', '')) * 1000)
            elif 'm' in views_str:
                return int(float(views_str.replace('m', '')) * 1000000)
            elif 'b' in views_str:
                return int(float(views_str.replace('b', '')) * 1000000000)
            else:
                return int(views_str)
        except:
            return 0
    
    def _get_trend_metrics(self, hashtag):
        """Hole detaillierte Metriken für einen Hashtag"""
        # Beispielimplementierung - in der Realität würden hier
        # tatsächliche Metriken von TikTok geholt
        return {
            'video_count': 1000,
            'avg_likes': 5000,
            'avg_comments': 100,
            'avg_shares': 50
        }
    
    def _calculate_engagement_rate(self, metrics):
        """Berechne die Engagement-Rate"""
        if metrics['video_count'] == 0:
            return 0.0
        total_engagement = (metrics['avg_likes'] + metrics['avg_comments'] + metrics['avg_shares'])
        return (total_engagement / metrics['video_count']) * 100
    
    def _calculate_growth_rate(self, hashtag):
        """Berechne die Wachstumsrate des Hashtags"""
        # Hier würde normalerweise die Wachstumsrate über Zeit berechnet
        return 5.0  # Beispielwert
    
    def _generate_analysis(self, trend, metrics):
        """Generiere eine detaillierte Analyse des Trends"""
        return f"""Trend Analyse für #{trend['hashtag']}:

1. Aktuelle Performance:
   - Gesamt Views: {trend['views']:,}
   - Anzahl Videos: {metrics['video_count']:,}
   - Durchschnittliche Likes: {metrics['avg_likes']:,}
   - Durchschnittliche Kommentare: {metrics['avg_comments']:,}
   - Durchschnittliche Shares: {metrics['avg_shares']:,}

2. Engagement:
   - Engagement Rate: {self._calculate_engagement_rate(metrics):.2f}%
   - Wachstumsrate: {self._calculate_growth_rate(trend['hashtag']):.2f}%

3. Beschreibung:
   {trend['description']}

4. Empfehlung:
   Basierend auf den Metriken ist dieser Trend {
   'sehr vielversprechend' if self._calculate_engagement_rate(metrics) > 5
   else 'möglicherweise interessant' if self._calculate_engagement_rate(metrics) > 2
   else 'weniger relevant'
   } für Content Creator.""" 