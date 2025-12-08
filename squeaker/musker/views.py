from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta

from .models import Profile, Meep, Comment, Notification,Hashtag, Share, Message, Conversation
from .forms import MeepForm, ProfileEditForm, SignUpForm
from .utils import create_notification


def home(request):
    """Main home view"""
    meeps = Meep.objects.all().order_by("-created_at")
    if request.user.is_authenticated:
        if request.method == "POST":
            print("=" * 50)
            print("POST REQUEST RECEIVED")
            print("POST data:", request.POST)
            print("FILES data:", request.FILES)
            print("=" * 50)
            
            form = MeepForm(request.POST, request.FILES)
            
            print("Form is valid?", form.is_valid())
            if not form.is_valid():
                print("Form errors:", form.errors)
            
            if form.is_valid():
                try:
                    meep = form.save(commit=False)
                    meep.user = request.user
                    print("About to save meep...")
                    meep.save()
                    print("Meep saved successfully! ID:", meep.id)
                    messages.success(request, "Your Squeak Has Been Posted")
                    return redirect('home')
                except Exception as e:
                    print("ERROR SAVING MEEP:", str(e))
                    import traceback
                    traceback.print_exc()
                    messages.error(request, f"Error: {str(e)}")
        else:
            form = MeepForm()
        return render(request, 'home.html', {"meeps": meeps, "form": form})
    return render(request, 'home.html', {"meeps": meeps})
@login_required
def profile_list(request):
    """Profile list view"""
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


def profile(request, pk):
    """Profile view with follow/unfollow"""
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to view profiles")
        return redirect('home')
    
    profile = get_object_or_404(Profile, user_id=pk)
    meeps = Meep.objects.filter(user_id=pk).order_by("-created_at")
    shared_meeps = Meep.objects.filter(shares__user_id=pk).order_by("-created_at")
    
    if request.method == "POST":
        current_user_profile = request.user.profile
        action = request.POST.get('follow')
        if action == "unfollow":
            current_user_profile.follows.remove(profile)
            messages.success(request, f"You unfollowed {profile.user.username}")
            Notification.objects.filter(
                recipient=profile.user,
                sender=request.user,
                notification_type='follow'
            ).delete()
        elif action == "follow":
            current_user_profile.follows.add(profile)
            messages.success(request, f"You are now following {profile.user.username}")
            create_notification(
                recipient=profile.user,
                sender=request.user,
                notification_type='follow'
            )
        current_user_profile.save()
        return redirect('profile', pk=pk)
    
    return render(request, "profile.html", {
        "profile": profile,
        "meeps": meeps,
        "shared_meeps": shared_meeps
    })


@login_required
def edit_profile(request):
    """Edit profile"""
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
        if user:
            login(request, user)
            messages.success(request, 'You have successfully logged in')
            return redirect('home')
        messages.error(request, 'Invalid credentials')
    return render(request, 'login.html')


def register_user(request):
    """Register view"""
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
    """Logout"""
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('login')


def meep_like(request, pk):
    """Like/unlike a meep with notification"""
    if request.user.is_authenticated:
        meep = get_object_or_404(Meep, id=pk)
        if meep.likes.filter(id=request.user.id).exists():
            meep.likes.remove(request.user)
            Notification.objects.filter(
                recipient=meep.user,
                sender=request.user,
                notification_type='like',
                meep=meep
            ).delete()
        else:
            meep.likes.add(request.user)
            create_notification(
                recipient=meep.user,
                sender=request.user,
                notification_type='like',
                meep=meep
            )
        return redirect(request.META.get("HTTP_REFERER"))
    messages.success(request, 'You Must Be Logged In To View That Page ...')
    return redirect('home')


@login_required
def meep_comment(request, meep_id):
    """Post comment"""
    meep = get_object_or_404(Meep, id=meep_id)
    if request.method == 'POST':
        comment_body = request.POST.get('comment_body', '').strip()
        if comment_body:
            comment = Comment.objects.create(
                meep=meep,
                user=request.user,
                content=comment_body
            )
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
    """Show notifications"""
    user_notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('sender', 'meep', 'comment')[:50]
    
    if request.method == 'POST' and request.POST.get('mark_all_read'):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return redirect('notifications')
    
    return render(request, 'notifications.html', {'notifications': user_notifications})


@login_required
def mark_notification_read(request, notification_id):
    """Mark single notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return redirect(notification.get_link())


@login_required
def get_unread_count(request):
    """Return unread notification count"""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})


def explore(request):
    """Explore view with search"""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'meeps')
    meeps, hashtags, people = [], [], []

    if query:
        if search_type == 'meeps':
            meeps = Meep.objects.filter(
                Q(body__icontains=query) | Q(user__username__icontains=query)
            ).select_related('user', 'user__profile').order_by('-created_at')[:50]
        elif search_type == 'hashtags':
            hashtags = Hashtag.objects.filter(
                name__icontains=query
            ).annotate(meep_count=Count('meephashtag')).order_by('-meep_count')[:20]
        elif search_type == 'people':
            people = Profile.objects.filter(
                Q(user__username__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(bio__icontains=query)
            ).select_related('user').order_by('-date_created')[:20]
    else:
        meeps = Meep.objects.all().select_related('user', 'user__profile').order_by('-created_at')[:50]

    # Trending hashtags
    time_threshold = timezone.now() - timedelta(days=7)
    trending_hashtags = Hashtag.objects.filter(
        meephashtag__meep__created_at__gte=time_threshold
    ).annotate(meep_count=Count('meephashtag')).filter(meep_count__gte=2).order_by('-meep_count')[:10]

    return render(request, 'explore.html', {
        'meeps': meeps,
        'hashtags': hashtags,
        'people': people,
        'trending_hashtags': trending_hashtags,
        'query': query,
        'search_type': search_type,
    })


def meep_show(request, pk):
    """Show single meep"""
    meep = get_object_or_404(Meep, id=pk)
    comments = meep.comments.all()
    return render(request, 'show_meep.html', {'meep': meep, 'comments': comments})


@login_required
def messages_view(request):
    """Display conversations"""
    conversations_queryset = Conversation.objects.filter(participants=request.user).prefetch_related('participants', 'last_message')
    conversations = []
    for conversation in conversations_queryset:
        other_user = conversation.participants.exclude(id=request.user.id).first()
        if other_user:
            unread = Message.objects.filter(sender=other_user, recipient=request.user, is_read=False).count()
            conversation.get_other_user = other_user
            conversation.unread = unread
            conversations.append(conversation)
    return render(request, 'messages.html', {'conversations': conversations})


@login_required
def conversation_detail(request, user_id):
    """Conversation with specific user"""
    other_user = get_object_or_404(User, id=user_id)
    if other_user == request.user:
        messages.error(request, "You cannot message yourself!")
        return redirect('messages')

    conversation = Conversation.objects.filter(participants=request.user).filter(participants=other_user).first()
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)

    messages_list = Message.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user)
    ).order_by('created_at')

    Message.objects.filter(sender=other_user, recipient=request.user, is_read=False).update(is_read=True)

    return render(request, 'conversation_detail.html', {
        'conversation': conversation,
        'other_user': other_user,
        'messages': messages_list,
    })


@login_required
def send_message(request):
    """Send a new message via AJAX"""
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        content = request.POST.get('content', '').strip()

        if not content:
            return JsonResponse({'success': False, 'error': 'Message cannot be empty'})
        if not recipient_id:
            return JsonResponse({'success': False, 'error': 'Recipient not specified'})

        try:
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Recipient not found'})
        if recipient == request.user:
            return JsonResponse({'success': False, 'error': 'You cannot message yourself'})

        message = Message.objects.create(sender=request.user, recipient=recipient, content=content)

        conversation = Conversation.objects.filter(participants=request.user).filter(participants=recipient).first()
        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, recipient)

        conversation.last_message = message
        conversation.save()

        return JsonResponse({'success': True, 'message': {
            'id': message.id,
            'content': message.content,
            'sender': message.sender.username,
            'created_at': message.created_at.strftime('%I:%M %p'),
        }})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def get_new_messages(request, user_id):
    """Fetch new messages for AJAX polling"""
    last_message_id = request.GET.get('last_message_id', 0)
    other_user = get_object_or_404(User, id=user_id)

    new_messages = Message.objects.filter(
        Q(sender=other_user, recipient=request.user) |
        Q(sender=request.user, recipient=other_user),
        id__gt=last_message_id
    ).order_by('created_at')

    Message.objects.filter(sender=other_user, recipient=request.user, is_read=False, id__gt=last_message_id).update(is_read=True)

    messages_data = [{
        'id': msg.id,
        'content': msg.content,
        'sender': msg.sender.username,
        'sender_id': msg.sender.id,
        'created_at': msg.created_at.strftime('%I:%M %p'),
        'profile_image': msg.sender.profile.profile_image.url if msg.sender.profile.profile_image else None
    } for msg in new_messages]

    return JsonResponse({'success': True, 'messages': messages_data})


@login_required
def start_conversation(request, user_id):
    """Redirect to conversation with user (creates if not exists)"""
    other_user = get_object_or_404(User, id=user_id)
    if other_user == request.user:
        messages.error(request, "You cannot message yourself!")
        return redirect('messages')
    return redirect('conversation_detail', user_id=user_id)


def hashtag_view(request, hashtag_name):
    """Show posts for a hashtag"""
    try:
        hashtag = Hashtag.objects.get(name=hashtag_name.lower())
        posts = Meep.objects.filter(meephashtag__hashtag=hashtag).order_by('-created_at')
        return render(request, 'hashtag.html', {'hashtag': hashtag, 'posts': posts})
    except Hashtag.DoesNotExist:
        return render(request, 'hashtag.html', {'hashtag': None, 'posts': []})


def meep_share(request, pk):
    """Share/unshare a meep"""
    if request.user.is_authenticated:
        meep = get_object_or_404(Meep, id=pk)
        if meep.shares.filter(user=request.user).exists():
            meep.shares.filter(user=request.user).delete()
            messages.success(request, "You unshared the meep.")
        else:
            Share.objects.create(user=request.user, meep=meep)
            messages.success(request, "Sharing successfully!")
        return redirect(request.META.get("HTTP_REFERER"))
    messages.error(request, 'You must be logged in to share a meep.')
    return redirect('home')
