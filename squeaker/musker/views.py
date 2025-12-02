from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Profile, Meep, Comment
from .forms import MeepForm, ProfileEditForm , SignUpForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.db.models import Q, Max, Count, Case, When, IntegerField
from .models import Profile, Meep, Comment, Message, Conversation
from django.contrib.auth.models import User

def home(request):
    if request.user.is_authenticated:

        if request.method == "POST":
            form = MeepForm(request.POST, request.FILES)  # <-- IMPORTANT: request.FILES
            if form.is_valid():
                meep = form.save(commit=False)
                meep.user = request.user
                meep.save()
                messages.success(request, ("Your Squeak Has Been Posted"))
                return redirect('home')
        else:
            form = MeepForm()

        meeps = Meep.objects.all().order_by("-created_at")
        return render(request, 'home.html', {"meeps": meeps, "form": form})

    else:
        meeps = Meep.objects.all().order_by("-created_at")
        return render(request, 'home.html', {"meeps": meeps})


@login_required
def profile_list(request):
    if request.user.is_authenticated:
        # Get all profiles except the current user
        profiles = Profile.objects.exclude(user=request.user)
        
        # Handle follow/unfollow POST request
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
            
            # Redirect back to profile_list to prevent form resubmission
            return redirect('profile_list')
        
        return render(request, 'profile_list.html', {"profiles": profiles})
    else:
        return redirect('home')
def profile(request, pk):
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
        elif action == "follow":
            current_user_profile.follows.add(profile)
            messages.success(request, f"You are now following {profile.user.username}")
        current_user_profile.save()
        return redirect('profile', pk=pk)
    
    return render(request, "profile.html", {"profile": profile, "meeps": meeps})

@login_required
def edit_profile(request):
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
        form = SignUpForm()  # create empty form for GET requests

    return render(request, 'register.html', {'form': form})

def logout_user(request):
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('login')

def meep_like(request, pk):
    if request.user.is_authenticated:
        meep = get_object_or_404(Meep, id=pk)
        if meep.likes.filter(id=request.user.id):
            meep.likes.remove(request.user)
        else:
            meep.likes.add(request.user)

        return redirect(request.META.get("HTTP_REFERER"))
    
    else:
        messages.success(request, 'You Must Be Logged In To View That Page ...')
        return redirect('home')
def explore(request):
    meeps = Meep.objects.all().order_by("-created_at")
    return render(request, 'explore.html', {"meeps": meeps})

def meep_show(request, pk):
    meep = get_object_or_404(Meep, id=pk)
    if meep:
        return render(request, 'show_meep.html', {"meep": meep})
    else:
        messages.success(request, 'That Squeak does not exist..')
        return redirect('home')
    
@login_required
def meep_comment(request, meep_id):
    """Handle comment submission for a meep"""
    meep = get_object_or_404(Meep, id=meep_id)
    
    if request.method == 'POST':
        comment_body = request.POST.get('comment_body', '').strip()
        
        if comment_body:
            # Create the comment
            Comment.objects.create(
                meep=meep,
                user=request.user,
                content=comment_body
            )
            messages.success(request, 'Comment posted successfully!')
        else:
            messages.error(request, 'Comment cannot be empty.')
    
    # Redirect back to the meep detail page
    return redirect('meep_show', pk=meep_id)


def meep_show(request, pk):
    """Display a single meep with its comments"""
    meep = get_object_or_404(Meep, id=pk)
    comments = meep.comments.all()  # Get all comments for this meep
    
    context = {
        'meep': meep,
        'comments': comments,
    }
    return render(request, 'show_meep.html', context)

@login_required
def messages_view(request):
    """Display all conversations for the current user"""
    # Get all conversations where user is a participant
    conversations_queryset = Conversation.objects.filter(
        participants=request.user
    ).prefetch_related('participants', 'last_message')
    
    # Process conversations to add other_user attribute
    conversations = []
    for conversation in conversations_queryset:
        other_user = conversation.participants.exclude(id=request.user.id).first()
        
        # Only include conversations that have another user
        if other_user:
            # Calculate unread count
            unread = Message.objects.filter(
                sender=other_user,
                recipient=request.user,
                is_read=False
            ).count()
            
            # Add attributes to conversation
            conversation.get_other_user = other_user
            conversation.unread = unread
            conversations.append(conversation)
    
    return render(request, 'messages.html', {'conversations': conversations})

@login_required
def conversation_detail(request, user_id):
    """Display messages with a specific user"""
    other_user = get_object_or_404(User, id=user_id)
    
    # Don't allow messaging yourself
    if other_user == request.user:
        messages.error(request, "You cannot message yourself!")
        return redirect('messages')
    
    # Get or create conversation
    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).first()
    
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
    
    # Get all messages in this conversation
    messages_list = Message.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user)
    ).order_by('created_at')
    
    # Mark messages as read
    Message.objects.filter(
        sender=other_user,
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    
    context = {
        'conversation': conversation,
        'other_user': other_user,
        'messages': messages_list,
    }
    
    return render(request, 'conversation_detail.html', context)

@login_required
def send_message(request):
    """API endpoint to send a message"""
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
        
        # Don't allow messaging yourself
        if recipient == request.user:
            return JsonResponse({'success': False, 'error': 'You cannot message yourself'})
        
        # Create the message
        message = Message.objects.create(
            sender=request.user,
            recipient=recipient,
            content=content
        )
        
        # Get or create conversation
        conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=recipient
        ).first()
        
        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, recipient)
        
        conversation.last_message = message
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'sender': message.sender.username,
                'created_at': message.created_at.strftime('%I:%M %p'),
            }
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def get_new_messages(request, user_id):
    """API endpoint to fetch new messages (for real-time updates)"""
    last_message_id = request.GET.get('last_message_id', 0)
    
    try:
        other_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'})
    
    # Get new messages since last_message_id
    new_messages = Message.objects.filter(
        Q(sender=other_user, recipient=request.user) |
        Q(sender=request.user, recipient=other_user),
        id__gt=last_message_id
    ).order_by('created_at')
    
    # Mark received messages as read
    Message.objects.filter(
        sender=other_user,
        recipient=request.user,
        is_read=False,
        id__gt=last_message_id
    ).update(is_read=True)
    
    messages_data = [{
        'id': msg.id,
        'content': msg.content,
        'sender': msg.sender.username,
        'sender_id': msg.sender.id,
        'created_at': msg.created_at.strftime('%I:%M %p'),
        'profile_image': msg.sender.profile.profile_image.url if msg.sender.profile.profile_image else None
    } for msg in new_messages]
    
    return JsonResponse({
        'success': True,
        'messages': messages_data
    })

@login_required
def start_conversation(request, user_id):
    """Start a new conversation with a user (redirects to conversation detail)"""
    other_user = get_object_or_404(User, id=user_id)
    
    # Don't allow messaging yourself
    if other_user == request.user:
        messages.error(request, "You cannot message yourself!")
        return redirect('messages')
    
    # Simply redirect to the conversation detail page
    # The conversation will be created there if it doesn't exist
    return redirect('conversation_detail', user_id=user_id)