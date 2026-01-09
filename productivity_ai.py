"""
AI-Powered Productivity Analyzer
Analyzes your blocking patterns and provides intelligent insights
"""

import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, Union

logger = logging.getLogger(__name__)


class ProductivityAnalyzer:
    """AI-powered productivity insights"""

    def __init__(self, stats_path: Union[str, Path]) -> None:
        self.stats_path = Path(stats_path)
        self.stats: Dict[str, Any] = self._load_stats()

    def _load_stats(self) -> Dict[str, Any]:
        if self.stats_path.exists():
            try:
                with open(self.stats_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError, OSError):
                return {}
        return {}

    def get_peak_productivity_hours(self) -> Dict[str, Dict[str, int]]:
        """Identify when user is most productive"""
        hourly_data: Dict[str, Dict[str, int]] = defaultdict(lambda: {'count': 0, 'total_time': 0})

        # Analyze session start times (would need to track this)
        for date, data in self.stats.get('daily_stats', {}).items():
            # Simplified - in real implementation, track session times
            focus_time = data.get('focus_time', 0)
            if focus_time > 0:
                # Mock analysis - you'd track actual session start hours
                morning = 9 <= datetime.now().hour < 12
                if morning:
                    hourly_data['morning']['count'] += 1
                    hourly_data['morning']['total_time'] += focus_time

        return dict(hourly_data)

    def predict_optimal_session_length(self) -> int:
        """ML-based prediction of optimal session duration"""
        # Analyze completion rates by duration
        # This is simplified - you'd track actual session durations and completion
        completed = self.stats.get('sessions_completed', 0)
        cancelled = self.stats.get('sessions_cancelled', 0)

        if completed + cancelled > 10:
            completion_rate = completed / (completed + cancelled)

            if completion_rate > 0.8:
                return 45  # User completes most sessions, can go longer
            elif completion_rate > 0.6:
                return 25  # Standard Pomodoro
            else:
                return 15  # Shorter sessions needed

        return 25  # Default

    def get_distraction_patterns(self):
        """Identify patterns in when user gets distracted"""
        patterns = {
            'weekday_vs_weekend': self._analyze_weekday_weekend(),
            'time_of_day': 'mornings' if datetime.now().hour < 12 else 'afternoons',
            'consistency': self._calculate_consistency(),
        }
        return patterns

    def _analyze_weekday_weekend(self):
        """Compare weekday vs weekend productivity"""
        weekday_total = 0
        weekend_total = 0

        for date_str, data in self.stats.get('daily_stats', {}).items():
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
                time_spent = data.get('focus_time', 0)

                if date.weekday() < 5:
                    weekday_total += time_spent
                else:
                    weekend_total += time_spent
            except (ValueError, TypeError, KeyError):
                continue

        if weekday_total > weekend_total * 1.5:
            return 'weekdays'
        elif weekend_total > weekday_total * 1.5:
            return 'weekends'
        return 'balanced'

    def _calculate_consistency(self):
        """Calculate how consistent user's focus sessions are"""
        daily_stats = self.stats.get('daily_stats', {})
        if len(daily_stats) < 7:
            return 'building'

        recent_days = sorted(daily_stats.keys())[-7:]
        focus_times = [daily_stats[d].get('focus_time', 0) for d in recent_days]

        avg = sum(focus_times) / len(focus_times)
        variance = sum((t - avg) ** 2 for t in focus_times) / len(focus_times)

        if variance < 100:
            return 'very_consistent'
        elif variance < 500:
            return 'consistent'
        else:
            return 'inconsistent'

    def generate_insights(self):
        """Generate actionable insights"""
        insights = []

        # Streak insights
        streak = self.stats.get('streak_days', 0)
        if streak >= 7:
            insights.append({
                'type': 'achievement',
                'title': '🔥 Amazing Streak!',
                'message': f"You've focused for {streak} days straight! Keep it up!",
                'action': None
            })
        elif streak == 0:
            last_date = self.stats.get('last_session_date')
            if last_date:
                insights.append({
                    'type': 'warning',
                    'title': '⚠️ Streak Broken',
                    'message': 'Start a session today to rebuild your streak!',
                    'action': 'start_session'
                })

        # Productivity pattern
        pattern = self._analyze_weekday_weekend()
        if pattern == 'weekdays':
            insights.append({
                'type': 'info',
                'title': '💼 Weekday Warrior',
                'message': 'You focus more on weekdays. Consider weekend review sessions.',
                'action': 'schedule_weekend'
            })

        # Session completion rate
        completed = self.stats.get('sessions_completed', 0)
        cancelled = self.stats.get('sessions_cancelled', 0)
        if completed + cancelled > 5:
            rate = completed / (completed + cancelled)
            if rate < 0.5:
                insights.append({
                    'type': 'tip',
                    'title': '💡 Try Shorter Sessions',
                    'message': f'You cancel {int((1-rate)*100)}% of sessions. Try 15-min sessions!',
                    'action': 'suggest_short'
                })

        # Total time milestone
        total_hours = self.stats.get('total_focus_time', 0) / 3600
        milestones = [10, 25, 50, 100, 250, 500, 1000]
        for m in milestones:
            if total_hours < m < total_hours + 5:
                insights.append({
                    'type': 'achievement',
                    'title': f'🎯 Approaching {m} Hours!',
                    'message': f'Only {m - int(total_hours)} hours to your next milestone!',
                    'action': None
                })
                break

        return insights

    def get_recommendations(self):
        """Get personalized recommendations"""
        recommendations = []

        optimal_length = self.predict_optimal_session_length()
        recommendations.append({
            'category': 'session_length',
            'suggestion': f'Try {optimal_length}-minute sessions',
            'reason': 'Based on your completion patterns',
            'confidence': 0.8
        })

        # Check consistency
        consistency = self._calculate_consistency()
        if consistency == 'inconsistent':
            recommendations.append({
                'category': 'consistency',
                'suggestion': 'Set up daily schedule at same time',
                'reason': 'Your focus times vary widely',
                'confidence': 0.9
            })

        # Check if using strict mode
        if self.stats.get('sessions_cancelled', 0) > self.stats.get('sessions_completed', 0):
            recommendations.append({
                'category': 'mode',
                'suggestion': 'Enable Strict Mode with password',
                'reason': 'You cancel more than you complete',
                'confidence': 0.85
            })

        return recommendations


class GamificationEngine:
    """Gamification system with achievements and challenges"""

    ACHIEVEMENTS = {
        'first_session': {
            'icon': '🎬',
            'name': 'First Steps',
            'desc': 'Complete your first focus session',
            'requirement': lambda s: s.get('sessions_completed', 0) >= 1
        },
        'dedicated': {
            'icon': '⭐',
            'name': 'Dedicated',
            'desc': 'Complete 10 focus sessions',
            'requirement': lambda s: s.get('sessions_completed', 0) >= 10
        },
        'week_warrior': {
            'icon': '📅',
            'name': 'Week Warrior',
            'desc': 'Maintain a 7-day streak',
            'requirement': lambda s: s.get('streak_days', 0) >= 7
        },
        'century_club': {
            'icon': '💯',
            'name': 'Century Club',
            'desc': 'Complete 100 focus sessions',
            'requirement': lambda s: s.get('sessions_completed', 0) >= 100
        },
        'marathon': {
            'icon': '🏃',
            'name': 'Marathon',
            'desc': 'Accumulate 1000 minutes focus time',
            'requirement': lambda s: (s.get('total_focus_time', 0) // 60) >= 1000
        },
        'perfectionist': {
            'icon': '⭐',
            'name': 'Perfectionist',
            'desc': 'Complete 10 sessions without canceling',
            'requirement': lambda s: (s.get('sessions_completed', 0) >= 10 and
                                     s.get('sessions_cancelled', 0) == 0)
        },
        'early_bird': {
            'icon': '🌅',
            'name': 'Early Bird',
            'desc': 'Complete 10 sessions before 9 AM',
            'requirement': lambda s: s.get('early_sessions', 0) >= 10
        },
        'night_owl': {
            'icon': '🦉',
            'name': 'Night Owl',
            'desc': 'Complete 10 sessions after 9 PM',
            'requirement': lambda s: s.get('night_sessions', 0) >= 10
        },
        'fire_keeper': {
            'icon': '🔥',
            'name': 'Fire Keeper',
            'desc': 'Maintain a 30-day streak',
            'requirement': lambda s: s.get('best_streak', 0) >= 30
        },
        'iron_will': {
            'icon': '🛡️',
            'name': 'Iron Will',
            'desc': 'Complete 10 strict mode sessions',
            'requirement': lambda s: s.get('strict_sessions', 0) >= 10
        },
        'pomodoro_pro': {
            'icon': '🍅',
            'name': 'Pomodoro Pro',
            'desc': 'Complete 25 Pomodoro sessions',
            'requirement': lambda s: s.get('pomodoro_sessions', 0) >= 25
        },
    }

    def __init__(self, stats_path):
        self.stats_path = Path(stats_path)
        self.stats = self._load_stats()
        self.unlocked = self.stats.get('achievements_unlocked', [])

    def _load_stats(self):
        """Load statistics from file"""
        if self.stats_path.exists():
            try:
                with open(self.stats_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError, OSError):
                return {}
        return {}

    def _save_stats(self):
        """Save statistics to file"""
        try:
            with open(self.stats_path, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save stats: {e}")

    def check_achievements(self):
        """Check which achievements are newly unlocked"""
        # Reload stats to get latest
        self.stats = self._load_stats()
        self.unlocked = self.stats.get('achievements_unlocked', [])
        newly_unlocked = []

        for ach_id, achievement in self.ACHIEVEMENTS.items():
            if ach_id not in self.unlocked:
                if achievement['requirement'](self.stats):
                    newly_unlocked.append({
                        'id': ach_id,
                        'name': achievement['name'],
                        'desc': achievement['desc']
                    })
                    self.unlocked.append(ach_id)

        # Save updated unlocked achievements
        if newly_unlocked:
            self.stats['achievements_unlocked'] = self.unlocked
            self._save_stats()

        # Return progress for all achievements
        progress = {}
        for ach_id, achievement in self.ACHIEVEMENTS.items():
            # Get current progress based on achievement type
            current, target = self._get_achievement_progress(ach_id, achievement)

            progress[ach_id] = {
                'current': current,
                'target': target,
                'unlocked': ach_id in self.unlocked
            }

        return progress

    def _get_achievement_progress(self, ach_id, achievement):
        """Get current and target values for an achievement"""
        # Map achievement IDs to their progress metrics
        progress_map = {
            'first_session': (self.stats.get('sessions_completed', 0), 1),
            'dedicated': (self.stats.get('sessions_completed', 0), 10),
            'week_warrior': (self.stats.get('streak_days', 0), 7),
            'century_club': (self.stats.get('sessions_completed', 0), 100),
            'marathon': (self.stats.get('total_focus_time', 0) // 60, 1000),  # minutes
            'perfectionist': (self.stats.get('sessions_completed', 0), 10),
            'early_bird': (self.stats.get('early_sessions', 0), 10),
            'night_owl': (self.stats.get('night_sessions', 0), 10),
            'fire_keeper': (self.stats.get('best_streak', 0), 30),
            'iron_will': (self.stats.get('strict_sessions', 0), 10),
            'pomodoro_pro': (self.stats.get('pomodoro_sessions', 0), 25),
        }

        return progress_map.get(ach_id, (0, 1))

    def get_progress(self):
        """Get progress towards locked achievements"""
        progress = []

        for ach_id, achievement in self.ACHIEVEMENTS.items():
            if ach_id not in self.unlocked:
                # Calculate progress (simplified)
                if 'sessions_completed' in achievement['desc']:
                    current = self.stats.get('sessions_completed', 0)
                    # Extract number from description
                    import re
                    match = re.search(r'\d+', achievement['desc'])
                    if match:
                        target = int(match.group())
                        progress.append({
                            'id': ach_id,
                            'name': achievement['name'],
                            'desc': achievement['desc'],
                            'progress': min(100, int((current / target) * 100))
                        })

        return progress

    def get_achievements(self):
        """Get all achievement definitions with icons and descriptions"""
        achievements_with_details = {}

        for ach_id, achievement in self.ACHIEVEMENTS.items():
            achievements_with_details[ach_id] = {
                'icon': achievement['icon'],
                'name': achievement['name'],
                'description': achievement['desc']
            }

        return achievements_with_details

    def get_daily_challenge(self):
        """Generate a daily challenge"""
        today = datetime.now().strftime('%Y-%m-%d')
        challenges = [
            {
                'title': '🎯 Power Hour',
                'description': 'Complete 60 minutes of focused work',
                'target': 3600,
                'type': 'time'
            },
            {
                'title': '🔥 Triple Threat',
                'description': 'Complete 3 focus sessions',
                'target': 3,
                'type': 'sessions'
            },
            {
                'title': '⚡ Sprint Master',
                'description': 'Complete 6 Pomodoro cycles',
                'target': 6,
                'type': 'pomodoro'
            },
            {
                'title': '💪 Endurance Test',
                'description': 'One uninterrupted 90-minute session',
                'target': 5400,
                'type': 'single_session'
            },
        ]

        # Rotate based on day of year
        day_of_year = datetime.now().timetuple().tm_yday
        daily_challenge = challenges[day_of_year % len(challenges)]

        # Check progress
        today_stats = self.stats.get('daily_stats', {}).get(today, {})
        if daily_challenge['type'] == 'time':
            current = today_stats.get('focus_time', 0)
            target = daily_challenge['target']
        elif daily_challenge['type'] == 'sessions':
            current = today_stats.get('sessions', 0)
            target = daily_challenge['target']
        else:
            current = 0
            target = daily_challenge['target']

        daily_challenge['progress'] = {
            'current': current,
            'target': target
        }
        daily_challenge['completed'] = current >= target

        return daily_challenge

    def get_leaderboard_rank(self, total_users=1000):
        """Simulate leaderboard ranking"""
        total_time = self.stats.get('total_focus_time', 0) / 3600

        # Simulate ranking based on total hours
        if total_time > 500:
            rank = 10
            percentile = 99
        elif total_time > 250:
            rank = 50
            percentile = 95
        elif total_time > 100:
            rank = 150
            percentile = 85
        elif total_time > 50:
            rank = 300
            percentile = 70
        else:
            rank = 600
            percentile = 40

        return {
            'rank': rank,
            'total_users': total_users,
            'percentile': percentile,
            'next_rank_hours': (rank - 1) * 0.5  # Simplified
        }


class FocusGoals:
    """Goal setting and tracking system"""

    def __init__(self, goals_path, stats_path=None):
        self.goals_path = Path(goals_path)
        self.stats_path = Path(stats_path) if stats_path else None
        self.goals = self._load_goals()
        self.stats = self._load_stats() if stats_path else {}

    def _load_stats(self):
        """Load statistics from file"""
        if self.stats_path and self.stats_path.exists():
            try:
                with open(self.stats_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError, OSError):
                return {}
        return {}

    def _load_goals(self):
        if self.goals_path.exists():
            try:
                with open(self.goals_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError, OSError):
                return []
        return []

    def save_goals(self):
        with open(self.goals_path, 'w', encoding='utf-8') as f:
            json.dump(self.goals, f, indent=2)

    def add_goal(self, title, goal_type, target, deadline=None):
        """Add a new goal"""
        import uuid
        goal = {
            'id': str(uuid.uuid4())[:8],
            'title': title,
            'type': goal_type,  # 'daily', 'weekly', 'monthly', 'custom'
            'target': target,
            'deadline': deadline,
            'created': datetime.now().isoformat(),
            'completed': False,
            'progress': 0
        }
        self.goals.append(goal)
        self.save_goals()
        return goal['id']

    def update_progress(self, focus_minutes=None):
        """Update progress on all goals"""
        # Reload stats if available
        if self.stats_path:
            self.stats = self._load_stats()

        today = datetime.now().strftime('%Y-%m-%d')

        for goal in self.goals:
            if goal['completed']:
                continue

            if goal['type'] == 'daily':
                if focus_minutes is not None:
                    goal['progress'] = goal.get('progress', 0) + (focus_minutes * 60)  # convert to seconds
                else:
                    today_stats = self.stats.get('daily_stats', {}).get(today, {})
                    goal['progress'] = today_stats.get('focus_time', 0)
            elif goal['type'] == 'weekly':
                # Calculate last 7 days
                total = 0
                for i in range(7):
                    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                    daily = self.stats.get('daily_stats', {}).get(date, {})
                    total += daily.get('focus_time', 0)
                goal['progress'] = total
            elif goal['type'] == 'custom':
                # For custom goals, use total stats
                total = self.stats.get('best_streak', 0)
                goal['progress'] = total

            if goal['progress'] >= goal['target']:
                goal['completed'] = True

        self.save_goals()

    def get_active_goals(self):
        """Get all active (not completed) goals"""
        return [g for g in self.goals if not g['completed']]

    def suggest_goals(self):
        """Suggest goals based on user's patterns"""
        return self.get_goal_suggestions(self.stats)

    def complete_goal(self, goal_id):
        """Mark a goal as completed"""
        for goal in self.goals:
            if goal['id'] == goal_id:
                goal['completed'] = True
                goal['progress'] = goal['target']
                break
        self.save_goals()

    def get_goal_suggestions(self, stats):
        """Suggest goals based on user's patterns"""
        suggestions = []

        # Check current average
        recent_avg = self._get_recent_average(stats)

        if recent_avg < 1800:  # Less than 30 min/day
            suggestions.append({
                'type': 'daily',
                'target': 1800,
                'title': 'Daily 30 Minutes',
                'desc': 'Build the habit with 30 min daily'
            })
        elif recent_avg < 3600:
            suggestions.append({
                'type': 'daily',
                'target': 3600,
                'title': 'Daily Power Hour',
                'desc': 'Level up to 1 hour daily'
            })

        # Weekly goals
        suggestions.append({
            'type': 'weekly',
            'target': 18000,  # 5 hours
            'title': 'Weekly 5 Hours',
            'desc': 'Accumulate 5 focused hours this week'
        })

        return suggestions

    def _get_recent_average(self, stats):
        """Calculate average focus time over last 7 days"""
        total = 0
        count = 0
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            daily = stats.get('daily_stats', {}).get(date, {})
            time = daily.get('focus_time', 0)
            if time > 0:
                total += time
                count += 1
        return total / count if count > 0 else 0
