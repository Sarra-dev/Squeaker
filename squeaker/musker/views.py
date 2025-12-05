from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .utils import create_notification
from .models import Notification, Profile, Meep, Comment
from .forms import MeepForm, ProfileEditForm , SignUpForm
from .models import Hashtag, Profile, Meep
from .forms import MeepForm, ProfileEditForm, SignUpForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache  

def home(request):
    """Main home view - context processor handles trending/suggestions"""
    if request.user.is_authenticated:

        if request.method == "POST":
            form = MeepForm(request.POST, request.FILES)  # <-- IMPORTANT: request.FILES
            if form.is_valid():
                meep = form.save(commit=False)
                meep.user = request.user
                meep.save()
                messages.success(request, "Your Squeak Has Been Posted")
                return redirect('home')
        else:
            form = MeepForm()

        
        meeps = Meep.objects.all().order_by("-created_at")
        return render(request, 'home.html', {"meeps": meeps, "form": form})

        return render(request, 'home.html', {
            "meeps": meeps,
            "form": form,
        })
    else:
        meeps = Meep.objects.all().order_by("-created_at")
        return render(request, 'home.html', {
            "meeps": meeps,
        })



@login_required
def profile_list(request):
    """Profile list view - context processor handles sidebar"""
    if request.user.is_authenticated:
        profiles = Profile.objects.exclude(user=request.user)
        
        if request.method == "POST":
            profile_id = request.POST.get('profile_id')
            action = request.POST.get('follow')
            
            if profile_id:
                profile_to_follow = Profile.objects.get(user__id=profile_id)
                
                if action == "unfollow":
                    request.user.profile.follows.remove(profile_to_follow)
                elif action == "follow":
                    request.user.profile.follows.add(profile_to_follow)
                
                request.user.profile.save()
            
            return redirect('profile_list')
        
        return render(request, 'profile_list.html', {"profiles": profiles})
    else:
        return redirect('home')


def profile(request, pk):
    """Profile view with follow notifications"""
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to view profiles")
        return redirect('home')
    
    profile = get_object_or_404(Profile, user_id=pk)
    meeps = Meep.objects.filter(user_id=pk).order_by("-created_at")
    
    if request.method == "POST":
        current_user_profile = request.user.profile
        action = request.POST.get('follow')
        if action == "unfollow":
            current_user_profile.follows.remove(profile)
            messages.success(request, f"You unfollowed {profile.user.username}")
            # Optionally: Delete the follow notification
            Notification.objects.filter(
                recipient=profile.user,
                sender=request.user,
                notification_type='follow'
            ).delete()
        elif action == "follow":
            current_user_profile.follows.add(profile)
            messages.success(request, f"You are now following {profile.user.username}")
            # Create follow notification
            create_notification(
                recipient=profile.user,
                sender=request.user,
                notification_type='follow'
            )
        current_user_profile.save()
        return redirect('profile', pk=pk)
    
    return render(request, "profile.html", {"profile": profile, "meeps": meeps})


@login_required
def edit_profile(request):
    """Edit profile view - context processor handles sidebar"""
    profile = request.user.profile
    
    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('profile', pk=request.user.pk)
    else:
        form = ProfileEditForm(instance=profile)
    
    return render(request, 'editProfile.html', {'form': form, 'profile': profile})


def login_user(request):
    """Login view"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'You have successfully logged in')
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials')
            return render(request, 'login.html')
    return render(request, 'login.html')


def register_user(request):
    """Registration view"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = SignUpForm()

    return render(request, 'register.html', {'form': form})


def logout_user(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('login')


def meep_like(request, pk):
    """Like/unlike a meep with notification"""
    if request.user.is_authenticated:
        meep = get_object_or_404(Meep, id=pk)
        if meep.likes.filter(id=request.user.id):
            meep.likes.remove(request.user)
            # Remove like notification
            Notification.objects.filter(
                recipient=meep.user,
                sender=request.user,
                notification_type='like',
                meep=meep
            ).delete()
        else:
            meep.likes.add(request.user)
            # Create like notification
            create_notification(
                recipient=meep.user,
                sender=request.user,
                notification_type='like',
                meep=meep
            )

        return redirect(request.META.get("HTTP_REFERER"))
    else:
        messages.success(request, 'You Must Be Logged In To View That Page ...')
        return redirect('home')


@login_required
def meep_comment(request, meep_id):
    """Handle comment submission with notification"""
    meep = get_object_or_404(Meep, id=meep_id)
    
    if request.method == 'POST':
        comment_body = request.POST.get('comment_body', '').strip()
        
        if comment_body:
            # Create the comment
            comment = Comment.objects.create(
                meep=meep,
                user=request.user,
                content=comment_body
            )
            # Create comment notification
            create_notification(
                recipient=meep.user,
                sender=request.user,
                notification_type='comment',
                meep=meep,
                comment=comment
            )
            messages.success(request, 'Comment posted successfully!')
        else:
            messages.error(request, 'Comment cannot be empty.')
    
    return redirect('meep_show', pk=meep_id)


@login_required
def notifications(request):
    """Display user notifications"""
    user_notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('sender', 'meep', 'comment')[:50]
    
    # Mark all as read when viewing
    if request.method == 'POST' and request.POST.get('mark_all_read'):
        Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        return redirect('notifications')
    
    context = {
        'notifications': user_notifications,
    }
    return render(request, 'notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    notification = get_object_or_404(
        Notification, 
        id=notification_id, 
        recipient=request.user
    )
    notification.is_read = True
    notification.save()
    return redirect(notification.get_link())


@login_required
def get_unread_count(request):
    """API endpoint to get unread notification count"""
    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    return JsonResponse({'count': count})



def explore(request):
    """
    Explore view with search functionality for meeps, hashtags, and people
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'meeps')  # 'meeps', 'hashtags', or 'people'
    
    meeps = []
    hashtags = []
    people = []
    
    if query:
        # Search meeps
        if search_type == 'meeps':
            meeps = Meep.objects.filter(
                Q(body__icontains=query) | Q(user__username__icontains=query)
            ).select_related('user', 'user__profile').order_by('-created_at')[:50]
        
        # Search hashtags
        elif search_type == 'hashtags':
            hashtags = Hashtag.objects.filter(
                name__icontains=query
            ).annotate(
                meep_count=Count('meephashtag')
            ).order_by('-meep_count')[:20]
        
        # Search people
        elif search_type == 'people':
            people = Profile.objects.filter(
                Q(user__username__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(bio__icontains=query)
            ).select_related('user').order_by('-date_created')[:20]
    else:
        # Show all meeps when no search query
        meeps = Meep.objects.all().select_related('user', 'user__profile').order_by('-created_at')[:50]
    
    # Get trending hashtags for explore page
    time_threshold = timezone.now() - timedelta(days=7)
    trending_hashtags = Hashtag.objects.filter(
        meephashtag__meep__created_at__gte=time_threshold
    ).annotate(
        meep_count=Count('meephashtag')
    ).filter(
        meep_count__gte=2
    ).order_by('-meep_count')[:10]
    
    context = {
        'meeps': meeps,
        'hashtags': hashtags,
        'people': people,
        'trending_hashtags': trending_hashtags,
        'query': query,
        'search_type': search_type,
    }
    
    return render(request, 'explore.html', context)
    


def meep_show(request, pk):
    """Display a single meep with its comments"""
    meep = get_object_or_404(Meep, id=pk)
    comments = meep.comments.all()  # Get all comments for this meep
    
    context = {
        'meep': meep,
        'comments': comments,
    }
    return render(request, 'show_meep.html', context)


def hashtag_view(request, hashtag_name):
    """View posts for a specific hashtag - context processor handles sidebar"""
    try:
        hashtag = Hashtag.objects.get(name=hashtag_name.lower())
        posts = Meep.objects.filter(
            meephashtag__hashtag=hashtag
        ).order_by('-created_at')
        
        context = {
            'hashtag': hashtag,
            'posts': posts,
        }
        return render(request, 'hashtag.html', context)
    except Hashtag.DoesNotExist:
        return render(request, 'hashtag.html', {'hashtag': None, 'posts': []})