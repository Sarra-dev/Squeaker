"""
SymSpell Autocorrect - FIXED VERSION that actually corrects text
Install: pip install symspellpy
"""

from symspellpy import SymSpell, Verbosity
import pkg_resources
import re
import os
import logging

logger = logging.getLogger(__name__)

class AutocorrectService:
    def __init__(self):
        """Initialize SymSpell with pretrained dictionary"""
        self.sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
        
        try:
            # Load pretrained English dictionary (comes with symspellpy)
            dictionary_path = pkg_resources.resource_filename(
                "symspellpy", "frequency_dictionary_en_82_765.txt"
            )
            
            if os.path.exists(dictionary_path):
                self.sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)
                logger.info("SymSpell dictionary loaded successfully")
            else:
                logger.warning(f"Dictionary not found at {dictionary_path}")
                
            # Try to load bigram dictionary for better context
            bigram_path = pkg_resources.resource_filename(
                "symspellpy", "frequency_bigramdictionary_en_243_342.txt"
            )
            
            if os.path.exists(bigram_path):
                self.sym_spell.load_bigram_dictionary(bigram_path, term_index=0, count_index=2)
                logger.info("Bigram dictionary loaded successfully")
                
        except Exception as e:
            logger.error(f"Failed to load dictionaries: {e}")
    
    def autocorrect_text(self, text):
        """
        Autocorrect entire text using SymSpell
        Preserves: hashtags, mentions, URLs, emojis
        """
        if not text or not text.strip():
            return text
        
        # Preserve special patterns
        patterns = {
            'url': r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            'hashtag': r'#\w+',
            'mention': r'@\w+',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        }
        
        # Store matches with placeholders
        preserved = {}
        temp_text = text
        counter = 0
        
        for pattern_name, pattern in patterns.items():
            for match in re.finditer(pattern, temp_text):
                placeholder = f"__PRESERVE{counter}__"
                preserved[placeholder] = match.group()
                temp_text = temp_text.replace(match.group(), placeholder, 1)
                counter += 1
        
        # Use lookup_compound for sentence-level correction
        try:
            suggestions = self.sym_spell.lookup_compound(
                temp_text,
                max_edit_distance=2,
                transfer_casing=True,
                ignore_non_words=True
            )
            
            if suggestions and len(suggestions) > 0:
                corrected_text = suggestions[0].term
            else:
                # Fallback: word-by-word correction
                corrected_text = self._correct_word_by_word(temp_text)
                
        except Exception as e:
            logger.error(f"Compound lookup failed: {e}")
            # Fallback to word-by-word
            corrected_text = self._correct_word_by_word(temp_text)
        
        # Restore preserved patterns
        for placeholder, original in preserved.items():
            corrected_text = corrected_text.replace(placeholder, original)
        
        return corrected_text
    
    def _correct_word_by_word(self, text):
        """Fallback: correct each word individually"""
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Skip placeholders
            if word.startswith('__PRESERVE'):
                corrected_words.append(word)
                continue
            
            # Check if word needs correction
            suggestions = self.sym_spell.lookup(
                word,
                Verbosity.CLOSEST,
                max_edit_distance=2,
                include_unknown=False,
                transfer_casing=True
            )
            
            if suggestions and len(suggestions) > 0:
                # Use the best suggestion
                corrected_words.append(suggestions[0].term)
            else:
                # Keep original if no suggestions
                corrected_words.append(word)
        
        return ' '.join(corrected_words)
    
    def get_suggestions(self, word, max_suggestions=5):
        """Get spelling suggestions for a single word"""
        if not word or len(word) < 2:
            return []
        
        try:
            suggestions = self.sym_spell.lookup(
                word,
                Verbosity.TOP,
                max_edit_distance=2,
                include_unknown=False,
                transfer_casing=True
            )
            
            result = []
            for sug in suggestions[:max_suggestions]:
                if sug.term.lower() != word.lower():
                    result.append({
                        'word': sug.term,
                        'distance': sug.distance,
                        'frequency': sug.count
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Suggestion lookup failed: {e}")
            return []
    
    def check_spelling_errors(self, text):
        """
        Check text for spelling errors
        Returns: dict with {misspelled_word: [suggestions]}
        """
        if not text or not text.strip():
            return {}
        
        # Extract only alphabetic words
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        errors = {}
        
        for word in words:
            # Skip very short words and common abbreviations
            if len(word) < 3:
                continue
            
            # Check if word exists in dictionary
            suggestions = self.sym_spell.lookup(
                word,
                Verbosity.CLOSEST,
                max_edit_distance=2,
                include_unknown=False
            )
            
            # If the closest match is different from the word, it's misspelled
            if suggestions and suggestions[0].term.lower() != word.lower():
                # Get top 3 suggestions
                all_suggestions = self.sym_spell.lookup(
                    word,
                    Verbosity.TOP,
                    max_edit_distance=2
                )
                
                errors[word] = [sug.term for sug in all_suggestions[:3]]
        
        return errors


# ==================== SINGLETON PATTERN ====================

_autocorrect_service = None

def get_autocorrect_service():
    """Get or create singleton instance"""
    global _autocorrect_service
    if _autocorrect_service is None:
        _autocorrect_service = AutocorrectService()
    return _autocorrect_service


# ==================== CONVENIENCE FUNCTIONS ====================

def autocorrect_text(text):
    """Autocorrect text using pretrained SymSpell model"""
    service = get_autocorrect_service()
    return service.autocorrect_text(text)


def get_spelling_suggestions(word):
    """Get suggestions for a single word"""
    service = get_autocorrect_service()
    return service.get_suggestions(word)


def check_spelling_errors(text):
    """Check for spelling errors and return suggestions"""
    service = get_autocorrect_service()
    return service.check_spelling_errors(text)


# ==================== TEST FUNCTION ====================

def test_autocorrect():
    """Test the autocorrect functionality"""
    test_cases = [
        "i lke programming",
        "ths is a tst",
        "speling error detectd",
        "I went to the shoping mall yesturday",
        "Follow me @user and check #hashtag for more info"
    ]
    
    print("Testing SymSpell Autocorrect:")
    print("=" * 60)
    
    for text in test_cases:
        corrected = autocorrect_text(text)
        errors = check_spelling_errors(text)
        
        print(f"\nOriginal:  {text}")
        print(f"Corrected: {corrected}")
        if errors:
            print(f"Errors found: {errors}")
        print("-" * 60)


if __name__ == "__main__":
    test_autocorrect()