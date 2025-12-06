from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from django.core.cache import cache
from .models import Hashtag, Profile

def get_trending_topics(days=1, limit=5, min_meeps=3):
    """
    Get trending hashtags based on meep count
    """
    cache_key = f'trending_topics_{days}_{limit}_{min_meeps}'
    cached = cache.get(cache_key)
    
    if cached:
        return cached
    
    time_threshold = timezone.now() - timedelta(days=days)
    
    # Get hashtags with at least min_meeps in the time period
    trending = Hashtag.objects.filter(
        meephashtag__meep__created_at__gte=time_threshold
    ).annotate(
        meep_count=Count('meephashtag')
    ).filter(
        meep_count__gte=min_meeps
    ).order_by('-meep_count')[:limit]
    
    # Cache for 5 minutes
    cache.set(cache_key, trending, 300)
    return trending


def get_suggested_profiles(user, limit=3):
    """Get suggested profiles for user to follow"""
    if not user.is_authenticated:
        return []
    
    # Get profiles the user is not following and exclude self
    suggested = Profile.objects.exclude(
        user=user
    ).exclude(
        followed_by=user.profile
    ).annotate(
        follower_count=Count('followed_by')
    ).order_by('-follower_count')[:limit]
    
    return suggested


def sidebar_context(request):
    """
    Context processor to add trending topics and suggested profiles to all templates
    """
    context = {
        'trending_topics': get_trending_topics(days=1, limit=5, min_meeps=3),
    }
    
    # Only add suggested profiles if user is authenticated
    if request.user.is_authenticated:
        context['suggested_profiles'] = get_suggested_profiles(request.user, limit=3)
    
    return context