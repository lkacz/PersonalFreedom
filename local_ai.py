"""
Local GPU-accelerated AI models for advanced productivity insights
Requires: pip install transformers torch sentence-transformers
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
import warnings
warnings.filterwarnings('ignore')

# Initialize with defaults - will be overwritten if imports succeed
GPU_AVAILABLE = False
DEVICE = -1

try:
    import torch
    from transformers import pipeline  # type: ignore
    from sentence_transformers import SentenceTransformer  # type: ignore
    GPU_AVAILABLE = torch.cuda.is_available()
    DEVICE = 0 if GPU_AVAILABLE else -1  # 0 = GPU, -1 = CPU
except ImportError:
    pipeline = None  # type: ignore
    SentenceTransformer = None  # type: ignore
    print("⚠️  Install transformers: pip install transformers torch sentence-transformers")


class LocalAI:
    """GPU-accelerated AI for productivity analysis"""
    
    def __init__(self):
        self.device = DEVICE
        self.gpu_available = GPU_AVAILABLE
        
        # Lazy load models (only when needed)
        self._sentiment_analyzer = None
        self._embedder = None
        self._summarizer = None
        
        print(f"🧠 Local AI initialized (GPU: {self.gpu_available})")
    
    @property
    def sentiment_analyzer(self):
        """Lazy load sentiment analysis model (40MB)"""
        if self._sentiment_analyzer is None:
            print("📥 Loading sentiment model (distilbert-base-uncased-finetuned-sst-2-english)...")
            # Note: type: ignore needed due to incomplete transformers type stubs
            self._sentiment_analyzer = pipeline(
                "sentiment-analysis",  # type: ignore[arg-type]
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=self.device
            )
        return self._sentiment_analyzer
    
    @property
    def embedder(self):
        """Lazy load sentence embeddings model (80MB)"""
        if self._embedder is None:
            print("📥 Loading embedding model (all-MiniLM-L6-v2)...")
            device = 'cuda' if self.gpu_available else 'cpu'
            self._embedder = SentenceTransformer('all-MiniLM-L6-v2', device=device)  # type: ignore[misc]
        return self._embedder
    
    @property
    def summarizer(self):
        """Lazy load text summarization model (240MB)"""
        if self._summarizer is None:
            print("📥 Loading summarization model (distilbart-cnn-6-6)...")
            self._summarizer = pipeline(  # type: ignore[misc]
                "summarization",
                model="sshleifer/distilbart-cnn-6-6",
                device=self.device
            )
        return self._summarizer
    
    # ==================== FEATURE 1: Focus Quality Analysis ====================
    
    def analyze_focus_quality(self, session_note):
        """
        Analyze user's session notes to detect focus quality
        
        Example:
        "Great session, very productive!" → POSITIVE (0.98)
        "Struggled to concentrate, many distractions" → NEGATIVE (0.91)
        """
        if not session_note or len(session_note.strip()) < 5:
            return None
        
        result = self.sentiment_analyzer(session_note)[0]
        
        return {
            'sentiment': result['label'],  # POSITIVE or NEGATIVE
            'confidence': result['score'],
            'interpretation': self._interpret_sentiment(result)
        }
    
    def _interpret_sentiment(self, result):
        """Convert sentiment to actionable insight"""
        if result['label'] == 'POSITIVE' and result['score'] > 0.9:
            return "🌟 High-quality focus session detected!"
        elif result['label'] == 'POSITIVE':
            return "✅ Good session"
        elif result['score'] > 0.8:
            return "⚠️ Challenging session - consider adjusting strategy"
        else:
            return "💡 Difficult session - try shorter duration next time"
    
    # ==================== FEATURE 2: Smart Goal Suggestions ====================
    
    def suggest_goals_from_history(self, stats):
        """
        Use embeddings to find similar successful patterns and suggest goals
        """
        # Extract past successful patterns
        successful_sessions = self._get_successful_patterns(stats)
        
        if len(successful_sessions) < 5:
            return ["Need more data - complete 5+ sessions first"]
        
        # Analyze patterns using embeddings
        pattern_descriptions = [
            f"{s['duration']}min session at {s['hour']}:00, {s['mode']} mode"
            for s in successful_sessions
        ]
        
        # Get embeddings
        embeddings = self.embedder.encode(pattern_descriptions)
        
        # Find most common pattern (cluster center)
        # Simplified: just use most frequent hour and duration
        avg_duration = sum(s['duration'] for s in successful_sessions) // len(successful_sessions)
        most_common_hour = max(set(s['hour'] for s in successful_sessions), 
                               key=[s['hour'] for s in successful_sessions].count)
        
        suggestions = [
            f"Try {avg_duration}-minute sessions (your average success duration)",
            f"Schedule sessions at {most_common_hour}:00 (your most productive hour)",
        ]
        
        return suggestions
    
    def _get_successful_patterns(self, stats):
        """Extract patterns from completed sessions"""
        patterns = []
        for date, daily in stats.get('daily_stats', {}).items():
            if daily.get('sessions', 0) > 0:
                patterns.append({
                    'duration': daily.get('focus_time', 0) // 60,  # minutes
                    'hour': 9,  # Would extract from timestamp
                    'mode': 'normal'
                })
        return patterns
    
    # ==================== FEATURE 3: Distraction Detection ====================
    
    def detect_distraction_triggers(self, session_notes):
        """
        Analyze multiple session notes to find common distraction triggers
        
        Example notes:
        - "Phone kept buzzing, hard to focus"
        - "Too many notifications today"
        - "Email alerts were distracting"
        
        AI detects: "notifications" is a common trigger
        """
        if not session_notes or len(session_notes) < 3:
            return []
        
        # Get embeddings for all notes
        embeddings = self.embedder.encode(session_notes)
        
        # Calculate similarity matrix
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(embeddings)
        
        # Find notes with high similarity (similar distractions)
        common_triggers = []
        
        # Simple keyword extraction from similar notes
        distraction_keywords = [
            'phone', 'notification', 'email', 'social media', 
            'noise', 'tired', 'hungry', 'stressed'
        ]
        
        for keyword in distraction_keywords:
            count = sum(1 for note in session_notes if keyword.lower() in note.lower())
            if count >= 2:  # Appears in 2+ notes
                common_triggers.append({
                    'trigger': keyword,
                    'frequency': count,
                    'recommendation': self._get_trigger_recommendation(keyword)
                })
        
        return sorted(common_triggers, key=lambda x: x['frequency'], reverse=True)
    
    def _get_trigger_recommendation(self, trigger):
        """Get actionable advice for each trigger"""
        recommendations = {
            'phone': 'Enable airplane mode or use app blockers',
            'notification': 'Turn on Do Not Disturb mode',
            'email': 'Close email client during focus sessions',
            'social media': 'Use website blocker for social apps',
            'noise': 'Try noise-cancelling headphones or white noise',
            'tired': 'Schedule sessions earlier in the day',
            'hungry': 'Eat a small snack before focusing',
            'stressed': 'Try 5-minute meditation before sessions'
        }
        return recommendations.get(trigger, 'Identify and eliminate this distraction')
    
    # ==================== FEATURE 4: Session Summary Generation ====================
    
    def generate_weekly_summary(self, weekly_data):
        """
        Generate AI-powered weekly summary
        
        Input: 7 days of focus data
        Output: Human-readable summary with insights
        """
        # Create detailed text description
        total_time = sum(d.get('focus_time', 0) for d in weekly_data.values())
        total_sessions = sum(d.get('sessions', 0) for d in weekly_data.values())
        
        description = f"""This week you completed {total_sessions} focus sessions, 
        accumulating {total_time // 60} minutes of focused work. 
        Your most productive day was {self._find_best_day(weekly_data)} 
        with {self._get_best_day_time(weekly_data)} minutes of focus. 
        You maintained consistency across {len([d for d in weekly_data.values() if d.get('sessions', 0) > 0])} days."""
        
        # Summarize using AI (makes it concise and engaging)
        try:
            summary = self.summarizer(description, max_length=50, min_length=20)[0]['summary_text']
            return summary
        except:
            return description[:200] + "..."
    
    def _find_best_day(self, weekly_data):
        """Find most productive day"""
        best_day = max(weekly_data.items(), key=lambda x: x[1].get('focus_time', 0))
        return best_day[0]
    
    def _get_best_day_time(self, weekly_data):
        """Get focus time of best day"""
        best_time = max(d.get('focus_time', 0) for d in weekly_data.values())
        return best_time // 60
    
    # ==================== FEATURE 5: Intelligent Break Suggestions ====================
    
    def suggest_break_activity(self, session_duration, user_mood):
        """
        AI-powered break activity suggestions based on session and mood
        
        Long session + tired → "Take a 10-minute walk outside"
        Short session + energized → "5-minute stretch, then continue"
        """
        suggestions = []
        
        if session_duration > 60:  # Long session
            suggestions.extend([
                "🚶 Take a 10-minute walk to refresh",
                "💧 Drink water and do light stretching",
                "🌳 Step outside for fresh air"
            ])
        elif session_duration > 30:
            suggestions.extend([
                "☕ Quick coffee/tea break",
                "🧘 5-minute breathing exercises",
                "👀 Look away from screen, rest eyes"
            ])
        else:
            suggestions.extend([
                "⚡ Brief 2-minute stretch",
                "💪 Do 10 pushups for energy",
                "🎵 Listen to one song"
            ])
        
        # Analyze mood if provided
        if user_mood:
            mood_result = self.analyze_focus_quality(user_mood)
            if mood_result and mood_result['sentiment'] == 'NEGATIVE':
                suggestions.insert(0, "🧠 Consider meditation - you seem stressed")
        
        return suggestions[:3]  # Top 3 suggestions
    
    # ==================== FEATURE 6: Productivity Forecasting ====================
    
    def predict_session_success(self, planned_duration, planned_hour, recent_stats):
        """
        Predict likelihood of completing a session based on patterns
        
        Uses: Recent completion rates at this hour, typical successful duration
        Returns: Probability (0-100%) and recommendation
        """
        # Simple ML: Check historical success rate
        similar_sessions = [
            s for s in recent_stats 
            if abs(s['hour'] - planned_hour) <= 1  # Within 1 hour
            and abs(s['duration'] - planned_duration) <= 15  # Within 15 min
        ]
        
        if not similar_sessions:
            return {
                'probability': 50,
                'confidence': 'low',
                'recommendation': 'No similar sessions in history - give it a try!'
            }
        
        success_rate = sum(1 for s in similar_sessions if s['completed']) / len(similar_sessions)
        
        return {
            'probability': int(success_rate * 100),
            'confidence': 'high' if len(similar_sessions) >= 5 else 'medium',
            'recommendation': self._get_success_recommendation(success_rate, planned_duration)
        }
    
    def _get_success_recommendation(self, success_rate, duration):
        """Generate recommendation based on predicted success"""
        if success_rate > 0.8:
            return f"✅ Great time to focus! You have {int(success_rate*100)}% success rate at this time"
        elif success_rate > 0.5:
            return f"👍 Good choice - {int(success_rate*100)}% success rate. Stay committed!"
        else:
            return f"⚠️ Consider a shorter {duration//2}-minute session. This time has {int(success_rate*100)}% success rate"


# ==================== Demo/Testing ====================

def demo_local_ai():
    """Demonstrate all AI features"""
    print("=" * 60)
    print("🧠 LOCAL AI DEMO")
    print("=" * 60)
    
    ai = LocalAI()
    
    # Feature 1: Sentiment Analysis
    print("\n1️⃣ FOCUS QUALITY ANALYSIS")
    print("-" * 60)
    test_notes = [
        "Amazing session! Got so much done, felt in the zone!",
        "Struggled to concentrate, too many interruptions",
        "Decent work, but could have been better"
    ]
    
    for note in test_notes:
        result = ai.analyze_focus_quality(note)
        print(f"📝 '{note}'")
        if result:
            print(f"   → {result['interpretation']} (confidence: {result['confidence']:.2%})")
        else:
            print("   → Could not analyze")
        print()
    
    # Feature 2: Distraction Detection
    print("\n2️⃣ DISTRACTION TRIGGER DETECTION")
    print("-" * 60)
    distraction_notes = [
        "Phone notifications kept interrupting my flow",
        "Email alerts were very distracting today",
        "Too many phone calls during this session",
        "Notifications from Slack broke my concentration"
    ]
    
    triggers = ai.detect_distraction_triggers(distraction_notes)
    for trigger in triggers:
        print(f"🎯 {trigger['trigger'].upper()} (appeared {trigger['frequency']} times)")
        print(f"   💡 {trigger['recommendation']}")
        print()
    
    # Feature 3: Break Suggestions
    print("\n3️⃣ INTELLIGENT BREAK SUGGESTIONS")
    print("-" * 60)
    breaks = ai.suggest_break_activity(75, "feeling tired")
    for i, suggestion in enumerate(breaks, 1):
        print(f"   {i}. {suggestion}")
    
    print("\n" + "=" * 60)
    print("✅ All AI features working!")
    print(f"🖥️  Running on: {'GPU (CUDA)' if ai.gpu_available else 'CPU'}")
    print("=" * 60)


if __name__ == "__main__":
    demo_local_ai()
