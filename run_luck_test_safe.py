"""Run luck tests and save output to file."""
import sys
import io
from test_luck_mechanics import run_tests

# Capture output
output_buffer = io.StringIO()
sys.stdout = output_buffer
sys.stderr = output_buffer

try:
    result = run_tests()
    success = result.wasSuccessful()
except Exception as e:
    output_buffer.write(f"\nException occurred: {e}\n")
    success = False

# Restore stdout
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

# Write to file
with open("luck_test_results.txt", "w") as f:
    f.write(output_buffer.getvalue())

# Print to console
print(output_buffer.getvalue())

if success:
    print("\n✅ ALL TESTS PASSED")
    sys.exit(0)
else:
    print("\n❌ SOME TESTS FAILED")
    sys.exit(1)
