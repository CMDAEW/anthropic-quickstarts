from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
from anthropic import Anthropic
from datetime import datetime
from models.db import db, TrendAnalysis, TrendMetrics
from trend_scraper import TikTokTrendScraper
from apscheduler.schedulers.background import BackgroundScheduler
import json

# Lade Umgebungsvariablen
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trends.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisiere Datenbank
db.init_app(app)

# Initialisiere Anthropic Client
anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Initialisiere TikTok Scraper
trend_scraper = TikTokTrendScraper()

def analyze_trend(trend_data):
    """Analysiere einen TikTok-Trend mit Claude"""
    prompt = f"""Analysiere diesen TikTok-Trend:
    Hashtag: {trend_data['hashtag']}
    Beschreibung: {trend_data['description']}
    Aktuelle Views: {trend_data['views']}
    
    Bitte bewerte:
    1. Virales Potenzial (1-10)
    2. Zielgruppe
    3. Beste Tageszeit für Posts
    4. Empfohlene Hashtags
    5. Wachstumsprognose
    """
    
    response = anthropic.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content

def scheduled_trend_analysis():
    """Führe regelmäßige Trend-Analyse durch"""
    with app.app_context():
        trend_scraper.analyze_trends()

# Initialisiere Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_trend_analysis, trigger="interval", hours=1)
scheduler.start()

@app.route('/')
def index():
    # Hole die neuesten automatisch entdeckten Trends
    latest_trends = TrendAnalysis.query.filter_by(is_auto_discovered=True)\
        .order_by(TrendAnalysis.timestamp.desc())\
        .limit(5)\
        .all()
    return render_template('index.html', latest_trends=latest_trends)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    
    # Führe Analyse durch
    analysis = analyze_trend(data)
    
    # Speichere in Datenbank
    new_analysis = TrendAnalysis(
        hashtag=data['hashtag'],
        description=data['description'],
        views=data['views'],
        analysis_result=analysis,
        timestamp=datetime.now(),
        is_auto_discovered=False
    )
    db.session.add(new_analysis)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'analysis': analysis
    })

@app.route('/history')
def history():
    analyses = TrendAnalysis.query.order_by(TrendAnalysis.timestamp.desc()).all()
    return render_template('history.html', analyses=analyses)

@app.route('/metrics/<hashtag>')
def get_metrics(hashtag):
    metrics = TrendMetrics.query.filter_by(hashtag=hashtag)\
        .order_by(TrendMetrics.timestamp.desc())\
        .first()
    
    if metrics:
        return jsonify({
            'total_views': metrics.total_views,
            'video_count': metrics.video_count,
            'avg_likes': metrics.avg_likes,
            'avg_comments': metrics.avg_comments,
            'avg_shares': metrics.avg_shares
        })
    else:
        return jsonify({'error': 'Keine Metriken gefunden'}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 