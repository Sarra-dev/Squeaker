from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

def get_trending_topics(days=1, limit=5, min_meeps=1):
    """Get trending hashtags using MeepHashtag bridge model"""
    try:
        from .models import Hashtag, Meep, MeepHashtag
        
        cache_key = f'trending_{days}days_{limit}_{min_meeps}'
        
        # Check cache first
        cached = cache.get(cache_key)
        if cached is not None:
            logger.info(f"📦 Returning cached trending topics: {len(cached)} items")
            return cached
        
        # Calculate time threshold
        if days == 1:
            # For "today", use midnight
            time_threshold = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # For multiple days, use timedelta
            time_threshold = timezone.now() - timedelta(days=days)
        
        logger.info(f"🔍 Searching for trending hashtags since: {time_threshold}")
        
        # Debug: Check how many meeps have hashtags in this period
        recent_meeps_with_hashtags = Meep.objects.filter(
            created_at__gte=time_threshold
        ).filter(meephashtag__isnull=False).distinct().count()
        logger.info(f"📝 Meeps with hashtags in period: {recent_meeps_with_hashtags}")
        
        # Get all hashtags used in the period
        trending = list(Hashtag.objects.filter(
            meephashtag__meep__created_at__gte=time_threshold
        ).annotate(
            meep_count=Count('meephashtag', distinct=True)
        ).filter(
            meep_count__gte=min_meeps
        ).order_by('-meep_count')[:limit])
        
        # Debug: If no trending, check all hashtags
        if not trending:
            logger.warning("⚠️ No trending hashtags found!")
            
            # Show ALL hashtags in the system (for debugging)
            all_hashtags = Hashtag.objects.all().annotate(
                meep_count=Count('meephashtag', distinct=True)
            ).order_by('-meep_count')[:10]
            
            logger.info(f"🔍 Top 10 hashtags overall:")
            for h in all_hashtags:
                logger.info(f"   #{h.name} - {h.meep_count} total meeps")
        
        # Cache for 5 minutes
        cache.set(cache_key, trending, 300)
        
        logger.info(f"✅ Returning {len(trending)} trending topics")
        return trending
        
    except Exception as e:
        logger.error(f"❌ Error getting trending: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def get_suggested_profiles(user, limit=3):
    """Get suggested profiles for authenticated users"""
    try:
        from .models import Profile
        
        if not user.is_authenticated:
            return []
        
        suggested = list(Profile.objects.exclude(
            user=user
        ).exclude(
            followed_by=user.profile
        ).annotate(
            follower_count=Count('followed_by')
        ).order_by('-follower_count')[:limit])
        
        logger.info(f"👥 Found {len(suggested)} suggested profiles for {user.username}")
        
        return suggested
        
    except Exception as e:
        logger.error(f"❌ Error getting suggested profiles: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def sidebar_context(request):
    """Context processor for sidebar - Shows TODAY's trending only"""
    try:
        context = {
            'trending_topics': get_trending_topics(days=1, limit=5, min_meeps=1),
            'suggested_profiles': []
        }
        
        if request.user.is_authenticated:
            context['suggested_profiles'] = get_suggested_profiles(request.user, limit=3)
        
        logger.info(f"📊 Sidebar: {len(context['trending_topics'])} trending, {len(context['suggested_profiles'])} suggested")
        
        return context
        
    except Exception as e:
        logger.error(f"❌ Error in sidebar_context: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'trending_topics': [],
            'suggested_profiles': []
        }