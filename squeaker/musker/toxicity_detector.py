"""
Toxicity Detection System for Squeaker
Falls back to keyword detection if AI model unavailable
"""

import logging

logger = logging.getLogger(__name__)

# Simple keyword lists
TOXIC_KEYWORDS = ['hate', 'stupid', 'idiot', 'dumb', 'kill', 'die', 'worst']
BORDERLINE_KEYWORDS = ['annoying', 'bad', 'sucks', 'lame']

def simple_keyword_check(text):
    """Keyword-based toxicity detection"""
    if not text:
        return 0.0
    
    text_lower = text.lower()
    toxic_count = sum(1 for word in TOXIC_KEYWORDS if word in text_lower)
    borderline_count = sum(1 for word in BORDERLINE_KEYWORDS if word in text_lower)
    
    total_words = max(len(text.split()), 1)
    score = (toxic_count * 0.8 + borderline_count * 0.4) / total_words
    return min(score, 1.0)


def analyze_content(text):
    """
    Analyze text for toxicity
    Falls back to keyword detection if AI model unavailable
    """
    if not text or not text.strip():
        return {
            'is_toxic': False,
            'is_borderline': False,
            'toxicity_score': 0.0,
            'label': 'safe',
            'confidence': 1.0
        }
    
    try:
        # Try using AI model if transformers is installed
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            import torch
            import torch.nn.functional as F
            
            MODEL_NAME = "textdetox/xlmr-large-toxicity-classifier-v2"
            
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
            model.eval()
            
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            
            with torch.no_grad():
                logits = model(**inputs).logits
                probs = F.softmax(logits, dim=1)[0].tolist()
            
            toxicity_score = probs[1] if len(probs) > 1 else probs[0]
            logger.info(f"Using AI model (score: {toxicity_score:.3f})")
            
        except Exception as e:
            # Fallback to keyword detection
            logger.warning(f"AI model unavailable, using keywords: {e}")
            toxicity_score = simple_keyword_check(text)
        
        # Determine label
        TOXIC_THRESHOLD = 0.7
        BORDERLINE_THRESHOLD = 0.4
        
        if toxicity_score > TOXIC_THRESHOLD:
            label = 'toxic'
            is_toxic = True
            is_borderline = False
        elif toxicity_score > BORDERLINE_THRESHOLD:
            label = 'borderline'
            is_toxic = False
            is_borderline = True
        else:
            label = 'safe'
            is_toxic = False
            is_borderline = False
        
        return {
            'is_toxic': is_toxic,
            'is_borderline': is_borderline,
            'toxicity_score': toxicity_score,
            'label': label,
            'confidence': 0.8
        }
        
    except Exception as e:
        logger.error(f"Toxicity detection failed: {e}")
        # Always return safe on error
        return {
            'is_toxic': False,
            'is_borderline': False,
            'toxicity_score': 0.0,
            'label': 'safe',
            'confidence': 0.0
        }


def is_content_toxic(text):
    """Check if content is toxic"""
    result = analyze_content(text)
    return result['is_toxic']


def is_content_borderline(text):
    """Check if content is borderline toxic"""
    result = analyze_content(text)
    return result['is_borderline']