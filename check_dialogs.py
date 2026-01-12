"""Quick syntax check for all dialog files."""
import sys

try:
    print("Checking item_drop_dialog.py...")
    import item_drop_dialog
    print("✓ item_drop_dialog.py OK")
    
    print("Checking level_up_dialog.py...")
    import level_up_dialog
    print("✓ level_up_dialog.py OK")
    
    print("Checking emergency_cleanup_dialog.py...")
    import emergency_cleanup_dialog
    print("✓ emergency_cleanup_dialog.py OK")
    
    print("Checking merge_dialog.py...")
    import merge_dialog
    print("✓ merge_dialog.py OK")
    
    print("Checking session_complete_dialog.py...")
    import session_complete_dialog
    print("✓ session_complete_dialog.py OK")
    
    print("\n✅ All dialog files compile successfully!")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
