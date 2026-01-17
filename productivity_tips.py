"""
Productivity Tips for AGI Assistant Chad entity.

100 normal tips (science-based) for normal Chad variant.
100 advanced tips (witty & insightful) for exceptional Chad variant.
"""

from typing import Tuple
from datetime import datetime
import hashlib

# =============================================================================
# NORMAL TIPS - Science-based productivity tips for knowledge workers
# =============================================================================

NORMAL_TIPS = [
    # 🧠 Cognitive Load, Attention, and Focus (1-20)
    ("Work in **single-task mode**; multitasking reliably reduces accuracy and speed.", "🧠"),
    ("Batch similar tasks to reduce **context-switching costs**.", "🧠"),
    ("Externalize memory (notes, task lists) to free **working memory capacity**.", "🧠"),
    ("Limit open tabs; visual clutter increases cognitive load.", "🧠"),
    ("Use clear task definitions ('write abstract' vs 'work on paper').", "🧠"),
    ("Start sessions with the most cognitively demanding task.", "🧠"),
    ("Apply the **Zeigarnik effect**: write a small next step before stopping.", "🧠"),
    ("Avoid email and messaging during deep work blocks.", "🧠"),
    ("Use time-boxed focus sessions (e.g., 25–90 minutes).", "🧠"),
    ("Schedule shallow work for low-energy periods.", "🧠"),
    ("Reduce decision fatigue by standardizing routines.", "🧠"),
    ("Keep task lists short and prioritized.", "🧠"),
    ("Use checklists for recurring tasks.", "🧠"),
    ("Avoid 'open-ended' work sessions.", "🧠"),
    ("Separate planning time from execution time.", "🧠"),
    ("Minimize notifications; intermittent interruptions impair focus.", "🧠"),
    ("Silence phone and desktop alerts during focus periods.", "🧠"),
    ("Read difficult material in print when possible (better comprehension).", "🧠"),
    ("Use outlines to structure thinking before writing.", "🧠"),
    ("End workdays with a brief review to reduce mental rumination.", "🧠"),
    
    # ⏱️ Time, Energy, and Circadian Biology (21-40)
    ("Align demanding work with your **circadian peak**.", "⏱️"),
    ("Maintain consistent sleep and wake times.", "⏱️"),
    ("Avoid sleep deprivation; it degrades executive function.", "⏱️"),
    ("Use short breaks to prevent vigilance decline.", "⏱️"),
    ("Take breaks **before** fatigue becomes noticeable.", "⏱️"),
    ("Use longer breaks after prolonged cognitive effort.", "⏱️"),
    ("Avoid heavy meals before focus work.", "⏱️"),
    ("Stay hydrated; mild dehydration impairs cognition.", "⏱️"),
    ("Use light exposure (daylight) to support alertness.", "⏱️"),
    ("Avoid bright screens late at night.", "⏱️"),
    ("Schedule meetings when cognitive demand is lower.", "⏱️"),
    ("Limit caffeine to earlier in the day.", "⏱️"),
    ("Use caffeine strategically, not continuously.", "⏱️"),
    ("Avoid 'revenge bedtime procrastination.'", "⏱️"),
    ("Respect weekly recovery cycles; rest days matter.", "⏱️"),
    ("Do not overwork consecutive days without recovery.", "⏱️"),
    ("Track energy, not just time.", "⏱️"),
    ("Use deadlines to constrain Parkinson's Law.", "⏱️"),
    ("Avoid chronic time pressure; it reduces creativity.", "⏱️"),
    ("Protect at least one uninterrupted block per day.", "⏱️"),
    
    # 🪑 Ergonomics, Body, and Physical Health (41-60)
    ("Adjust monitor height to eye level.", "🪑"),
    ("Keep wrists neutral while typing.", "🪑"),
    ("Use an external keyboard and mouse for laptops.", "🪑"),
    ("Sit with feet flat and back supported.", "🪑"),
    ("Avoid static postures; posture variation matters more than 'perfect posture.'", "🪑"),
    ("Stand up at least once every 30–60 minutes.", "🪑"),
    ("Use sit-stand desks intermittently, not continuously.", "🪑"),
    ("Stretch hands and forearms to reduce strain.", "🪑"),
    ("Use keyboard shortcuts to reduce repetitive movements.", "🪑"),
    ("Optimize chair height to reduce shoulder tension.", "🪑"),
    ("Reduce glare to prevent eye strain.", "🪑"),
    ("Follow the 20-20-20 rule for vision.", "🪑"),
    ("Use adequate font sizes.", "🪑"),
    ("Keep frequently used items within easy reach.", "🪑"),
    ("Avoid working from bed or couch.", "🪑"),
    ("Maintain room temperature within thermal comfort range.", "🪑"),
    ("Use noise reduction for auditory comfort.", "🪑"),
    ("Address pain early; discomfort reduces cognitive performance.", "🪑"),
    ("Incorporate light physical activity during the day.", "🪑"),
    ("Use breathing exercises to reduce physiological stress.", "🪑"),
    
    # 🧩 Learning, Memory, and Skill Development (61-75)
    ("Use spaced repetition for knowledge retention.", "🧩"),
    ("Prefer active recall over rereading.", "🧩"),
    ("Explain concepts aloud to reveal gaps.", "🧩"),
    ("Interleave related skills to improve transfer.", "🧩"),
    ("Practice at the edge of competence.", "🧩"),
    ("Use deliberate practice, not mindless repetition.", "🧩"),
    ("Sleep consolidates learning—do not sacrifice it.", "🧩"),
    ("Take notes by synthesizing, not transcribing.", "🧩"),
    ("Periodically review old material.", "🧩"),
    ("Teach others to reinforce understanding.", "🧩"),
    ("Use diagrams and visual representations.", "🧩"),
    ("Reduce passive consumption of information.", "🧩"),
    ("Test yourself before checking answers.", "🧩"),
    ("Avoid illusion of competence from familiarity.", "🧩"),
    ("Use retrieval practice in short bursts.", "🧩"),
    
    # 🧪 Environment, Tools, and Systems (76-90)
    ("Design your workspace to cue productive behavior.", "🧪"),
    ("Separate work and leisure environments when possible.", "🧪"),
    ("Use consistent file-naming conventions.", "🧪"),
    ("Automate repetitive digital tasks.", "🧪"),
    ("Use version control for important documents.", "🧪"),
    ("Reduce friction for starting important tasks.", "🧪"),
    ("Increase friction for distractions.", "🧪"),
    ("Use task managers that match cognitive style.", "🧪"),
    ("Avoid over-engineering productivity systems.", "🧪"),
    ("Periodically prune tools and workflows.", "🧪"),
    ("Keep a clean digital desktop.", "🧪"),
    ("Back up work automatically.", "🧪"),
    ("Use templates for recurring outputs.", "🧪"),
    ("Track progress visually.", "🧪"),
    ("Review systems monthly for effectiveness.", "🧪"),
    
    # 🧘 Psychological Well-Being and Sustainability (91-100)
    ("Set realistic daily goals.", "🧘"),
    ("Avoid perfectionism; it delays completion.", "🧘"),
    ("Separate self-worth from productivity.", "🧘"),
    ("Use self-compassion to recover from setbacks.", "🧘"),
    ("Limit social comparison.", "🧘"),
    ("Acknowledge progress, not just outcomes.", "🧘"),
    ("Use brief mindfulness practices to reset attention.", "🧘"),
    ("Address chronic stress proactively.", "🧘"),
    ("Maintain social connection; isolation impairs performance.", "🧘"),
    ("Optimize for **sustainable productivity**, not maximal output.", "🧘"),
]

# =============================================================================
# ADVANCED TIPS - Witty & insightful tips for exceptional Chad variant
# =============================================================================

ADVANCED_TIPS = [
    # Core Attention (1-10)
    ("**Do one thing at a time.**\nMultitasking is just your brain screaming 'I can do this!' while dropping everything.", "🎯"),
    ("**Notifications cost attention even when ignored.**\nYour brain hears every ping like a dog hearing a treat bag.", "🔔"),
    ("**Decision fatigue is real—automate choices.**\nIf you spend 20 minutes choosing a font, the font has already won.", "⚙️"),
    ("**Brain fog = low sleep or glucose.**\nCoffee is a bandage, not a blood transfusion.", "☁️"),
    ("**Working memory holds ~4 items.**\nThat's why your brain is not a whiteboard—it's a Post-it.", "📝"),
    ("**Don't start the day with email.**\nThat's letting strangers schedule your neurons.", "📧"),
    ("**Deep focus starts late—don't quit early.**\nStopping after 5 minutes is like leaving the gym during the warm-up.", "💪"),
    ("**Real breaks restore attention.**\nScrolling is not rest; it's cardio for your thumbs.", "📱"),
    ("**Novelty feels productive but isn't.**\nRearranging icons is not 'system optimization.'", "✨"),
    ("**Define the next physical action.**\n'Work on project' is not a task; it's a cry for help.", "✅"),
    
    # Focus, Distraction & Environment (11-20)
    ("**Phone nearby reduces cognition.**\nEven face-down, it whispers: 'What if I'm famous now?'", "📵"),
    ("**Too many tabs = mental open loops.**\nYour browser has more unresolved issues than a soap opera.", "🗂️"),
    ("**Language noise disrupts thinking.**\nYour brain tries to understand the podcast instead of your job.", "🔊"),
    ("**Lyrics hijack language processing.**\nYou can't write code while emotionally processing a breakup song.", "🎵"),
    ("**Windows improve focus and mood.**\nSunlight: the original productivity app.", "☀️"),
    ("**Visual clutter increases cognitive load.**\nYour brain keeps asking, 'Why is THAT still here?'", "🗑️"),
    ("**Dark mode ≠ automatic productivity.**\nYou're not Batman; context still matters.", "🦇"),
    ("**Predictable desks beat tidy desks.**\nChaos is fine if your brain has a map.", "🗺️"),
    ("**Same workspace trains focus faster.**\nYour brain goes: 'Ah yes, the thinking cave.'", "🏠"),
    ("**Changing locations boosts creativity, hurts focus.**\nCoffee shops are great—if your goal is ideas, not completion.", "☕"),
    
    # Time, Planning & Work Structure (21-30)
    ("**Time blocking reduces decisions.**\nIt tells your brain, 'Relax, someone already decided.'", "📅"),
    ("**Plan tomorrow today.**\nOtherwise your brain plans it at 3 a.m.", "🌙"),
    ("**You overestimate daily capacity.**\nYou plan like a superhero but wake up as a human.", "🦸"),
    ("**Deadlines exploit Parkinson's Law.**\nWork expands until fear intervenes.", "⏰"),
    ("**Fake deadlines need consequences.**\nYour brain knows when you're bluffing.", "🎭"),
    ("**Break tasks into tiny pieces.**\nIf it feels silly, it's the right size.", "🧩"),
    ("**Hard tasks first avoid willpower drain.**\nEat the frog before it starts eating you.", "🐸"),
    ("**Or start tiny to overcome resistance.**\nYou're not lazy—you're stuck in 'start mode.'", "🚀"),
    ("**Long to-do lists increase anxiety.**\nCongratulations, you've invented a stress generator.", "📋"),
    ("**<2 minutes? Do it now.**\nOtherwise it joins the graveyard of 'small but immortal tasks.'", "⚡"),
    
    # Body, Movement & Ergonomics (31-40)
    ("**Stillness reduces cognition.**\nYour brain likes movement; it's not a houseplant.", "🌱"),
    ("**Micro-movement beats heroic workouts.**\nFive squats now beat a gym fantasy later.", "🏋️"),
    ("**Monitor at eye level prevents strain.**\nYour neck is not designed for permanent disappointment.", "🖥️"),
    ("**Best posture is the next posture.**\nStatic perfection is a myth invented by chairs.", "💺"),
    ("**Discomfort drains attention.**\nPain is a very loud background app.", "🔊"),
    ("**Cold hands reduce typing accuracy.**\nYour fingers are protesting in Morse code.", "🥶"),
    ("**Standing desks help—sometimes.**\nStanding all day is just sitting with ambition.", "🧍"),
    ("**Slouching lowers mood physiologically.**\nYour body votes on your emotions.", "😞"),
    ("**Stretching beats scrolling for alertness.**\nOne feeds blood; the other feeds doom.", "🙆"),
    ("**Body and brain are one system.**\nSorry—you can't outsource biology.", "🧬"),
    
    # Sleep, Energy & Recovery (41-50)
    ("**Sleep loss > alcohol for impairment.**\nYou're sober but cognitively drunk.", "😴"),
    ("**Consistent sleep timing matters.**\nYour brain loves routines more than surprises.", "🛏️"),
    ("**Blue light delays melatonin.**\nYour phone convinces your brain it's noon forever.", "📱"),
    ("**Late caffeine sabotages sleep.**\nFeeling fine now, awake at 3 a.m. later.", "☕"),
    ("**Short naps boost performance.**\nPower naps are software updates, not shutdowns.", "💤"),
    ("**Fatigue feels like boredom.**\nYou're not uninspired—you're tired.", "😩"),
    ("**All-nighters destroy learning.**\nYou studied bravely and remembered nothing.", "📚"),
    ("**Sleep is computation time.**\nYour brain saves files while you drool.", "💾"),
    ("**Recovery increases output.**\nEven machines overheat.", "🔥"),
    ("**Rest is strategy, not laziness.**\nRecharge beats heroic burnout.", "🔋"),
    
    # Motivation, Emotion & Psychology (51-60)
    ("**Motivation follows action.**\nWaiting to feel ready is waiting forever.", "🎬"),
    ("**Dopamine spikes reduce persistence.**\nSocial media is dessert before dinner.", "🍰"),
    ("**Fear boosts focus briefly, burns later.**\nAdrenaline is a loan shark.", "😱"),
    ("**Tracking progress increases persistence.**\nTiny wins are brain candy.", "🍬"),
    ("**Self-criticism reduces flexibility.**\nYour brain works better without a bully.", "🤔"),
    ("**Curiosity outperforms discipline.**\nInterest lasts longer than grit.", "🔍"),
    ("**Positive mood improves cognition.**\nHappy brains solve harder puzzles.", "😊"),
    ("**Burnout is nervous system overload.**\nYou didn't fail—the system tripped.", "⚡"),
    ("**Meaning reduces perceived effort.**\nPurpose is lighter than force.", "💫"),
    ("**Momentum beats passion.**\nPassion naps; momentum shows up.", "🏃"),
    
    # Digital Hygiene & Tools (61-70)
    ("**Software friction accumulates.**\nDeath by a thousand tiny dialogs.", "💀"),
    ("**Automate before optimizing.**\nDon't polish what shouldn't exist.", "🤖"),
    ("**Shortcuts save hours.**\nYour mouse walks so your keyboard can teleport.", "⌨️"),
    ("**Pull notifications, don't accept pushes.**\nYou choose interruptions—or they choose you.", "🔕"),
    ("**Batch email reduces stress hormones.**\nInbox zero is cortisol zero-ish.", "📬"),
    ("**Good file names help future you.**\nTime travel, but polite.", "📁"),
    ("**Version control reduces fear.**\nUndo anxiety is productivity.", "↩️"),
    ("**Tool switching taxes attention.**\nYour brain pays import fees.", "💸"),
    ("**New tools feel productive early.**\nThe honeymoon phase lies.", "💍"),
    ("**Trust beats novelty.**\nFamiliar tools don't steal focus.", "🔧"),
    
    # Learning, Memory & Thinking (71-80)
    ("**Writing clarifies thought.**\nConfusion evaporates on paper.", "✍️"),
    ("**Teaching improves retention.**\nExplaining reveals what you don't know.", "👨‍🏫"),
    ("**Spaced repetition beats cramming.**\nBrains hate last-minute heroics.", "📆"),
    ("**Errors strengthen learning.**\nMistakes are protein for memory.", "❌"),
    ("**Handwriting improves understanding.**\nSlow hands, deep brain.", "🖊️"),
    ("**Highlighting feels productive.**\nYour book is now neon—but you're not smarter.", "🖍️"),
    ("**Sleep improves memory more than study.**\nDreams do the filing.", "💭"),
    ("**Rephrase ideas to expose gaps.**\nIf you can't explain it, it's hiding.", "🔎"),
    ("**Understanding beats memorization.**\nPressure reveals comprehension fraud.", "🎭"),
    ("**Confusion signals learning.**\nGrowth feels dumb at first.", "🤯"),
    
    # Social, Work Culture & Boundaries (81-90)
    ("**People switching is costly.**\nYour brain reloads personalities.", "👥"),
    ("**Meetings without agendas raise cortisol.**\nFear-based brainstorming.", "📊"),
    ("**Fewer collaborators improve quality.**\nToo many chefs cook email.", "👨‍🍳"),
    ("**Clear expectations reduce anxiety.**\nAmbiguity is a stress multiplier.", "❓"),
    ("**Saying no protects focus.**\nEvery yes is a future apology.", "🙅"),
    ("**Availability ≠ productivity.**\nBusy is not effective.", "📞"),
    ("**Async communication helps deep work.**\nYour brain likes uninterrupted sentences.", "💬"),
    ("**Interruptions reset mental models.**\nYou were building a castle; now you're re-finding bricks.", "🧱"),
    ("**Psychological safety boosts cognition.**\nBrains don't think well under threat.", "🛡️"),
    ("**Work expands to fill attention.**\nGive it less, it shrinks.", "📏"),
    
    # Meta-Productivity (91-100)
    ("**Optimizing productivity can be procrastination.**\nYou researched productivity instead of producing.", "🔄"),
    ("**Systems beat goals.**\nGoals point; systems walk.", "🗺️"),
    ("**Measure what matters.**\nOtherwise you optimize nonsense efficiently.", "📐"),
    ("**Repetition creates automation.**\nHabits are brain macros.", "🔁"),
    ("**Energy beats time.**\nEight tired hours < two sharp ones.", "⚡"),
    ("**Boredom precedes insight.**\nDon't interrupt the simmer.", "💡"),
    ("**Perfectionism delays completion.**\nPerfect drafts never ship.", "📦"),
    ("**Done beats perfect.**\nFinished things work.", "✔️"),
    ("**Sustainable productivity looks boring.**\nNo drama, just output.", "😐"),
    ("**If productivity advice stresses you, it failed.**\nThe goal was working—not suffering.", "🎯"),
]


def get_tip_count(is_exceptional: bool = False) -> int:
    """Get the total number of tips available."""
    return len(ADVANCED_TIPS) if is_exceptional else len(NORMAL_TIPS)


def get_tip_by_index(index: int, is_exceptional: bool = False) -> Tuple[str, str]:
    """
    Get a specific tip by index.
    
    Returns:
        tuple: (tip_text, category_emoji)
    """
    tips_list = ADVANCED_TIPS if is_exceptional else NORMAL_TIPS
    index = index % len(tips_list)
    return tips_list[index]
