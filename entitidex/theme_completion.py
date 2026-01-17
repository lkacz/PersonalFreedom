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
