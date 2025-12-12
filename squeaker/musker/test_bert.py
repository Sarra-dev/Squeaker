"""
Test script for spell correction integration
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
print("Spell Correction Test Script")
print("=" * 60)

# Test 1: Check if dependencies are installed
print("\n[1] Checking dependencies...")
try:
    import textblob
    print(f"✓ textblob version: {textblob.__version__}")
except ImportError:
    print("✗ textblob not installed!")
    print("Install with: pip install textblob")
    print("Then run: python -m textblob.download_corpora")
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
print("\n[3] Initializing service...")
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
    "Helllo wrld",
    "I cant beleive its not butter",
    "Tommorrow will be a grat day",
    "Recieve the packge soon",
]

success_count = 0
for test_text in test_cases:
    print(f"\n  Input:  '{test_text}'")
    try:
        result = service.autocorrect(test_text)
        corrected = result.get('corrected', '')
        print(f"  Output: '{corrected}'")
        
        corrections = result.get('corrections', [])
        if corrections:
            print(f"  ✓ {len(corrections)} correction(s) made:")
            for c in corrections:
                print(f"    '{c['original']}' → '{c['suggestion']}'")
            success_count += 1
        else:
            if corrected != test_text:
                print(f"  ✓ Text was corrected (no detailed changes tracked)")
                success_count += 1
            else:
                print(f"  • No corrections needed")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print(f"Test complete! {success_count}/{len(test_cases)} tests made corrections")
print("=" * 60)