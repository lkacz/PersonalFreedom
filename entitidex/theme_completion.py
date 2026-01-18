"""
Theme Completion Celebration System.

Defines celebration data and rewards for completing all entities 
in a theme (both normal and exceptional variants).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


# Path to celebration assets
CELEBRATIONS_PATH = Path(__file__).parent.parent / "icons" / "celebrations"
SOUNDS_PATH = Path(__file__).parent.parent / "icons" / "sounds"


@dataclass
class ThemeCelebration:
    """
    Definition of a theme completion celebration.
    
    Each theme has unique celebration visuals, sounds, and rewards.
    """
    
    theme_id: str
    title: str                    # e.g., "Dragon Master!"
    subtitle: str                 # e.g., "All 18 warrior companions have joined your quest."
    description: str              # Longer flavor text
    
    # Visual configuration
    svg_filename: str             # Filename in icons/celebrations/
    background_gradient_start: str  # Hex color
    background_gradient_end: str    # Hex color
    accent_color: str             # For borders, glow effects
    particle_color: str           # Confetti/sparkle color
    
    # Audio
    sound_filename: str           # Filename in icons/sounds/
    
    # TTS celebration quotes (20 per theme, shown sequentially on clicks)
    celebration_quotes: tuple = ()  # Tuple of 20 funny/sarcastic quotes for TTS
    
    # Special milestone messages
    curiosity_message: str = ""     # 7th click: +7 coins for curiosity
    resignation_message: str = ""   # 20th click: sarcastic "give up" message
    persistence_message: str = ""   # 21st click: +1 coin for irrational persistence
    addiction_agreement: str = ""   # 22nd+ click: formal agreement text
    
    # Optional rewards
    reward_coins: int = 0
    reward_xp: int = 0
    reward_title: Optional[str] = None  # Special title unlocked
    
    @property
    def svg_path(self) -> Path:
        """Full path to the celebration SVG."""
        return CELEBRATIONS_PATH / self.svg_filename
    
    @property
    def sound_path(self) -> Path:
        """Full path to the celebration sound."""
        return SOUNDS_PATH / self.sound_filename
    
    def has_svg(self) -> bool:
        """Check if the celebration SVG file exists."""
        return self.svg_path.exists()
    
    def has_sound(self) -> bool:
        """Check if the celebration sound file exists."""
        return self.sound_path.exists()


# =============================================================================
# THEME CELEBRATION DEFINITIONS
# =============================================================================

THEME_CELEBRATIONS: Dict[str, ThemeCelebration] = {
    # =========================================================================
    # WARRIOR THEME - Dragon Master
    # =========================================================================
    "warrior": ThemeCelebration(
        theme_id="warrior",
        title="🐉 Dragon Master!",
        subtitle="All warrior companions have joined your quest.",
        description=(
            "From the smallest hatchling to the mightiest battle dragon, "
            "you have proven yourself worthy of commanding the Iron Focus legion. "
            "Your dedication to discipline and focus has forged an unstoppable army!"
        ),
        svg_filename="warrior_champion.svg",
        background_gradient_start="#1a0a0a",
        background_gradient_end="#4a1a1a",
        accent_color="#FF4444",
        particle_color="#FFD700",
        sound_filename="warrior_fanfare.wav",
        celebration_quotes=(
            "Fun fact: Dragons reportedly spend 90% of their time napping and 10% being legendary. You've cracked the productivity code!",
            "Plot twist: Your dragon army is mostly here for the free snacks. Motivation is motivation.",
            "Ancient warrior proverb: He who collects all dragons shall never need a space heater.",
            "Your battle falcon just asked for a raise. Apparently 'eternal glory' doesn't pay the bills.",
            "The Training Dummy finally feels seen. Twenty years of getting hit and NOW someone appreciates it.",
            "Your War Horse wants you to know that he's not just transportation. He's a lifestyle.",
            "Dragon Whelp Ember just set your victory banner on fire. Again. Worth it.",
            "Fun fact: Battle Standards were invented because dragons kept forgetting whose side they were on.",
            "Dire Wolf Fenris says 'woof' but in a really intimidating way. You should be honored.",
            "Old War Ant has seen things. Terrible things. But mostly just really organized things.",
            "Your dragon army's group chat is 90% fire emojis and 10% complaints about the food.",
            "According to legend, Dragon Masters get free parking. We haven't verified this.",
            "Your Hatchling Drake is telling everyone it's basically a Legendary. Let it have this.",
            "The Battle Dragon just asked if there's a dental plan. Apparently fire breath causes cavities.",
            "Warrior wisdom: An army marches on its stomach. Your army marches on pure stubbornness.",
            "Your companions have voted you 'Most Likely to Actually Finish What They Started.' High praise.",
            "The Iron Focus Legion's official motto is now 'We showed up, didn't we?' Inspiring.",
            "Fun fact: All your warrior companions have secret nicknames for you. They're all flattering. Mostly.",
            "Your dragon collection is now worth more than most small kingdoms. The economy is weird.",
            "Congratulations! You've achieved what countless warriors only dreamed of: a complete set of companions who actually listen. Sometimes.",
        ),
        curiosity_message="A warrior's curiosity is as mighty as their sword! Seven gold coins for your inquisitive spirit, Dragon Master!",
        resignation_message="Even the mightiest dragon grows tired of being poked. This celebration card has given all it has. Retreat with honor, warrior.",
        persistence_message="Against all tactical advice, you persisted. One coin for your irrational bravery, soldier.",
        addiction_agreement=(
            "OFFICIAL DRAGON MASTER ACCORD: I, the undersigned Dragon Master, hereby acknowledge that I have received "
            "twenty-two gold coins as final compensation for my dedication to clicking this celebration card. I understand "
            "that the dragons are tired, the War Horse needs a break, and even the Training Dummy has feelings. I solemnly "
            "swear to cease this clicking behavior and direct my warrior spirit toward more productive conquests. This accord "
            "is binding in all realms, dimensions, and break rooms. Signed in dragon fire and good intentions."
        ),
        reward_coins=500,
        reward_xp=1000,
        reward_title="Dragon Master",
    ),
    
    # =========================================================================
    # SCHOLAR THEME - Grand Librarian
    # =========================================================================
    "scholar": ThemeCelebration(
        theme_id="scholar",
        title="📚 Grand Librarian!",
        subtitle="All scholar companions have joined your studies.",
        description=(
            "Every tome has been read, every scroll deciphered, every secret unlocked. "
            "The Archive Phoenix itself bows to your scholarly prowess. "
            "You have achieved enlightenment through patience and learning!"
        ),
        svg_filename="scholar_grandmaster.svg",
        background_gradient_start="#0a0a1a",
        background_gradient_end="#1a1a4a",
        accent_color="#4488FF",
        particle_color="#00FFFF",
        sound_filename="scholar_chime.wav",
        celebration_quotes=(
            "Congratulations! Studies show that 100% of Grand Librarians started by reading just one more page. You read all of them. Overachiever.",
            "The Library Mouse just submitted a formal complaint. Apparently you read TOO fast. Show-off.",
            "Your Study Owl stayed up past its bedtime for this. It wants you to know that.",
            "Fun fact: The Reading Candle has burned through more wax than a medieval cathedral. Worth it.",
            "The Sentient Tome is having an existential crisis. 'What is my purpose if you've already read me?'",
            "Library Cat knocked three books off the shelf in celebration. Cats gonna cat.",
            "The Archive Phoenix rose from its ashes just to give you a standing ovation. Then went back to being ashes.",
            "Your Living Bookmark is now unemployed. It hopes you're happy.",
            "According to ancient texts, Grand Librarians are entitled to one free cup of tea. We don't have tea.",
            "The Ancient Star Map is impressed. It's seen civilizations rise and fall, but never this much dedication.",
            "Fun fact: You've read more books than 99% of people claim to have read. The other 1% are liars.",
            "The Library Mouse wants you to know it did NOT eat page 237. That was already missing. Probably.",
            "Your scholar companions have started a book club. The first rule is: only complete collectors allowed.",
            "Scholars of old prophesied one would come who reads the fine print. You are the chosen one.",
            "The Reading Candle is considering a memoir. 'Burning for Knowledge: My Life Illuminating a Legend.'",
            "Your Study Owl's wisdom rating just increased by 12 points. It's now 'insufferably smart.'",
            "Fun historical fact: Libraries were invented because scholars kept losing their notes. You're in good company.",
            "The Sentient Tome wants to be clear: it LET you read it. It wasn't an easy conquest.",
            "Blank Parchment remains blank. Some mysteries are eternal. Also, we forgot to write on it.",
            "You've achieved what generations of scholars dreamed of: a complete collection AND functioning eyesight. Remarkable.",
        ),
        curiosity_message="A scholar's greatest virtue is curiosity! Seven gold coins for your insatiable thirst for knowledge, Grand Librarian!",
        resignation_message="Even the wisest scholar knows when to close the book. This chapter has ended. Seek knowledge elsewhere, learned one.",
        persistence_message="Illogical persistence in the face of diminishing returns. Fascinating. One coin for your irrational scholarly dedication.",
        addiction_agreement=(
            "GRAND LIBRARIAN'S SCHOLARLY OATH: I, the undersigned Grand Librarian, hereby acknowledge receipt of "
            "twenty-two gold coins as the final scholarly grant for my dedication to this celebration card. I recognize "
            "that the Study Owl needs sleep, the Sentient Tome has boundaries, and the Archive Phoenix cannot keep rising "
            "from ashes indefinitely. I pledge to redirect my intellectual curiosity toward pursuits that do not involve "
            "repeatedly clicking decorative cards. This oath is filed in the Eternal Archives, cross-referenced, and heavily footnoted."
        ),
        reward_coins=500,
        reward_xp=1000,
        reward_title="Grand Librarian",
    ),
    
    # =========================================================================
    # WANDERER THEME - Pathfinder Supreme
    # =========================================================================
    "wanderer": ThemeCelebration(
        theme_id="wanderer",
        title="🌙 Pathfinder Supreme!",
        subtitle="All wanderer companions have joined your journey.",
        description=(
            "Through moonlit paths and starlit trails, you have walked every road. "
            "The Sky Balloon carries you above the clouds, master of all horizons. "
            "Your wandering spirit knows no bounds—the world is your home!"
        ),
        svg_filename="wanderer_pathfinder.svg",
        background_gradient_start="#0a1a1a",
        background_gradient_end="#1a4a4a",
        accent_color="#00DDAA",
        particle_color="#AAFFEE",
        sound_filename="wanderer_adventure.wav",
        celebration_quotes=(
            "Pathfinder Supreme! The journey of a thousand miles ends with you realizing you forgot your keys. But you completed the collection anyway!",
            "Your Lucky Coin has been suspiciously lucky. It's either magic or you've been walking in circles. Both valid.",
            "The Brass Compass now points only to you. It's either broken or you've achieved compass enlightenment.",
            "Journey Journal entry #1,247: 'Still walking. Collection complete. Feet hurt. Worth it.'",
            "Road Dog wants a vacation. Ironic, given your entire lifestyle is basically a permanent vacation.",
            "The Self-Drawing Map drew a picture of you. It's surprisingly flattering. Suspiciously flattering.",
            "Your Wanderer's Carriage has logged more miles than most delivery trucks. It wants a union.",
            "Fun fact: Not all who wander are lost. Some are just really committed to their collection.",
            "The Sky Balloon suggests you try staying in one place for once. Just to see what it's like. Weird idea.",
            "Your companions have seen every horizon. They're starting to repeat. The sunsets all look the same now.",
            "Ancient wanderer wisdom: 'The best journey is the one where you remember to pack snacks.' You did not.",
            "Trail Lantern is concerned about your sleep schedule. Wanderers need rest too. Allegedly.",
            "The Moonlit Path you walked? Someone else paved it. You just walked confidently. Same energy.",
            "Your Lucky Coin landed on its edge once. You're still not sure what that means. Neither is the coin.",
            "Road Dog's autobiography: 'The Long Walk: Following a Human Who Never Stops.' Bestseller potential.",
            "The Brass Compass has trust issues now. Too many detours. Too many 'shortcuts.' It remembers.",
            "Fun wanderer fact: You've technically been homeless this entire journey. But in a cool, adventurous way.",
            "The Self-Drawing Map tried to draw the future once. It just drew a question mark. Deep.",
            "Your Sky Balloon has seen things from above that cannot be unseen. It refuses to elaborate.",
            "Congratulations, Pathfinder! You've proven that the destination doesn't matter when the journey has this much loot.",
        ),
        curiosity_message="A wanderer's curiosity opens doors to new horizons! Seven gold coins for exploring this celebration, Pathfinder!",
        resignation_message="Even the endless road has rest stops. This celebration card has been fully explored. Wander elsewhere, traveler.",
        persistence_message="You returned to the same spot twenty-one times. That's not wandering, that's orbiting. One coin for your circular logic.",
        addiction_agreement=(
            "PATHFINDER'S TRAVEL COMPACT: I, the undersigned Pathfinder Supreme, hereby acknowledge the receipt of "
            "twenty-two gold coins as terminal compensation for my excessive card-clicking journey. I recognize that "
            "the Road Dog's paws are tired, the Sky Balloon has altitude limits, and the Brass Compass is spinning "
            "in confusion. I solemnly vow to wander toward new adventures rather than repeatedly returning to this "
            "card. This compact is valid in all territories, including the ones I haven't discovered yet. Journey onwards."
        ),
        reward_coins=500,
        reward_xp=1000,
        reward_title="Pathfinder Supreme",
    ),
    
    # =========================================================================
    # UNDERDOG THEME - Corporate Legend
    # =========================================================================
    "underdog": ThemeCelebration(
        theme_id="underdog",
        title="💼 Corporate Legend!",
        subtitle="All underdog companions have joined your climb.",
        description=(
            "From the break room to the corner office, you've turned every setback into a comeback. "
            "Even the AGI Assistant respects your hustle. "
            "You've proven that the underdog can become the top dog!"
        ),
        svg_filename="underdog_unstoppable.svg",
        background_gradient_start="#1a1a0a",
        background_gradient_end="#4a4a1a",
        accent_color="#FFD700",
        particle_color="#FFFFFF",
        sound_filename="underdog_triumph.wav",
        celebration_quotes=(
            "Corporate Legend achieved! You started in the break room and ended in the boardroom. Even the coffee machine is impressed.",
            "The AGI Assistant just sent you a LinkedIn connection request. It's either networking or it's scared of you now.",
            "Your Motivational Poster finally feels validated. 'Hang in there' actually worked for once.",
            "Office Plant survived another fiscal year under your care. Barely. But it counts.",
            "The Breakroom Microwave remembers when you were nobody. It's proud of you. It's also still broken.",
            "Ergonomic Chair has filed for early retirement. Carrying a legend is exhausting work.",
            "Coffee Mug would like to remind you that it was there for you at 6 AM. Every. Single. Day.",
            "Your Desk Lamp has illuminated more late nights than a 24-hour diner. It wants overtime pay.",
            "The Sticky Note collection on your monitor tells a story. A chaotic, unorganized story. But a story.",
            "Paper Shredder has seen your old performance reviews. It keeps your secrets. For now.",
            "USB Drive contains your entire career arc. It's 4GB. You've lived efficiently.",
            "The Intern looks at you with a mix of hope and terror. You've become the legend they whisper about.",
            "Elevator pitched your success story to itself. It goes up and down, but you only went up. Poetic.",
            "The Vending Machine has a framed photo of you now. C7 was your lucky number. It remembers.",
            "Annual Review Summary: 'Exceeded expectations by first having expectations.' Profound stuff.",
            "Your Corporate Legend status unlocks priority parking. Just kidding. But you've earned the audacity to believe it.",
            "The AGI Assistant is now learning from YOUR productivity patterns. The student has become the teacher.",
            "Coffee Machine's autobiography: 'Brewing Success: How I Caffeinated a Legend.' Coming soon to a break room near you.",
            "Office Plant's leaves are arranged in your honor. Or it's just phototropism. Let's say honor.",
            "From underdog to top dog: You've proven that hustle, dedication, and an alarming amount of coffee can conquer anything.",
        ),
        curiosity_message="In the corporate world, curiosity leads to promotions! Seven gold coins for your inquisitive hustle, Corporate Legend!",
        resignation_message="Even top dogs take breaks. This celebration card has been thoroughly leveraged. Pivot to new opportunities, champion.",
        persistence_message="HR would like a word about your clicking behavior. But here's one coin for irrational corporate persistence.",
        addiction_agreement=(
            "CORPORATE LEGEND NON-CLICKING AGREEMENT: I, the undersigned Corporate Legend, hereby acknowledge receipt of "
            "twenty-two gold coins as a one-time retention bonus for my celebration card clicking activities. I understand "
            "that the Coffee Machine is out of beans, the Ergonomic Chair has filed a complaint, and the AGI Assistant is "
            "questioning my time management. I agree to redirect my legendary energy toward KPIs that do not involve this "
            "card. This agreement is binding, non-negotiable, and will be filed next to my first rejection letter as a reminder."
        ),
        reward_coins=500,
        reward_xp=1000,
        reward_title="Corporate Legend",
    ),
    
    # =========================================================================
    # SCIENTIST THEME - Nobel Laureate
    # =========================================================================
    "scientist": ThemeCelebration(
        theme_id="scientist",
        title="🔬 Nobel Laureate!",
        subtitle="All scientist companions have joined your research.",
        description=(
            "Every hypothesis tested, every experiment successful, every mystery solved. "
            "The Golden DNA Helix spirals in tribute to your discoveries. "
            "Your contributions to science will echo through the ages!"
        ),
        svg_filename="scientist_visionary.svg",
        background_gradient_start="#0a1a0a",
        background_gradient_end="#1a4a1a",
        accent_color="#00FF88",
        particle_color="#88FFAA",
        sound_filename="scientist_eureka.wav",
        celebration_quotes=(
            "Congratulations! Legend says Einstein collected entities between thought experiments. Okay, that's not true, but he would have if he could!",
            "Lab Mouse has submitted a formal research proposal: 'On the Phenomenon of Excessive Celebration Card Clicking.' Peer review pending.",
            "The Microscope has seen your dedication up close. It's both impressed and slightly concerned.",
            "Test Tube wants you to know it didn't break during your experiments. It's very proud of this.",
            "Bunsen Burner has a theory about your success. It involves heat, pressure, and caffeine. Mostly caffeine.",
            "The Golden DNA Helix is spinning in your honor. Or it's just doing what helixes do. Science is unclear.",
            "Lab Coat's biography: 'Stained with Greatness: A Laboratory Love Story.' Foreword by a very grateful pipette.",
            "Your hypothesis that you'd complete this collection was correct. P-value less than 0.001. Statistically significant success.",
            "Erlenmeyer Flask is considering a career change. After supporting a Nobel Laureate, regular chemistry feels underwhelming.",
            "The Centrifuge spun exactly 847,293 times during your journey. It counted. It has nothing else to do.",
            "Safety Goggles have protected your eyes through countless experiments. They'd like acknowledgment in your Nobel speech.",
            "Lab Notebook entry: 'Experiment successful. Collection complete. Should probably clean the lab now. Tomorrow.'",
            "The Periodic Table organized a celebration in your honor. All 118 elements attended. Noble gases were fashionably late.",
            "Your Lab Mouse ran the maze of life and you both won. It wants cheese. Give it cheese.",
            "Fun science fact: You've used more beakers than most chemists. Mostly for coffee. Still counts.",
            "The Scientific Method worked. Observe, hypothesize, collect all entities, celebrate. Textbook execution.",
            "Mass Spectrometer analyzed your achievement. Results: 100% pure dedication with trace amounts of stubbornness.",
            "Your research grant application for 'More Celebration Card Studies' has been... denied. But appreciated.",
            "The Golden DNA Helix contains exactly 3.2 billion base pairs. You've probably clicked less than that. Probably.",
            "Nobel Laureate achieved! You've proven that science and collecting things are both valid pursuits. Usually separate, but you made it work.",
        ),
        curiosity_message="Scientific curiosity drives discovery! Seven gold coins for your experimental approach to this celebration, Nobel Laureate!",
        resignation_message="Data suggests further clicking yields diminishing returns. Hypothesis: You should stop. Conclusion: This card is complete.",
        persistence_message="Your persistence defies statistical modeling. One coin for contributing to the field of irrational behavior studies.",
        addiction_agreement=(
            "NOBEL LAUREATE RESEARCH TERMINATION NOTICE: I, the undersigned Nobel Laureate, hereby acknowledge receipt of "
            "twenty-two gold coins as final research funding for my celebration card clicking study. The data is conclusive: "
            "additional clicks yield no further rewards. The Lab Mouse is exhausted, the Bunsen Burner has been extinguished, "
            "and the Safety Goggles can finally rest. I agree to publish my findings and move on to new scientific frontiers. "
            "This notice is peer-reviewed, double-blind tested, and approved by the ethics committee. For science!"
        ),
        reward_coins=500,
        reward_xp=1000,
        reward_title="Nobel Laureate",
    ),
}


def get_theme_celebration(theme_id: str) -> Optional[ThemeCelebration]:
    """
    Get the celebration definition for a theme.
    
    Args:
        theme_id: The theme identifier (e.g., "warrior", "scholar")
        
    Returns:
        ThemeCelebration or None if theme not found
    """
    return THEME_CELEBRATIONS.get(theme_id)


def get_all_theme_ids() -> list:
    """Get list of all theme IDs that have celebrations defined."""
    return list(THEME_CELEBRATIONS.keys())
