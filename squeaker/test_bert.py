"""
Test script for BERT model integration
Run this from your Django project root directory
"""
import os
import sys
import django

# Add the project directory to the path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'squeaker.settings')
django.setup()

print("=" * 60)
print("BERT Model Test Script")
print("=" * 60)

# Test 1: Check if dependencies are installed
print("\n[1] Checking dependencies...")
try:
    import transformers
    print(f"✓ transformers version: {transformers.__version__}")
except ImportError:
    print("✗ transformers not installed!")
    print("Install with: pip install transformers")
    sys.exit(1)

try:
    import torch
    print(f"✓ torch version: {torch.__version__}")
    print(f"  CUDA available: {torch.cuda.is_available()}")
except ImportError:
    print("✗ torch not installed!")
    print("Install with: pip install torch")
    sys.exit(1)

# Test 2: Import the module
print("\n[2] Importing TextPredictionService...")
try:
    from musker.ml_text_predictor import TextPredictionService
    print("✓ Module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

# Test 3: Initialize the service
print("\n[3] Initializing service (this may take a few minutes on first run)...")
try:
    service = TextPredictionService()
    print("✓ Service initialized successfully!")
except Exception as e:
    print(f"✗ Service initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test autocorrect
print("\n[4] Testing autocorrect functionality...")
test_cases = [
    "I am hppy today",
    "This is a tset",
    "The wether is nice",
    "I lke Python",
]

for test_text in test_cases:
    print(f"\n  Input: '{test_text}'")
    try:
        result = service.autocorrect(test_text)
        print(f"  Output: '{result.get('corrected', '')}'")
        corrections = result.get('corrections', [])
        if corrections:
            print(f"  Corrections: {len(corrections)} found")
            for c in corrections:
                print(f"    - '{c['original']}' → '{c['suggestion']}'")
        else:
            print(f"  Corrections: none")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)