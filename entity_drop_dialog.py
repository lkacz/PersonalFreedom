"""
Entity Drop/Encounter Dialog - Merge-Style Implementation
=========================================================
Replaces the old complex EntityEncounterDialog with a streamlined,
merge-dialog-style workflow using standard message boxes and 
the reliable lottery animation.
"""

from PySide6 import QtWidgets, QtCore
from lottery_animation import LotteryRollDialog
import random
from typing import Callable, Optional

def show_entity_encounter(entity, join_probability: float, 
                          bond_logic_callback: Callable[[str], dict],
                          parent: QtWidgets.QWidget = None) -> None:
    """
    Show the entity encounter flow using standard widgets and lottery animation.
    
    Args:
        entity: The Entity object encountered.
        join_probability: Chance of bonding (0.0-1.0).
        bond_logic_callback: Function that takes entity_id and returns result dict
                             (from gamification.attempt_entitidex_bond).
        parent: Parent widget.
    """
    
    # 1. Show simple encounter options
    rarity_colors = {
        "common": "#7f8c8d", "uncommon": "#27ae60", 
        "rare": "#2980b9", "epic": "#8e44ad", "legendary": "#d35400"
    }
    color = rarity_colors.get(entity.rarity.lower(), "#2c3e50")
    
    msg = QtWidgets.QMessageBox(parent)
    msg.setWindowTitle("✨ Entity Encountered!")
    msg.setText(f"<h3>You encountered: <b><font color='{color}'>{entity.name}</font></b></h3>")
    msg.setInformativeText(
        f"Rarity: {entity.rarity}\n"
        f"Power: {entity.power}\n\n"
        f"Bonding Chance: {int(join_probability * 100)}%"
    )
    
    # Custom buttons
    bond_btn = msg.addButton("Attempt Bond", QtWidgets.QMessageBox.AcceptRole)
    skip_btn = msg.addButton("Skip", QtWidgets.QMessageBox.RejectRole)
    
    msg.exec()
    
    if msg.clickedButton() != bond_btn:
        return
        
    # 2. Perform the ACTUAL logic
    try:
        result = bond_logic_callback(entity.id)
        success = result.get("success", False)
    except Exception as e:
        QtWidgets.QMessageBox.critical(parent, "Error", f"Bonding error: {str(e)}")
        return

    # 3. Calculate visualization roll to match the result
    # If success, we need a roll < probability
    # If fail, we need a roll >= probability
    if success:
        # Generate random success roll (0 to prob)
        roll = random.uniform(0.0, max(0.01, join_probability - 0.01))
    else:
        # Generate random fail roll (prob to 1.0)
        roll = random.uniform(min(0.99, join_probability + 0.01), 1.0)
    
    # 4. Show the dramatic lottery animation
    anim_dialog = LotteryRollDialog(
        target_roll=roll,
        success_threshold=join_probability,
        title=f"🎲 Bonding with {entity.name}...",
        success_text=f"✨ BONDED: {entity.name}! ✨",
        failure_text="💔 Bond Failed",
        animation_duration=4.0, 
        parent=parent
    )
    
    anim_dialog.exec()
    
    # 5. Optional: Show detailed result if needed (e.g. pity bonus info)
    # The LotteryRollDialog just shows success/fail. 
    # If we want to show "Pity Bonus Increased", we might need another msg box
    # or rely on the status bar updates usually done by the caller.
    if not success and result.get("consecutive_fails", 0) > 0:
        fails = result["consecutive_fails"]
        if fails % 3 == 0: # Only annoy user occasionally
             QtWidgets.QMessageBox.information(
                 parent, "Bond Failed", 
                 f"Don't worry! Pity bonus is building up.\nConsecutive fails: {fails}"
             )

