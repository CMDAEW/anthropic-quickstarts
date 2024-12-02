from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class TrendAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hashtag = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    views = db.Column(db.Integer, nullable=False)
    analysis_result = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_auto_discovered = db.Column(db.Boolean, default=False)
    engagement_rate = db.Column(db.Float)
    growth_rate = db.Column(db.Float)
    
    def __repr__(self):
        return f'<TrendAnalysis {self.hashtag}>'

class TrendMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hashtag = db.Column(db.String(100), nullable=False)
    total_views = db.Column(db.BigInteger, nullable=False)
    video_count = db.Column(db.Integer, nullable=False)
    avg_likes = db.Column(db.Integer)
    avg_comments = db.Column(db.Integer)
    avg_shares = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TrendMetrics {self.hashtag}>' 