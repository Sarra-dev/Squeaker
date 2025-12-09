"""
Spell correction and text prediction service using TextBlob.
"""

import logging
from textblob import TextBlob
from textblob import download_corpora

logger = logging.getLogger(__name__)

# Ensure required corpora are downloaded
try:
    download_corpora.download_all()
    logger.info("TextBlob corpora downloaded")
except Exception as e:
    logger.warning(f"Could not download TextBlob corpora: {e}")

# Singleton predictor instance
_predictor_instance = None

def get_predictor():
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = TextPredictionService()
    return _predictor_instance


class TextPredictionService:
    """Text prediction and autocorrection service."""

    def __init__(self):
        logger.info("TextPredictionService initialized")

    def autocorrect(self, sentence: str, max_changes: int = 10):
        if not sentence or not sentence.strip():
            return {"corrected": "", "corrections": []}

        try:
            blob = TextBlob(sentence)
            corrected_text = str(blob.correct())

            corrections = self._find_corrections(sentence, corrected_text)

            if len(corrections) > max_changes:
                corrections = corrections[:max_changes]
                corrected_text = self._apply_corrections(sentence, corrections)

            return {"corrected": corrected_text, "corrections": corrections}

        except Exception as e:
            logger.error(f"Autocorrect failed: {e}", exc_info=True)
            return {"corrected": sentence, "corrections": [], "error": str(e)}

    def _find_corrections(self, original, corrected):
        import re
        corrections = []

        def tokenize_with_pos(text):
            return [(m.group(), m.start(), m.end()) for m in re.finditer(r'\b\w+\b', text)]

        original_words = tokenize_with_pos(original)
        corrected_words = tokenize_with_pos(corrected)

        for i, (orig_word, start, end) in enumerate(original_words):
            if i < len(corrected_words):
                corr_word, _, _ = corrected_words[i]
                if orig_word.lower() != corr_word.lower():
                    corrections.append({
                        "original": orig_word,
                        "suggestion": corr_word,
                        "start": start,
                        "end": end
                    })
        return corrections

    def _apply_corrections(self, original, corrections):
        result = list(original)
        for corr in sorted(corrections, key=lambda x: x['start'], reverse=True):
            result[corr['start']:corr['end']] = list(corr['suggestion'])
        return ''.join(result)
