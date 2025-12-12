from django.utils import timezone
from django.db.models import Count
from datetime import timedelta, datetime
from django.core.cache import cache

def get_trending_topics(days=1, limit=5, min_meeps=1):
    """Get trending hashtags for today only"""
    try:
        from .models import Hashtag, MeepHashtag
        
        cache_key = f'trending_today_{limit}_{min_meeps}'
        cached = cache.get(cache_key)
        
        if cached is not None:
            return cached
        
        # Get start of today (midnight)
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get trending hashtags from TODAY ONLY
        trending = list(Hashtag.objects.filter(
            meephashtag__meep__created_at__gte=today_start
        ).annotate(
            meep_count=Count('meephashtag', distinct=True)
        ).filter(
            meep_count__gte=min_meeps
        ).order_by('-meep_count')[:limit])
        
        # Cache for 5 minutes only (so it updates frequently)
        cache.set(cache_key, trending, 300)
        
        print(f"✅ Found {len(trending)} trending topics TODAY")
        for t in trending:
            print(f"   #{t.name} - {t.meep_count} meeps today")
        
        return trending
        
    except Exception as e:
        print(f"❌ Error getting trending: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_suggested_profiles(user, limit=3):
    """Get suggested profiles"""
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
        
        return suggested
        
    except Exception as e:
        print(f"❌ Error getting suggested profiles: {e}")
        return []


def sidebar_context(request):
    """Context processor for sidebar - Shows TODAY's trending only"""
    try:
        context = {
            # Show only today's trending (24 hours)
            'trending_topics': get_trending_topics(days=1, limit=5, min_meeps=1),
            'suggested_profiles': []
        }
        
        if request.user.is_authenticated:
            context['suggested_profiles'] = get_suggested_profiles(request.user, limit=3)
        
        return context
        
    except Exception as e:
        print(f"❌ Error in sidebar_context: {e}")
        return {
            'trending_topics': [],
            'suggested_profiles': []
        }