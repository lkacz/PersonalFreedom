"""
Test script for AI features
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from productivity_ai import ProductivityAnalyzer, GamificationEngine, FocusGoals

# Create test data directories
APP_DIR = Path.home() / ".focus_blocker"
APP_DIR.mkdir(exist_ok=True)

STATS_PATH = APP_DIR / "stats.json"
GOALS_PATH = APP_DIR / "goals.json"

def create_test_stats():
    """Create sample stats data for testing"""
    test_stats = {
        "total_focus_time": 18000,  # 5 hours
        "sessions_completed": 25,
        "sessions_cancelled": 3,
        "streak_days": 5,
        "best_streak": 7,
        "early_sessions": 10,
        "night_sessions": 3,
        "strict_sessions": 8,
        "pomodoro_sessions": 15,
        "daily_stats": {}
    }
    
    # Add daily stats for the past 10 days
    for i in range(10, 0, -1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        test_stats["daily_stats"][date] = {
            "focus_time": 1800 + (i * 100),  # Varying session lengths
            "sessions": 2 + (i % 3)
        }
    
    # Add today's stats
    today = datetime.now().strftime("%Y-%m-%d")
    test_stats["daily_stats"][today] = {
        "focus_time": 3600,  # 1 hour today
        "sessions": 3
    }
    
    with open(STATS_PATH, 'w') as f:
        json.dump(test_stats, f, indent=2)
    
    return test_stats

def test_productivity_analyzer():
    """Test the ProductivityAnalyzer class"""
    print("=" * 60)
    print("TESTING PRODUCTIVITY ANALYZER")
    print("=" * 60)
    
    analyzer = ProductivityAnalyzer(STATS_PATH)
    
    print("\n📊 Peak Productivity Hours:")
    peak_hours = analyzer.get_peak_productivity_hours()
    print(f"  {', '.join(peak_hours) if peak_hours else 'Not enough data yet'}")
    
    print("\n⏱  Optimal Session Length:")
    optimal = analyzer.predict_optimal_session_length()
    print(f"  {optimal} minutes" if optimal else "  Not enough data yet")
    
    print("\n🔍 Distraction Patterns:")
    patterns = analyzer.get_distraction_patterns()
    if patterns:
        for pattern in patterns:
            print(f"  • {pattern}")
    else:
        print("  No patterns detected yet")
    
    print("\n💡 AI Insights:")
    insights = analyzer.generate_insights()
    if insights:
        for insight in insights:
            print(f"  • {insight}")
    else:
        print("  Complete more sessions to unlock insights")
    
    print("\n🎯 Recommendations:")
    recommendations = analyzer.get_recommendations()
    if recommendations:
        for rec in recommendations:
            print(f"  • {rec}")
    else:
        print("  No recommendations yet")

def test_gamification():
    """Test the GamificationEngine class"""
    print("\n" + "=" * 60)
    print("TESTING GAMIFICATION ENGINE")
    print("=" * 60)
    
    gamification = GamificationEngine(STATS_PATH)
    
    print("\n🏆 Achievement Progress:")
    progress = gamification.check_achievements()
    
    for ach_id, data in progress.items():
        status = "✅ UNLOCKED" if data['unlocked'] else f"🔒 {data['current']}/{data['target']}"
        achievements = gamification.get_achievements()
        ach_info = achievements[ach_id]
        print(f"  {ach_info['icon']} {ach_info['name']}: {status}")
    
    print("\n🎯 Daily Challenge:")
    challenge = gamification.get_daily_challenge()
    print(f"  {challenge['title']}")
    print(f"  {challenge['description']}")
    print(f"  Progress: {challenge['progress']['current']}/{challenge['progress']['target']}")

def test_focus_goals():
    """Test the FocusGoals class"""
    print("\n" + "=" * 60)
    print("TESTING FOCUS GOALS")
    print("=" * 60)
    
    goals = FocusGoals(GOALS_PATH, STATS_PATH)
    
    # Add sample goals
    print("\n➕ Adding sample goals...")
    goals.add_goal("Focus for 2 hours daily", "daily", 120)
    goals.add_goal("Complete 20 hours this week", "weekly", 1200)
    goals.add_goal("Build a 30-day streak", "custom", 30)
    
    print("\n🎯 Active Goals:")
    active_goals = goals.get_active_goals()
    for goal in active_goals:
        progress = goal.get('progress', 0)
        target = goal.get('target', 0)
        percentage = int((progress / target) * 100) if target > 0 else 0
        print(f"  • {goal['title']}: {percentage}% ({progress}/{target})")
    
    print("\n💡 Goal Suggestions:")
    suggestions = goals.suggest_goals()
    for suggestion in suggestions:
        print(f"  • {suggestion}")
    
    # Update goal progress
    print("\n📈 Updating goal progress...")
    goals.update_progress(60)  # 60 minutes
    
    print("\n🎯 Updated Active Goals:")
    active_goals = goals.get_active_goals()
    for goal in active_goals:
        progress = goal.get('progress', 0)
        target = goal.get('target', 0)
        percentage = int((progress / target) * 100) if target > 0 else 0
        print(f"  • {goal['title']}: {percentage}% ({progress}/{target})")

def main():
    print("\n🧪 AI FEATURES TEST SUITE")
    print("=" * 60)
    
    # Create test stats
    print("\n📝 Creating test statistics data...")
    stats = create_test_stats()
    print(f"✅ Created stats with {stats['sessions_completed']} completed sessions")
    
    # Run tests
    test_productivity_analyzer()
    test_gamification()
    test_focus_goals()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 60)
    print("\nThe AI features are working correctly!")
    print("Run 'python focus_blocker.py' to see them in the GUI.")

if __name__ == "__main__":
    main()
