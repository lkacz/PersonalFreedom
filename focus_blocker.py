"""
Personal Freedom - Website Blocker for Focus Time
A Windows application to block distracting websites during focus sessions.

Enhanced Version with Industry-Standard Features:
- Multiple blocking modes (Strict, Normal, Pomodoro)
- Schedule-based blocking
- Statistics and productivity tracking
- Password protection
- Break reminders
- Import/Export blacklists
- Website categories
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import time
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from core_logic import (
    BlockerCore, BlockMode, SITE_CATEGORIES, 
    AI_AVAILABLE, LOCAL_AI_AVAILABLE,
    APP_DIR, STATS_PATH, GOALS_PATH
)

# Re-import AI classes if available, for GUI usage
if AI_AVAILABLE:
    from productivity_ai import ProductivityAnalyzer, GamificationEngine, FocusGoals
else:
    # Stub classes when AI not available
    ProductivityAnalyzer = None  # type: ignore
    GamificationEngine = None  # type: ignore
    FocusGoals = None  # type: ignore

if LOCAL_AI_AVAILABLE:
    from local_ai import LocalAI
else:
    LocalAI = None  # type: ignore


class FocusBlockerGUI:
    """Enhanced GUI with tabbed interface"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Freedom - Focus Blocker")
        self.root.geometry("600x700")
        self.root.minsize(550, 600)
        
        self.blocker = BlockerCore()
        self.timer_running = False
        self.remaining_seconds = 0
        self._timer_lock = threading.Lock()
        self.session_start_time = None
        
        # Apply theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._configure_styles()
        
        self.setup_ui()
        self.check_admin_status()
        self.update_stats_display()
        
        # Check for scheduled blocking
        self.check_scheduled_blocking()
    
    def _configure_styles(self):
        """Configure custom styles"""
        self.style.configure('Title.TLabel', font=('Segoe UI', 20, 'bold'))
        self.style.configure('Timer.TLabel', font=('Consolas', 42, 'bold'))
        self.style.configure('Status.TLabel', font=('Segoe UI', 11, 'bold'))
        self.style.configure('Stats.TLabel', font=('Segoe UI', 10))
        self.style.configure('Header.TLabel', font=('Segoe UI', 11, 'bold'))
        
        # Button styles
        self.style.configure('Start.TButton', font=('Segoe UI', 10, 'bold'))
        self.style.configure('Stop.TButton', font=('Segoe UI', 10))
        self.style.configure('Category.TCheckbutton', font=('Segoe UI', 10))
    
    def setup_ui(self):
        """Setup the tabbed user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="🔒 Personal Freedom", 
                  style='Title.TLabel').pack(side=tk.LEFT)
        
        self.admin_label = ttk.Label(header_frame, text="", font=('Segoe UI', 9))
        self.admin_label.pack(side=tk.RIGHT, padx=10)
        
        # Notebook (Tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Timer
        self.timer_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.timer_tab, text="⏱ Timer")
        self.setup_timer_tab()
        
        # Tab 2: Sites
        self.sites_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.sites_tab, text="🌐 Sites")
        self.setup_sites_tab()
        
        # Tab 3: Categories
        self.categories_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.categories_tab, text="📁 Categories")
        self.setup_categories_tab()
        
        # Tab 4: Schedule
        self.schedule_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.schedule_tab, text="📅 Schedule")
        self.setup_schedule_tab()
        
        # Tab 5: Stats
        self.stats_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.stats_tab, text="📊 Stats")
        self.setup_stats_tab()
        
        # Tab 6: Settings
        self.settings_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.settings_tab, text="⚙ Settings")
        self.setup_settings_tab()
        
        # Tab 7: AI Insights (if available)
        if AI_AVAILABLE:
            self.ai_tab = ttk.Frame(self.notebook, padding="10")
            self.notebook.add(self.ai_tab, text="🧠 AI Insights")
            self.setup_ai_tab()
    
    def setup_timer_tab(self):
        """Setup the timer tab"""
        # Timer display
        timer_frame = ttk.LabelFrame(self.timer_tab, text="Focus Timer", padding="15")
        timer_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.timer_display = ttk.Label(timer_frame, text="00:00:00", style='Timer.TLabel')
        self.timer_display.pack(pady=15)
        
        # Mode selection
        mode_frame = ttk.Frame(timer_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mode_frame, text="Mode:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        self.mode_var = tk.StringVar(value=BlockMode.NORMAL)
        
        modes = [("Normal", BlockMode.NORMAL), ("Strict 🔐", BlockMode.STRICT), 
                 ("Pomodoro 🍅", BlockMode.POMODORO)]
        for text, mode in modes:
            ttk.Radiobutton(mode_frame, text=text, value=mode, 
                           variable=self.mode_var).pack(side=tk.LEFT, padx=10)
        
        # Time input
        time_frame = ttk.Frame(timer_frame)
        time_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(time_frame, text="Duration:").pack(side=tk.LEFT, padx=5)
        
        self.hours_var = tk.StringVar(value="0")
        ttk.Spinbox(time_frame, from_=0, to=12, width=4, 
                    textvariable=self.hours_var).pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame, text="h").pack(side=tk.LEFT)
        
        self.minutes_var = tk.StringVar(value="25")
        ttk.Spinbox(time_frame, from_=0, to=59, width=4,
                    textvariable=self.minutes_var).pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame, text="m").pack(side=tk.LEFT)
        
        # Quick buttons
        quick_frame = ttk.Frame(timer_frame)
        quick_frame.pack(fill=tk.X, pady=10)
        
        presets = [("25m", 25), ("45m", 45), ("1h", 60), ("2h", 120), ("4h", 240)]
        for text, mins in presets:
            ttk.Button(quick_frame, text=text, width=6,
                      command=lambda m=mins: self.set_quick_time(m)).pack(side=tk.LEFT, padx=3, expand=True)
        
        # Control buttons
        btn_frame = ttk.Frame(timer_frame)
        btn_frame.pack(fill=tk.X, pady=15)
        
        self.start_btn = ttk.Button(btn_frame, text="▶ Start Focus", 
                                    command=self.start_session, style='Start.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.stop_btn = ttk.Button(btn_frame, text="⬛ Stop", 
                                   command=self.stop_session, style='Stop.TButton', 
                                   state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Status
        self.status_label = ttk.Label(timer_frame, text="Ready to focus", 
                                      style='Status.TLabel')
        self.status_label.pack(pady=5)
        
        # Quick stats
        stats_frame = ttk.LabelFrame(self.timer_tab, text="Today's Progress", padding="10")
        stats_frame.pack(fill=tk.X, pady=10)
        
        self.quick_stats_label = ttk.Label(stats_frame, text="", style='Stats.TLabel')
        self.quick_stats_label.pack()
    
    def setup_sites_tab(self):
        """Setup the sites management tab"""
        # Blacklist frame
        black_frame = ttk.LabelFrame(self.sites_tab, text="Blocked Sites (Custom)", padding="10")
        black_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(black_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.site_listbox = tk.Listbox(list_frame, height=10, font=('Consolas', 10),
                                       yscrollcommand=scrollbar.set, selectmode=tk.EXTENDED)
        self.site_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.site_listbox.yview)
        
        # Add/Remove controls
        ctrl_frame = ttk.Frame(black_frame)
        ctrl_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.site_entry = ttk.Entry(ctrl_frame, font=('Segoe UI', 10))
        self.site_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.site_entry.bind('<Return>', lambda e: self.add_site())
        
        ttk.Button(ctrl_frame, text="+ Add", command=self.add_site, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="- Remove", command=self.remove_site, width=8).pack(side=tk.LEFT, padx=2)
        
        # Whitelist frame
        white_frame = ttk.LabelFrame(self.sites_tab, text="Whitelist (Never Block)", padding="10")
        white_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        list_frame2 = ttk.Frame(white_frame)
        list_frame2.pack(fill=tk.BOTH, expand=True)
        
        scrollbar2 = ttk.Scrollbar(list_frame2)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.whitelist_listbox = tk.Listbox(list_frame2, height=6, font=('Consolas', 10),
                                            yscrollcommand=scrollbar2.set)
        self.whitelist_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.config(command=self.whitelist_listbox.yview)
        
        ctrl_frame2 = ttk.Frame(white_frame)
        ctrl_frame2.pack(fill=tk.X, pady=(10, 0))
        
        self.whitelist_entry = ttk.Entry(ctrl_frame2, font=('Segoe UI', 10))
        self.whitelist_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(ctrl_frame2, text="+ Add", command=self.add_whitelist, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame2, text="- Remove", command=self.remove_whitelist, width=8).pack(side=tk.LEFT, padx=2)
        
        # Import/Export
        io_frame = ttk.Frame(self.sites_tab)
        io_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(io_frame, text="📥 Import", command=self.import_sites).pack(side=tk.LEFT, padx=5)
        ttk.Button(io_frame, text="📤 Export", command=self.export_sites).pack(side=tk.LEFT, padx=5)
        
        self.update_site_lists()
    
    def setup_categories_tab(self):
        """Setup the categories tab"""
        ttk.Label(self.categories_tab, text="Enable/disable entire categories of sites:",
                  style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        self.category_vars = {}
        
        for category, sites in SITE_CATEGORIES.items():
            frame = ttk.Frame(self.categories_tab)
            frame.pack(fill=tk.X, pady=3)
            
            var = tk.BooleanVar(value=self.blocker.categories_enabled.get(category, True))
            self.category_vars[category] = var
            
            cb = ttk.Checkbutton(frame, text=f"{category} ({len(sites)} sites)", 
                                variable=var, style='Category.TCheckbutton',
                                command=lambda c=category: self.toggle_category(c))
            cb.pack(side=tk.LEFT)
            
            # Show sites button
            ttk.Button(frame, text="View", width=6,
                      command=lambda c=category: self.show_category_sites(c)).pack(side=tk.RIGHT)
        
        # Total count
        ttk.Separator(self.categories_tab).pack(fill=tk.X, pady=15)
        
        self.total_sites_label = ttk.Label(self.categories_tab, text="", style='Stats.TLabel')
        self.total_sites_label.pack()
        self.update_total_sites_count()
    
    def setup_schedule_tab(self):
        """Setup the schedule tab"""
        ttk.Label(self.schedule_tab, text="Automatic blocking schedules:",
                  style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        # Schedule list
        list_frame = ttk.Frame(self.schedule_tab)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('days', 'time', 'status')
        self.schedule_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        self.schedule_tree.heading('days', text='Days')
        self.schedule_tree.heading('time', text='Time')
        self.schedule_tree.heading('status', text='Status')
        self.schedule_tree.column('days', width=200)
        self.schedule_tree.column('time', width=150)
        self.schedule_tree.column('status', width=80)
        self.schedule_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, command=self.schedule_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.schedule_tree.configure(yscrollcommand=scrollbar.set)
        
        # Add schedule controls
        add_frame = ttk.LabelFrame(self.schedule_tab, text="Add Schedule", padding="10")
        add_frame.pack(fill=tk.X, pady=10)
        
        # Days selection
        days_frame = ttk.Frame(add_frame)
        days_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(days_frame, text="Days:").pack(side=tk.LEFT, padx=5)
        
        self.day_vars = []
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            var = tk.BooleanVar(value=i < 5)  # Default: weekdays
            self.day_vars.append(var)
            ttk.Checkbutton(days_frame, text=day, variable=var).pack(side=tk.LEFT, padx=3)
        
        # Time selection
        time_frame = ttk.Frame(add_frame)
        time_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(time_frame, text="From:").pack(side=tk.LEFT, padx=5)
        self.start_hour = ttk.Spinbox(time_frame, from_=0, to=23, width=3, format="%02.0f")
        self.start_hour.set("09")
        self.start_hour.pack(side=tk.LEFT)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        self.start_min = ttk.Spinbox(time_frame, from_=0, to=59, width=3, format="%02.0f")
        self.start_min.set("00")
        self.start_min.pack(side=tk.LEFT)
        
        ttk.Label(time_frame, text="  To:").pack(side=tk.LEFT, padx=5)
        self.end_hour = ttk.Spinbox(time_frame, from_=0, to=23, width=3, format="%02.0f")
        self.end_hour.set("17")
        self.end_hour.pack(side=tk.LEFT)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        self.end_min = ttk.Spinbox(time_frame, from_=0, to=59, width=3, format="%02.0f")
        self.end_min.set("00")
        self.end_min.pack(side=tk.LEFT)
        
        ttk.Button(add_frame, text="+ Add Schedule", command=self.add_schedule).pack(pady=10)
        
        # Schedule actions
        action_frame = ttk.Frame(self.schedule_tab)
        action_frame.pack(fill=tk.X)
        
        ttk.Button(action_frame, text="Toggle", command=self.toggle_schedule).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Delete", command=self.delete_schedule).pack(side=tk.LEFT, padx=5)
        
        self.update_schedule_list()
    
    def setup_stats_tab(self):
        """Setup the statistics tab"""
        # Overview
        overview_frame = ttk.LabelFrame(self.stats_tab, text="Overview", padding="15")
        overview_frame.pack(fill=tk.X, pady=(0, 10))
        
        stats_grid = ttk.Frame(overview_frame)
        stats_grid.pack()
        
        self.stat_labels = {}
        stats = [
            ("total_hours", "Total Focus Time", "0h"),
            ("sessions", "Sessions Completed", "0"),
            ("streak", "Current Streak", "0 days"),
            ("best_streak", "Best Streak", "0 days"),
        ]
        
        for i, (key, label, default) in enumerate(stats):
            row, col = divmod(i, 2)
            frame = ttk.Frame(stats_grid)
            frame.grid(row=row, column=col, padx=20, pady=10)
            
            ttk.Label(frame, text=label, font=('Segoe UI', 9)).pack()
            self.stat_labels[key] = ttk.Label(frame, text=default, 
                                              font=('Segoe UI', 18, 'bold'))
            self.stat_labels[key].pack()
        
        # Weekly chart (simple text-based)
        week_frame = ttk.LabelFrame(self.stats_tab, text="This Week", padding="15")
        week_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.week_chart = tk.Text(week_frame, height=10, font=('Consolas', 10), 
                                  state=tk.DISABLED, bg='#f5f5f5')
        self.week_chart.pack(fill=tk.BOTH, expand=True)
        
        # Reset button
        ttk.Button(self.stats_tab, text="Reset Statistics", 
                   command=self.reset_stats).pack(pady=10)
    
    def setup_settings_tab(self):
        """Setup the settings tab"""
        # Password protection
        pwd_frame = ttk.LabelFrame(self.settings_tab, text="Password Protection", padding="10")
        pwd_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(pwd_frame, text="Set a password to prevent stopping Strict Mode sessions early.",
                  wraplength=400).pack(anchor=tk.W)
        
        pwd_btn_frame = ttk.Frame(pwd_frame)
        pwd_btn_frame.pack(fill=tk.X, pady=10)
        
        self.pwd_status = ttk.Label(pwd_btn_frame, text="No password set")
        self.pwd_status.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(pwd_btn_frame, text="Set Password", 
                   command=self.set_password).pack(side=tk.RIGHT, padx=5)
        ttk.Button(pwd_btn_frame, text="Remove Password", 
                   command=self.remove_password).pack(side=tk.RIGHT, padx=5)
        
        self.update_password_status()
        
        # Pomodoro settings
        pomo_frame = ttk.LabelFrame(self.settings_tab, text="Pomodoro Settings", padding="10")
        pomo_frame.pack(fill=tk.X, pady=10)
        
        settings = [
            ("Work duration (min):", "pomodoro_work", self.blocker.pomodoro_work),
            ("Short break (min):", "pomodoro_break", self.blocker.pomodoro_break),
            ("Long break (min):", "pomodoro_long_break", self.blocker.pomodoro_long_break),
        ]
        
        self.pomo_vars = {}
        for label, key, default in settings:
            frame = ttk.Frame(pomo_frame)
            frame.pack(fill=tk.X, pady=3)
            ttk.Label(frame, text=label, width=20).pack(side=tk.LEFT)
            var = tk.StringVar(value=str(default))
            self.pomo_vars[key] = var
            ttk.Spinbox(frame, from_=1, to=120, width=5, textvariable=var).pack(side=tk.LEFT)
        
        ttk.Button(pomo_frame, text="Save Pomodoro Settings", 
                   command=self.save_pomodoro_settings).pack(pady=10)
        
        # About
        about_frame = ttk.LabelFrame(self.settings_tab, text="About", padding="10")
        about_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(about_frame, text="Personal Freedom v2.0", 
                  font=('Segoe UI', 11, 'bold')).pack()
        ttk.Label(about_frame, text="A focus and productivity tool for Windows",
                  font=('Segoe UI', 9)).pack()
        ttk.Label(about_frame, text="Block distracting websites and track your progress.",
                  font=('Segoe UI', 9)).pack()
        
        # Emergency Cleanup Section
        cleanup_frame = ttk.LabelFrame(self.settings_tab, text="⚠️ Emergency Cleanup", padding="10")
        cleanup_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(cleanup_frame, 
                  text="Use this if websites remain blocked after closing the app,\n"
                       "or if you need to remove all app changes from your system.",
                  wraplength=450, justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 10))
        
        cleanup_btn = ttk.Button(cleanup_frame, text="🧹 Remove All Blocks & Clean System", 
                                 command=self.emergency_cleanup_action)
        cleanup_btn.pack(pady=5)
    
    def setup_ai_tab(self):
        """Setup the AI Insights tab"""
        # Initialize AI engines (guarded by AI_AVAILABLE check in setup_ui)
        self.analyzer = ProductivityAnalyzer(STATS_PATH)  # type: ignore[misc]
        self.gamification = GamificationEngine(STATS_PATH)  # type: ignore[misc]
        self.goals = FocusGoals(GOALS_PATH, STATS_PATH)  # type: ignore[misc]
        
        # Create scrollable canvas
        canvas = tk.Canvas(self.ai_tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.ai_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # === AI Insights Section ===
        insights_frame = ttk.LabelFrame(scrollable_frame, text="🔍 AI Insights & Recommendations", padding="15")
        insights_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.insights_text = tk.Text(insights_frame, height=6, wrap=tk.WORD, 
                                     font=('Segoe UI', 9), bg='#f0f0f0', relief=tk.FLAT)
        self.insights_text.pack(fill=tk.X, pady=5)
        
        ttk.Button(insights_frame, text="🔄 Refresh Insights", 
                   command=self.refresh_ai_insights).pack(pady=5)
        
        # === Achievements Section ===
        ach_frame = ttk.LabelFrame(scrollable_frame, text="🏆 Achievements", padding="15")
        ach_frame.pack(fill=tk.X, pady=10)
        
        self.achievement_widgets = {}
        achievements = self.gamification.get_achievements()
        
        # Create a grid of achievement cards
        for idx, (ach_id, ach_data) in enumerate(achievements.items()):
            row, col = divmod(idx, 2)
            
            card = ttk.Frame(ach_frame, relief=tk.RIDGE, borderwidth=1)
            card.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
            
            # Achievement icon and name
            header = ttk.Frame(card)
            header.pack(fill=tk.X, padx=8, pady=(8, 2))
            
            icon_label = ttk.Label(header, text=ach_data['icon'], font=('Segoe UI', 16))
            icon_label.pack(side=tk.LEFT)
            
            name_label = ttk.Label(header, text=ach_data['name'], 
                                  font=('Segoe UI', 9, 'bold'))
            name_label.pack(side=tk.LEFT, padx=5)
            
            # Description
            desc_label = ttk.Label(card, text=ach_data['description'], 
                                  font=('Segoe UI', 8), foreground='gray')
            desc_label.pack(fill=tk.X, padx=8, pady=(0, 2))
            
            # Progress bar
            progress_frame = ttk.Frame(card)
            progress_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
            
            progress_bar = ttk.Progressbar(progress_frame, mode='determinate', 
                                          length=150, maximum=100)
            progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            progress_label = ttk.Label(progress_frame, text="0%", 
                                      font=('Segoe UI', 8))
            progress_label.pack(side=tk.LEFT, padx=5)
            
            self.achievement_widgets[ach_id] = {
                'card': card,
                'progress_bar': progress_bar,
                'progress_label': progress_label,
                'icon': icon_label,
                'name': name_label
            }
        
        # Configure grid columns
        ach_frame.columnconfigure(0, weight=1)
        ach_frame.columnconfigure(1, weight=1)
        
        # === Daily Challenge Section ===
        challenge_frame = ttk.LabelFrame(scrollable_frame, text="🎯 Daily Challenge", padding="15")
        challenge_frame.pack(fill=tk.X, pady=10)
        
        self.challenge_title = ttk.Label(challenge_frame, text="", 
                                        font=('Segoe UI', 10, 'bold'))
        self.challenge_title.pack(anchor=tk.W)
        
        self.challenge_desc = ttk.Label(challenge_frame, text="", 
                                       font=('Segoe UI', 9), foreground='gray')
        self.challenge_desc.pack(anchor=tk.W, pady=(2, 8))
        
        challenge_progress_frame = ttk.Frame(challenge_frame)
        challenge_progress_frame.pack(fill=tk.X)
        
        self.challenge_progress = ttk.Progressbar(challenge_progress_frame, 
                                                 mode='determinate', length=300)
        self.challenge_progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.challenge_status = ttk.Label(challenge_progress_frame, text="0/0", 
                                         font=('Segoe UI', 9))
        self.challenge_status.pack(side=tk.LEFT, padx=10)
        
        # === Goals Section ===
        goals_frame = ttk.LabelFrame(scrollable_frame, text="🎯 Active Goals", padding="15")
        goals_frame.pack(fill=tk.X, pady=10)
        
        self.goals_listbox = tk.Listbox(goals_frame, height=5, 
                                        font=('Segoe UI', 9))
        self.goals_listbox.pack(fill=tk.X, pady=(0, 10))
        
        goals_btn_frame = ttk.Frame(goals_frame)
        goals_btn_frame.pack(fill=tk.X)
        
        ttk.Button(goals_btn_frame, text="➕ Add Goal", 
                   command=self.add_goal_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(goals_btn_frame, text="✓ Complete Goal", 
                   command=self.complete_selected_goal).pack(side=tk.LEFT, padx=5)
        ttk.Button(goals_btn_frame, text="🗑 Remove Goal", 
                   command=self.remove_selected_goal).pack(side=tk.LEFT, padx=5)
        
        # === Productivity Stats Section ===
        stats_frame = ttk.LabelFrame(scrollable_frame, text="📈 AI-Powered Statistics", padding="15")
        stats_frame.pack(fill=tk.X, pady=10)
        
        self.ai_stats_text = tk.Text(stats_frame, height=5, wrap=tk.WORD,
                                     font=('Courier New', 9), bg='#f0f0f0', relief=tk.FLAT)
        self.ai_stats_text.pack(fill=tk.X)
        
        # === GPU AI Insights Section (if available) ===
        if LOCAL_AI_AVAILABLE:
            gpu_frame = ttk.LabelFrame(scrollable_frame, text="🚀 GPU AI Insights", padding="15")
            gpu_frame.pack(fill=tk.X, pady=10)
            
            # Initialize local AI
            if not hasattr(self, 'local_ai'):
                self.local_ai = LocalAI()  # type: ignore[misc]
            
            # GPU status
            gpu_status = "✅ Running on GPU (CUDA)" if self.local_ai.gpu_available else "💻 Running on CPU"
            ttk.Label(gpu_frame, text=gpu_status, 
                     font=('Segoe UI', 9, 'italic'), foreground='green').pack(anchor=tk.W)
            
            # Distraction triggers display
            ttk.Label(gpu_frame, text="🎯 Common Distraction Triggers:", 
                     font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
            
            self.triggers_text = tk.Text(gpu_frame, height=4, wrap=tk.WORD,
                                        font=('Segoe UI', 9), bg='#fff9e6', relief=tk.FLAT)
            self.triggers_text.pack(fill=tk.X, pady=5)
            
            # Mood analysis
            ttk.Label(gpu_frame, text="😊 Recent Focus Quality:", 
                     font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
            
            self.mood_text = tk.Text(gpu_frame, height=3, wrap=tk.WORD,
                                    font=('Segoe UI', 9), bg='#e6f7ff', relief=tk.FLAT)
            self.mood_text.pack(fill=tk.X, pady=5)
        
        # Initial data refresh
        self.refresh_ai_data()
    
    # === Timer Tab Methods ===
    
    def check_admin_status(self):
        """Check and display admin status"""
        if self.blocker.is_admin():
            self.admin_label.config(text="✅ Admin", foreground='green')
        else:
            self.admin_label.config(text="⚠ Not Admin", foreground='red')
    
    def set_quick_time(self, minutes):
        """Set quick timer values"""
        self.hours_var.set(str(minutes // 60))
        self.minutes_var.set(str(minutes % 60))
    
    def start_session(self):
        """Start a focus session"""
        try:
            hours = int(self.hours_var.get())
            minutes = int(self.minutes_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid time values")
            return
        
        total_minutes = hours * 60 + minutes
        if total_minutes <= 0:
            messagebox.showerror("Error", "Please set a time greater than 0")
            return
        
        # Set mode
        self.blocker.mode = self.mode_var.get()
        
        # Block sites
        success, message = self.blocker.block_sites()
        if not success:
            messagebox.showerror("Error", message)
            return
        
        # Start timer
        with self._timer_lock:
            self.remaining_seconds = total_minutes * 60
            self.timer_running = True
            self.session_start_time = time.time()
        
        # Update UI
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        mode_text = {"normal": "BLOCKING", "strict": "STRICT MODE 🔐", 
                     "pomodoro": "POMODORO 🍅"}.get(self.blocker.mode, "BLOCKING")
        self.status_label.config(text=f"🔒 {mode_text}", foreground='red')
        
        # Start timer thread
        threading.Thread(target=self.run_timer, daemon=True).start()
        
        messagebox.showinfo("Focus Session", f"Blocking {len(self.blocker.get_effective_blacklist())} sites for {hours}h {minutes}m\nStay focused! 💪")
    
    def run_timer(self):
        """Run the countdown timer"""
        while True:
            with self._timer_lock:
                if not self.timer_running:
                    break
                
                current_seconds = self.remaining_seconds
                
                if current_seconds <= 0:
                    # Timer finished - trigger completion
                    self.timer_running = False
                    break
                
                h = current_seconds // 3600
                m = (current_seconds % 3600) // 60
                s = current_seconds % 60
                time_str = f"{h:02d}:{m:02d}:{s:02d}"
                self.remaining_seconds = current_seconds - 1
            
            try:
                self.root.after(0, lambda t=time_str: self.timer_display.config(text=t))
            except tk.TclError:
                break
            
            time.sleep(1)
        
        # Timer loop ended - check if we should complete the session
        # This runs in the background thread, so we need to schedule on main thread
        with self._timer_lock:
            should_complete = (self.remaining_seconds <= 0)
        
        if should_complete:
            try:
                # Schedule session completion on main thread
                # Use after_idle to ensure it runs when main thread is ready
                self.root.after(0, self._trigger_session_complete)
            except tk.TclError:
                pass
    
    def _trigger_session_complete(self):
        """Wrapper to safely trigger session completion from main thread"""
        try:
            # Update display to 00:00:00 first
            self.timer_display.config(text="00:00:00")
            # Then complete the session
            self.session_complete()
        except Exception as e:
            logging.error(f"Error in session completion: {e}", exc_info=True)
    
    def session_complete(self):
        """Handle session completion"""
        elapsed = int(time.time() - self.session_start_time) if self.session_start_time else 0
        self.blocker.update_stats(elapsed, completed=True)
        
        # Use _stop_session_internal to bypass password check and avoid double stats update
        self._stop_session_internal()
        self.timer_display.config(text="00:00:00")
        self.update_stats_display()
        
        # Refresh AI data after completing session
        if AI_AVAILABLE:
            self.refresh_ai_data()
        
        # Show AI-powered session completion dialog
        if LOCAL_AI_AVAILABLE:
            self.show_ai_session_complete(elapsed)
        else:
            messagebox.showinfo("Complete!", "🎉 Focus session complete!\nGreat job staying focused!")
    
    def show_ai_session_complete(self, session_duration):
        """AI-powered session completion with notes and analysis"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Session Complete! 🎉")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Congratulations
        ttk.Label(dialog, text="🎉 Great work!", 
                 font=('Segoe UI', 16, 'bold')).pack(pady=(20, 5))
        
        ttk.Label(dialog, text=f"You focused for {session_duration // 60} minutes", 
                 font=('Segoe UI', 11)).pack(pady=(0, 20))
        
        # Session notes section
        notes_frame = ttk.LabelFrame(dialog, text="📝 How was your focus? (optional)", padding="15")
        notes_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        
        ttk.Label(notes_frame, text="Rate your session or add notes:", 
                 font=('Segoe UI', 9)).pack(anchor=tk.W)
        
        # Quick rating buttons
        rating_frame = ttk.Frame(notes_frame)
        rating_frame.pack(fill=tk.X, pady=10)
        
        selected_rating = tk.StringVar(value="")
        
        ratings = [
            ("😫 Struggled", "Struggled to concentrate, many distractions"),
            ("😐 Okay", "Decent session, some distractions"),
            ("😊 Good", "Good session, stayed mostly focused"),
            ("🌟 Excellent", "Amazing session! In the zone!")
        ]
        
        for emoji, description in ratings:
            btn = ttk.Button(rating_frame, text=emoji, width=10,
                           command=lambda d=description: selected_rating.set(d))
            btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Free-form notes
        ttk.Label(notes_frame, text="Or write your own notes:", 
                 font=('Segoe UI', 9)).pack(anchor=tk.W, pady=(10, 5))
        
        notes_text = tk.Text(notes_frame, height=5, wrap=tk.WORD, font=('Segoe UI', 9))
        notes_text.pack(fill=tk.BOTH, expand=True)
        
        # AI Analysis result display
        analysis_label = ttk.Label(notes_frame, text="", 
                                   font=('Segoe UI', 9, 'italic'),
                                   foreground='#0066cc')
        analysis_label.pack(pady=5)
        
        # AI suggestion display
        suggestion_text = tk.Text(dialog, height=3, wrap=tk.WORD, 
                                 font=('Segoe UI', 9), bg='#f0f0f0', relief=tk.FLAT)
        suggestion_text.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Initialize local AI (method only called when LOCAL_AI_AVAILABLE is True)
        if not hasattr(self, 'local_ai'):
            self.local_ai = LocalAI()  # type: ignore[misc]
        
        # Generate break suggestions
        suggestions = self.local_ai.suggest_break_activity(
            session_duration // 60, 
            None
        )
        suggestion_text.insert('1.0', "💡 Suggested break activities:\n")
        for i, sug in enumerate(suggestions, 1):
            suggestion_text.insert(tk.END, f"  {i}. {sug}\n")
        suggestion_text.config(state=tk.DISABLED)
        
        def analyze_and_save():
            """Analyze notes with AI and save"""
            note = notes_text.get('1.0', tk.END).strip()
            if not note and selected_rating.get():
                note = selected_rating.get()
            
            if note:
                # AI sentiment analysis
                analysis = self.local_ai.analyze_focus_quality(note)
                if analysis:
                    analysis_label.config(text=f"🧠 AI: {analysis['interpretation']}")
                
                # Save note to stats
                self._save_session_note(note, analysis)
            
            dialog.destroy()
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        ttk.Button(btn_frame, text="💾 Save & Continue", 
                  command=analyze_and_save).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text="Skip", 
                  command=dialog.destroy).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
    
    def _save_session_note(self, note, analysis):
        """Save session note with AI analysis to stats"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if 'session_notes' not in self.blocker.stats:
            self.blocker.stats['session_notes'] = {}
        
        if today not in self.blocker.stats['session_notes']:
            self.blocker.stats['session_notes'][today] = []
        
        session_record = {
            'timestamp': datetime.now().isoformat(),
            'note': note,
            'sentiment': analysis['sentiment'] if analysis else 'NEUTRAL',
            'confidence': analysis['confidence'] if analysis else 0.5,
            'interpretation': analysis['interpretation'] if analysis else ''
        }
        
        self.blocker.stats['session_notes'][today].append(session_record)
        self.blocker.save_stats()
        
        logging.info(f"Saved session note: {note[:50]}...")

    
    def _stop_session_internal(self):
        """Internal method to stop session without password check or stats update.
        Used when timer completes naturally."""
        with self._timer_lock:
            self.timer_running = False
            self.remaining_seconds = 0
        
        # Force unblock - bypass password since timer completed naturally
        success, message = self.blocker.unblock_sites(force=True)
        
        # Update UI
        try:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_label.config(text="Ready to focus", foreground='black')
            self.timer_display.config(text="00:00:00")
        except tk.TclError:
            pass
    
    def stop_session(self, show_message=True):
        """Stop the focus session (manual stop by user)"""
        # Check strict mode - only for manual stops
        if self.blocker.mode == BlockMode.STRICT and self.blocker.is_blocking:
            if self.blocker.password_hash:
                password = simpledialog.askstring("Strict Mode", "Enter password to stop:", show='*')
                if not self.blocker.verify_password(password or ""):
                    messagebox.showerror("Error", "Incorrect password!")
                    return
        
        elapsed = int(time.time() - self.session_start_time) if self.session_start_time else 0
        
        with self._timer_lock:
            was_running = self.timer_running
            self.timer_running = False
            self.remaining_seconds = 0
        
        success, message = self.blocker.unblock_sites()
        
        # Only update stats for manual stops where session actually ran
        if was_running and elapsed > 60:  # Only count if > 1 minute
            self.blocker.update_stats(elapsed, completed=False)
        
        # Update UI
        try:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_label.config(text="Ready to focus", foreground='black')
            self.timer_display.config(text="00:00:00")
            self.update_stats_display()
        except tk.TclError:
            pass
        
        if show_message:
            messagebox.showinfo("Stopped", "Session stopped. Sites unblocked.")
    
    def update_stats_display(self):
        """Update statistics displays"""
        stats = self.blocker.get_stats_summary()
        
        # Quick stats on timer tab
        today = datetime.now().strftime("%Y-%m-%d")
        daily = self.blocker.stats.get("daily_stats", {}).get(today, {})
        today_time = daily.get("focus_time", 0) // 60
        today_sessions = daily.get("sessions", 0)
        
        self.quick_stats_label.config(
            text=f"Today: {today_time} min focused • {today_sessions} sessions • 🔥 {stats['current_streak']} day streak"
        )
        
        # Stats tab
        if hasattr(self, 'stat_labels'):
            self.stat_labels['total_hours'].config(text=f"{stats['total_hours']}h")
            self.stat_labels['sessions'].config(text=str(stats['sessions_completed']))
            self.stat_labels['streak'].config(text=f"{stats['current_streak']} days")
            self.stat_labels['best_streak'].config(text=f"{stats['best_streak']} days")
            
            self.update_week_chart()
    
    def update_week_chart(self):
        """Update the weekly chart"""
        self.week_chart.config(state=tk.NORMAL)
        self.week_chart.delete(1.0, tk.END)
        
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        today = datetime.now()
        
        chart_lines = []
        max_time = 1
        
        # Get data for last 7 days
        week_data = []
        for i in range(6, -1, -1):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            daily = self.blocker.stats.get("daily_stats", {}).get(date, {})
            time_min = daily.get("focus_time", 0) // 60
            week_data.append((date, time_min))
            max_time = max(max_time, time_min)
        
        # Create ASCII bar chart
        chart_lines.append("Focus time this week:\n\n")
        
        for date_str, time_min in week_data:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            day_name = days[date.weekday()]
            bar_len = int((time_min / max_time) * 30) if max_time > 0 else 0
            bar = "█" * bar_len + "░" * (30 - bar_len)
            chart_lines.append(f"  {day_name}  {bar} {time_min}m\n")
        
        total_week = sum(t for _, t in week_data)
        chart_lines.append(f"\n  Total this week: {total_week} minutes ({total_week // 60}h {total_week % 60}m)")
        
        self.week_chart.insert(tk.END, "".join(chart_lines))
        self.week_chart.config(state=tk.DISABLED)
    
    # === Sites Tab Methods ===
    
    def update_site_lists(self):
        """Update both site listboxes"""
        self.site_listbox.delete(0, tk.END)
        for site in sorted(self.blocker.blacklist):
            self.site_listbox.insert(tk.END, site)
        
        self.whitelist_listbox.delete(0, tk.END)
        for site in sorted(self.blocker.whitelist):
            self.whitelist_listbox.insert(tk.END, site)
    
    def add_site(self):
        """Add a site to blacklist"""
        site = self.site_entry.get().strip()
        if site and self.blocker.add_site(site):
            self.update_site_lists()
            self.site_entry.delete(0, tk.END)
            self.update_total_sites_count()
        elif site:
            messagebox.showinfo("Info", "Site already in list or invalid")
    
    def remove_site(self):
        """Remove selected sites from blacklist"""
        selection = self.site_listbox.curselection()
        for i in reversed(selection):
            site = self.site_listbox.get(i)
            self.blocker.remove_site(site)
        self.update_site_lists()
        self.update_total_sites_count()
    
    def add_whitelist(self):
        """Add a site to whitelist"""
        site = self.whitelist_entry.get().strip()
        if site and self.blocker.add_to_whitelist(site):
            self.update_site_lists()
            self.whitelist_entry.delete(0, tk.END)
            self.update_total_sites_count()
    
    def remove_whitelist(self):
        """Remove selected site from whitelist"""
        selection = self.whitelist_listbox.curselection()
        if selection:
            site = self.whitelist_listbox.get(selection[0])
            self.blocker.remove_from_whitelist(site)
            self.update_site_lists()
            self.update_total_sites_count()
    
    def import_sites(self):
        """Import sites from file"""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if filepath and self.blocker.import_config(filepath):
            self.update_site_lists()
            self.update_total_sites_count()
            messagebox.showinfo("Success", "Sites imported successfully!")
    
    def export_sites(self):
        """Export sites to file"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")])
        if filepath and self.blocker.export_config(filepath):
            messagebox.showinfo("Success", "Sites exported successfully!")
    
    # === Categories Tab Methods ===
    
    def toggle_category(self, category):
        """Toggle a category on/off"""
        self.blocker.categories_enabled[category] = self.category_vars[category].get()
        self.blocker.save_config()
        self.update_total_sites_count()
    
    def show_category_sites(self, category):
        """Show sites in a category"""
        sites = SITE_CATEGORIES.get(category, [])
        site_list = "\n".join(sorted(set(s.replace("www.", "") for s in sites)))
        messagebox.showinfo(f"{category} Sites", site_list)
    
    def update_total_sites_count(self):
        """Update total blocked sites count"""
        total = len(self.blocker.get_effective_blacklist())
        self.total_sites_label.config(text=f"Total sites to block: {total}")
    
    # === Schedule Tab Methods ===
    
    def update_schedule_list(self):
        """Update the schedule treeview"""
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        for schedule in self.blocker.schedules:
            day_names = ", ".join(days[d] for d in sorted(schedule.get('days', [])))
            time_range = f"{schedule.get('start_time', '')} - {schedule.get('end_time', '')}"
            status = "✅ Active" if schedule.get('enabled', True) else "⏸ Paused"
            
            self.schedule_tree.insert('', tk.END, iid=schedule['id'],
                                      values=(day_names, time_range, status))
    
    def add_schedule(self):
        """Add a new schedule"""
        days = [i for i, var in enumerate(self.day_vars) if var.get()]
        if not days:
            messagebox.showerror("Error", "Select at least one day")
            return
        
        start_time = f"{int(self.start_hour.get()):02d}:{int(self.start_min.get()):02d}"
        end_time = f"{int(self.end_hour.get()):02d}:{int(self.end_min.get()):02d}"
        
        self.blocker.add_schedule(days, start_time, end_time)
        self.update_schedule_list()
    
    def toggle_schedule(self):
        """Toggle selected schedule"""
        selection = self.schedule_tree.selection()
        if selection:
            self.blocker.toggle_schedule(selection[0])
            self.update_schedule_list()
    
    def delete_schedule(self):
        """Delete selected schedule"""
        selection = self.schedule_tree.selection()
        if selection:
            self.blocker.remove_schedule(selection[0])
            self.update_schedule_list()
    
    def check_scheduled_blocking(self):
        """Check if we should be blocking based on schedule"""
        if self.blocker.is_scheduled_block_time() and not self.blocker.is_blocking:
            if messagebox.askyesno("Scheduled Block", 
                                   "You have a blocking schedule active now.\nStart blocking?"):
                self.blocker.mode = BlockMode.SCHEDULED
                self.blocker.block_sites()
                self.status_label.config(text="🔒 SCHEDULED BLOCK", foreground='red')
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)
        
        # Check again in 60 seconds
        self.root.after(60000, self.check_scheduled_blocking)
    
    # === Stats Tab Methods ===
    
    def reset_stats(self):
        """Reset all statistics"""
        if messagebox.askyesno("Reset Stats", "Are you sure you want to reset all statistics?"):
            self.blocker.stats = self.blocker._default_stats()
            self.blocker.save_stats()
            self.update_stats_display()
    
    # === Settings Tab Methods ===
    
    def set_password(self):
        """Set strict mode password"""
        password = simpledialog.askstring("Set Password", "Enter new password:", show='*')
        if password:
            confirm = simpledialog.askstring("Confirm", "Confirm password:", show='*')
            if password == confirm:
                self.blocker.set_password(password)
                self.update_password_status()
                messagebox.showinfo("Success", "Password set!")
            else:
                messagebox.showerror("Error", "Passwords don't match")
    
    def remove_password(self):
        """Remove password"""
        if self.blocker.password_hash:
            password = simpledialog.askstring("Remove Password", "Enter current password:", show='*')
            if self.blocker.verify_password(password or ""):
                self.blocker.set_password(None)
                self.update_password_status()
            else:
                messagebox.showerror("Error", "Incorrect password")
        else:
            messagebox.showinfo("Info", "No password set")
    
    def update_password_status(self):
        """Update password status label"""
        if self.blocker.password_hash:
            self.pwd_status.config(text="🔐 Password is set", foreground='green')
        else:
            self.pwd_status.config(text="No password set", foreground='gray')
    
    def save_pomodoro_settings(self):
        """Save Pomodoro settings"""
        try:
            self.blocker.pomodoro_work = int(self.pomo_vars['pomodoro_work'].get())
            self.blocker.pomodoro_break = int(self.pomo_vars['pomodoro_break'].get())
            self.blocker.pomodoro_long_break = int(self.pomo_vars['pomodoro_long_break'].get())
            self.blocker.save_config()
            messagebox.showinfo("Success", "Pomodoro settings saved!")
        except ValueError:
            messagebox.showerror("Error", "Invalid values")
    
    def emergency_cleanup_action(self):
        """Emergency cleanup - remove all blocks and clean system"""
        confirm = messagebox.askyesno(
            "Emergency Cleanup",
            "This will:\n\n"
            "• Stop any active blocking session\n"
            "• Remove ALL blocked sites from your system\n"
            "• Clear DNS cache\n"
            "• Bypass any password protection\n\n"
            "Use this if websites remain blocked after the app closes.\n\n"
            "Continue?",
            icon='warning'
        )
        
        if confirm:
            # Stop the timer if running
            with self._timer_lock:
                self.timer_running = False
                self.remaining_seconds = 0
            
            # Run the cleanup
            success, message = self.blocker.emergency_cleanup()
            
            # Update UI
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.timer_display.config(text="00:00:00")
            self.status_label.config(text="✅ Ready", foreground='green')
            
            if success:
                messagebox.showinfo("Cleanup Complete", message + "\n\nAll websites should now be accessible.")
            else:
                messagebox.showerror("Cleanup Failed", message)

    # === AI Tab Methods ===
    
    def refresh_ai_data(self):
        """Refresh all AI-powered insights and data"""
        if not AI_AVAILABLE:
            return
        
        self.refresh_ai_insights()
        self.update_achievements()
        self.update_daily_challenge()
        self.update_goals_display()
        self.update_ai_stats()
        
        # Update GPU AI insights if available
        if LOCAL_AI_AVAILABLE and hasattr(self, 'local_ai'):
            self.update_gpu_insights()
    
    def refresh_ai_insights(self):
        """Refresh AI insights and recommendations"""
        if not AI_AVAILABLE:
            return
        
        self.insights_text.delete('1.0', tk.END)
        
        # Get insights and recommendations
        insights = self.analyzer.generate_insights()
        recommendations = self.analyzer.get_recommendations()
        
        if insights:
            self.insights_text.insert(tk.END, "💡 INSIGHTS:\n", 'header')
            for insight in insights:
                self.insights_text.insert(tk.END, f"  • {insight}\n")
            self.insights_text.insert(tk.END, "\n")
        
        if recommendations:
            self.insights_text.insert(tk.END, "🎯 RECOMMENDATIONS:\n", 'header')
            for rec in recommendations:
                self.insights_text.insert(tk.END, f"  • {rec}\n")
        
        if not insights and not recommendations:
            self.insights_text.insert(tk.END, "Complete a few sessions to unlock AI insights!\n", 'info')
        
        # Configure text tags
        self.insights_text.tag_config('header', font=('Segoe UI', 9, 'bold'))
        self.insights_text.tag_config('info', font=('Segoe UI', 9, 'italic'), foreground='gray')
        self.insights_text.config(state=tk.DISABLED)
    
    def update_achievements(self):
        """Update achievement progress bars"""
        if not AI_AVAILABLE:
            return
        
        progress_data = self.gamification.check_achievements()
        
        for ach_id, widgets in self.achievement_widgets.items():
            if ach_id in progress_data:
                progress = progress_data[ach_id]
                current = progress['current']
                target = progress['target']
                unlocked = progress['unlocked']
                
                percentage = min(100, int((current / target) * 100)) if target > 0 else 0
                
                widgets['progress_bar']['value'] = percentage
                widgets['progress_label'].config(text=f"{percentage}%")
                
                if unlocked:
                    widgets['card'].config(relief=tk.RAISED, style='success.TFrame')
                    widgets['icon'].config(font=('Segoe UI', 18))
                    widgets['name'].config(foreground='green')
                else:
                    widgets['card'].config(relief=tk.RIDGE)
                    widgets['icon'].config(font=('Segoe UI', 16))
                    widgets['name'].config(foreground='black')
    
    def update_daily_challenge(self):
        """Update daily challenge display"""
        if not AI_AVAILABLE:
            return
        
        challenge = self.gamification.get_daily_challenge()
        
        self.challenge_title.config(text=challenge['title'])
        self.challenge_desc.config(text=challenge['description'])
        
        current = challenge['progress']['current']
        target = challenge['progress']['target']
        
        self.challenge_progress['maximum'] = target
        self.challenge_progress['value'] = current
        self.challenge_status.config(text=f"{current}/{target}")
    
    def update_goals_display(self):
        """Update active goals listbox"""
        if not AI_AVAILABLE:
            return
        
        self.goals_listbox.delete(0, tk.END)
        
        active_goals = self.goals.get_active_goals()
        
        if not active_goals:
            self.goals_listbox.insert(tk.END, "No active goals. Add one to get started!")
        else:
            for goal in active_goals:
                progress = goal.get('progress', 0)
                target = goal.get('target', 100)
                percentage = int((progress / target) * 100) if target > 0 else 0
                
                display = f"{goal['title']} - {percentage}% ({progress}/{target})"
                self.goals_listbox.insert(tk.END, display)
    
    def update_ai_stats(self):
        """Update AI-powered statistics display"""
        if not AI_AVAILABLE:
            return
        
        self.ai_stats_text.delete('1.0', tk.END)
        
        # Get peak productivity hours
        peak_hours = self.analyzer.get_peak_productivity_hours()
        if peak_hours:
            self.ai_stats_text.insert(tk.END, f"🌟 Peak Hours: {', '.join(peak_hours)}\n")
        
        # Get optimal session length
        optimal = self.analyzer.predict_optimal_session_length()
        if optimal:
            self.ai_stats_text.insert(tk.END, f"⏱  Optimal Session: {optimal} minutes\n")
        
        # Get distraction patterns
        patterns = self.analyzer.get_distraction_patterns()
        if patterns and isinstance(patterns, dict):
            self.ai_stats_text.insert(tk.END, "\n🔍 Distraction Patterns:\n")
            for key, value in list(patterns.items())[:3]:  # Show top 3
                self.ai_stats_text.insert(tk.END, f"   • {key}: {value}\n")
        
        self.ai_stats_text.config(state=tk.DISABLED)
    
    def update_gpu_insights(self):
        """Update GPU AI-powered insights"""
        if not LOCAL_AI_AVAILABLE or not hasattr(self, 'triggers_text'):
            return
        
        # Get session notes from stats
        session_notes = []
        for date, notes_list in self.blocker.stats.get('session_notes', {}).items():
            for note_data in notes_list:
                session_notes.append(note_data.get('note', ''))
        
        # Update distraction triggers
        self.triggers_text.delete('1.0', tk.END)
        if len(session_notes) >= 3:
            triggers = self.local_ai.detect_distraction_triggers(session_notes[-10:])  # Last 10 notes
            if triggers and isinstance(triggers, list) and len(triggers) > 0:
                for trigger in triggers[:3]:  # Top 3
                    if isinstance(trigger, dict):
                        self.triggers_text.insert(tk.END, 
                            f"🎯 {trigger.get('trigger', 'Unknown').upper()} ({trigger.get('frequency', 0)}x)\n")
                        self.triggers_text.insert(tk.END, 
                            f"   💡 {trigger.get('recommendation', 'No recommendation')}\n\n")
                    else:
                        self.triggers_text.insert(tk.END, f"• {trigger}\n")
            else:
                self.triggers_text.insert(tk.END, "No common distraction patterns detected yet.\n")
        else:
            self.triggers_text.insert(tk.END, 
                "Complete 3+ sessions with notes to detect patterns.\n")
        self.triggers_text.config(state=tk.DISABLED)
        
        # Update mood analysis
        self.mood_text.delete('1.0', tk.END)
        if session_notes:
            recent_notes = session_notes[-5:]  # Last 5 sessions
            positive_count = 0
            negative_count = 0
            
            for note in recent_notes:
                result = self.local_ai.analyze_focus_quality(note)
                if result:
                    if result['sentiment'] == 'POSITIVE':
                        positive_count += 1
                    else:
                        negative_count += 1
            
            total = positive_count + negative_count
            if total > 0:
                positive_pct = int((positive_count / total) * 100)
                
                if positive_pct >= 80:
                    mood_msg = f"🌟 Excellent! {positive_pct}% of recent sessions were highly focused"
                elif positive_pct >= 60:
                    mood_msg = f"😊 Good trend: {positive_pct}% positive sessions"
                elif positive_pct >= 40:
                    mood_msg = f"😐 Mixed results: {positive_pct}% positive, {100-positive_pct}% challenging"
                else:
                    mood_msg = f"⚠️ Struggling: Only {positive_pct}% positive sessions\n   💡 Try shorter sessions or different times"
                
                self.mood_text.insert(tk.END, mood_msg)
            else:
                self.mood_text.insert(tk.END, "Add session notes to track focus quality trends")
        else:
            self.mood_text.insert(tk.END, "No session notes yet. Complete a session to start!")
        
        self.mood_text.config(state=tk.DISABLED)
    
    def add_goal_dialog(self):
        """Show dialog to add a new goal"""
        if not AI_AVAILABLE:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Goal")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Goal title
        ttk.Label(dialog, text="Goal Title:", font=('Segoe UI', 10)).pack(pady=(20, 5), padx=20, anchor=tk.W)
        title_entry = ttk.Entry(dialog, width=40, font=('Segoe UI', 10))
        title_entry.pack(padx=20, pady=(0, 10))
        
        # Goal type
        ttk.Label(dialog, text="Goal Type:", font=('Segoe UI', 10)).pack(pady=5, padx=20, anchor=tk.W)
        goal_type = tk.StringVar(value="daily")
        
        type_frame = ttk.Frame(dialog)
        type_frame.pack(padx=20, pady=(0, 10), anchor=tk.W)
        
        ttk.Radiobutton(type_frame, text="Daily", value="daily", variable=goal_type).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="Weekly", value="weekly", variable=goal_type).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="Custom", value="custom", variable=goal_type).pack(side=tk.LEFT, padx=5)
        
        # Target value
        ttk.Label(dialog, text="Target (minutes):", font=('Segoe UI', 10)).pack(pady=5, padx=20, anchor=tk.W)
        target_entry = ttk.Entry(dialog, width=15, font=('Segoe UI', 10))
        target_entry.pack(padx=20, pady=(0, 20), anchor=tk.W)
        target_entry.insert(0, "60")
        
        def save_goal():
            title = title_entry.get().strip()
            try:
                target = int(target_entry.get())
                if title and target > 0:
                    self.goals.add_goal(title, goal_type.get(), target)
                    self.update_goals_display()
                    dialog.destroy()
                else:
                    messagebox.showerror("Invalid Input", "Please enter a valid title and target.")
            except ValueError:
                messagebox.showerror("Invalid Input", "Target must be a number.")
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(padx=20, pady=10)
        
        ttk.Button(btn_frame, text="Save Goal", command=save_goal).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def complete_selected_goal(self):
        """Mark selected goal as completed"""
        if not AI_AVAILABLE:
            return
        
        selection = self.goals_listbox.curselection()
        if selection:
            idx = selection[0]
            active_goals = self.goals.get_active_goals()
            if 0 <= idx < len(active_goals):
                goal = active_goals[idx]
                self.goals.complete_goal(goal['id'])
                self.update_goals_display()
                messagebox.showinfo("Goal Completed", f"🎉 Congratulations on completing '{goal['title']}'!")
    
    def remove_selected_goal(self):
        """Remove selected goal"""
        if not AI_AVAILABLE:
            return
        
        selection = self.goals_listbox.curselection()
        if selection:
            idx = selection[0]
            active_goals = self.goals.get_active_goals()
            if 0 <= idx < len(active_goals):
                goal = active_goals[idx]
                if messagebox.askyesno("Remove Goal", f"Remove goal '{goal['title']}'?"):
                    # Get all goals and remove the selected one
                    all_goals = self.goals.goals
                    all_goals = [g for g in all_goals if g['id'] != goal['id']]
                    self.goals.goals = all_goals
                    self.goals.save_goals()
                    self.update_goals_display()
    
    # === Window Management ===

    
    def on_closing(self):
        """Handle window close"""
        if self.timer_running:
            if messagebox.askyesno("Confirm Exit", "A session is running!\nStop and exit?"):
                self.stop_session(show_message=False)
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    app = FocusBlockerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
