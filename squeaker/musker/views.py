from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Profile, Meep, Comment
from .forms import MeepForm, ProfileEditForm , SignUpForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

def home(request):
    if request.user.is_authenticated:
        form = MeepForm(request.POST or None)
        if request.method == "POST":
            if form.is_valid():
                meep = form.save(commit=False)
                meep.user = request.user
                meep.save()
                messages.success(request, ("Your Squeak Has Been Posted"))
                return redirect('home')
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