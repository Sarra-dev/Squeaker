from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

from django.shortcuts import get_object_or_404

from django.http import HttpResponseBadRequest, HttpResponse
from django.urls import reverse_lazy
from django import http

from django.db.models import Count

from .models import Profile, Meep
from .forms import MeepForm, SignUpForm, UpdateUserForm, ProfilePicForm


def home(request):
    if request.user.is_authenticated:
        form = MeepForm(request.POST or None)
        if request.method == "POST":
            if form.is_valid():
                meep = form.save(commit=False)
                meep.user = request.user
                meep.save()
                messages.success(request, "Your Meep has been posted!")
                return redirect("home")

        meeps = Meep.objects.all().order_by("-created_at")
        username = request.user.get_username()
        # print(username)

        context = {"meeps": meeps, "form": form}
        return render(request, "home.html", context)
    else:
        meeps = Meep.objects.all().order_by("-created_at")
        context = {"meeps": meeps}
        return render(request, "home.html", context)


# **********************
# ****** PROFILE *******
# **********************


def profile(request, pk):
    if request.user.is_authenticated:
        my_profile = Profile.objects.get(user_id=pk)
        meeps = Meep.objects.filter(user_id=pk).order_by("-created_at")
        current_user_profile = request.user.profile

        if request.method == "POST":
            action = request.POST.get("follow-btn")
            print(action)
            if action == "unfollow":
                current_user_profile.follows.remove(my_profile)
            elif action == "follow":
                current_user_profile.follows.add(my_profile)
            else:
                # If the action is neither follow nor unfollow, return a bad request response
                return HttpResponseBadRequest("Invalid follow action")
            current_user_profile.save()

    context = {"my_profile": my_profile, "meeps": meeps}
    return render(request, "profile.html", context)


def profile_list(request):
    profiles = Profile.objects.all()
    print(profiles)
    context = {"profiles": profiles}
    return render(request, "profile_list.html", context)


def profile_list(request):
    if request.user.is_authenticated:
        print(f" USER: {request.user}")
        profiles = Profile.objects.exclude(user=request.user)
        profiles = profiles.annotate(num_images=Count("profile_image")).order_by(
            "-num_images"
        )

        print(f"PROFILES: {profiles}")
        context = {"profiles": profiles}
        return render(request, "profile_list.html", context)
    else:
        profiles = Profile.objects.all()
        context = {"profiles": profiles}
        return render(request, "profile_list.html", context)


# **********************
# ****** FOLLOWERS *****
# **********************


def followers_list(request, pk):
    if request.user.is_authenticated:
        if request.user.id == pk:
            my_profile = Profile.objects.get(user_id=pk)
            context = {"my_profile": my_profile}
            return render(request, "followers_list.html", context=context)
        else:
            messages.success(request, "You can only see your followers, bitch!")
            return redirect("home")
    else:
        messages.success(request, "You must be logged in to view this page")
        return redirect("home")


def follows_list(request, pk):
    if request.user.is_authenticated:
        if request.user.id == pk:
            my_profile = Profile.objects.get(user_id=pk)
            context = {"my_profile": my_profile}
            # print(my_profile)
            # print(my_profile.follows.all())
            return render(request, "follows_list.html", context=context)
        else:
            messages.success(request, "You can only see your followers, bitch!")
            return redirect("home")
    else:
        messages.success(request, "You must be logged in to view this page")
        return redirect("home")


def unfollow(request, pk):
    if request.user.is_authenticated:
        profile_to_unfollow = Profile.objects.get(user_id=pk)
        request.user.profile.follows.remove(profile_to_unfollow)
        request.user.profile.save()
        messages.success(
            request,
            f"You have succesfully unfollowed @{profile_to_unfollow.user.get_username()}",
        )
        return redirect(request.META.get("HTTP_REFERER"))
    else:
        messages.success(request, "You must be logged in to view this page")
        return redirect("home")


def follow(request, pk):
    if request.user.is_authenticated:
        profile_to_follow = Profile.objects.get(user_id=pk)
        request.user.profile.follows.add(profile_to_follow)
        request.user.profile.save()
        messages.success(
            request,
            f"You have succesfully followed @{profile_to_follow.user.get_username()}",
        )
        return redirect(request.META.get("HTTP_REFERER"))
    else:
        messages.success(request, "You must be logged in to view this page")
        return redirect("home")


# **********************
# ****** MEEPS *********
# **********************


def meep_like(request, pk):
    if request.user.is_authenticated:
        meep = get_object_or_404(Meep, id=pk)
        # Del meep con id=pk, filtrar los usuarios inlcuidos en likes cuyo id=request.user.id
        # Ej: Tomar meep con id=4.
        # Si request.user.id=1, filtrar los usuarios que hayan dado like al meep con id=4 según el usuario con id=1
        if meep.likes.filter(id=request.user.id):  # Filtro el id del user
            meep.likes.remove(request.user)
        else:
            meep.likes.add(request.user)
        return redirect(request.META.get("HTTP_REFERER"))
    else:
        messages.success(request, "You must be logged in to view this page")
        return redirect("home")


def meep_show(request, pk):
    if request.user.is_authenticated:
        meep = get_object_or_404(Meep, id=pk)
        context = {"meep": meep}
        if meep:
            return render(request, "meep_show.html", context)
        else:
            messages.success(request, "That Meep does not exist.")
    else:
        return redirect("home")


def meep_delete(request, pk):
    if request.user.is_authenticated:
        meep = get_object_or_404(Meep, id=pk)
        if request.user.get_username() == meep.user.get_username():
            meep.delete()
            messages.success(request, "You have deleted the meep.")
            redirect_url = request.META.get("HTTP_REFERER", reverse_lazy("home"))
            return redirect(redirect_url)
        else:
            messages.success(
                request, "That's not your meep. You cannot delete it douchebag!."
            )
            redirect_url = request.META.get("HTTP_REFERER", reverse_lazy("home"))
            return redirect(redirect_url)

    else:
        messages.success(request, "You must be logged in to delete a meep")
        redirect_url = request.META.get("HTTP_REFERER", reverse_lazy("home"))
        return redirect(redirect_url)


def meep_edit(request, pk):
    if request.user.is_authenticated:
        meep = get_object_or_404(Meep, id=pk)
        if request.user.get_username() == meep.user.get_username():
            form = MeepForm(request.POST or None, instance=meep)
            if request.method == "POST":
                if form.is_valid():
                    meep = form.save(commit=False)
                    meep.user = request.user
                    meep.save()
                    messages.success(request, "Your Meep has been edited!")
                    return redirect("home")
            else:
                context = {"meep": meep, "form": form}
                return render(request, "meep_edit.html", context)
        else:
            messages.success(
                request, "That's not your meep. You cannot edit it douchebag!."
            )
            redirect_url = request.META.get("HTTP_REFERER", reverse_lazy("home"))
            return redirect(redirect_url)
    else:
        messages.success(request, "You must be logged in to edit a meep")
        redirect_url = request.META.get("HTTP_REFERER", reverse_lazy("home"))
        return redirect(redirect_url)


def meep_search(request):
    if request.method == "POST":
        search = request.POST["search"]
        # search = request.POST.get("search")

        if search:
            # print(f"Search: {search}")
            meeps = Meep.objects.filter(body__contains=search)
            # print(f"data: {meeps}")
            context = {"search": search, "meeps": meeps}
            return render(request, "meep_search.html", context)
        else:
            messages.success(request, "There is no text to search for.")
            redirect_url = request.META.get("HTTP_REFERER", reverse_lazy("home"))
            return redirect(redirect_url)

    else:
        return render(request, "meep_search.html")


def user_search(request):
    if request.method == "POST":
        search = request.POST["search"]
        if search:
            # print(f"Search: {search}")
            # users = User.objects.filter(username__contains=search)
            # print(f"data: {users}")
            profiles = Profile.objects.filter(user__username__contains=search)
            # print(profiles)
            # context = {"search": search, "users": users}
            context = {"search": search, "profiles": profiles}
            return render(request, "user_search.html", context)
        else:
            messages.success(request, "There is no text to search for.")
            redirect_url = request.META.get("HTTP_REFERER", reverse_lazy("home"))
            return redirect(redirect_url)

    else:
        return render(request, "user_search.html")


# **********************
# ****** VARIOS ********
# **********************


# Your existing profile view
# def profile(request, pk):
#     if request.user.is_authenticated:
#         profile = get_object_or_404(Profile, user_id=pk)
#         context = {"profile": profile}

#         print(profile.follows.all())
#         print(profile.follows.all)

#         handle_follow_action(request, request.user.profile, profile)

#         return render(request, "profile.html", context)
#     else:
#         messages.success(request, "You must be logged in to view this page")
#         return redirect("home")


# def handle_follow_action(request, current_user_profile, profile):
#     if request.method == "POST":
#         action = request.POST.get("follow-btn")

#         if action == "unfollow":
#             current_user_profile.follows.remove(profile)
#         elif action == "follow":
#             current_user_profile.follows.add(profile)
#         else:
#             # If the action is neither follow nor unfollow, return a bad request response
#             return HttpResponseBadRequest("Invalid follow action")

#         current_user_profile.save()


# **********************
# ****** MEMBERS ******
# **********************


def login_user(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        # print(password)
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, ("You have logued in."))
            return redirect("home")
        else:
            messages.success(request, "There was an error loggin in. Try again!")
            return redirect("login")

    else:
        return render(request, "login.html", {})


def logout_user(request):
    logout(request)
    messages.success(request, ("You have logued out."))
    return redirect("home")


def register_user(request):
    form = SignUpForm()
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            # first_name = form.cleaned_data["first_name"]
            # last_name = form.cleaned_data["last_name"]
            # email = form.cleaned_data["email"]
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, ("You have registered succesfully."))
            return redirect("home")

    context = {"form": form}
    return render(request, "register.html", context)


def update_user(request):
    if request.user.is_authenticated:
        current_user = User.objects.get(id=request.user.id)
        profile_user = Profile.objects.get(user_id=request.user.id)

        user_form = UpdateUserForm(
            request.POST or None, request.FILES or None, instance=current_user
        )
        profile_form = ProfilePicForm(
            request.POST or None, request.FILES or None, instance=profile_user
        )

        context = {"user_form": user_form, "profile_form": profile_form}

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            login(request, current_user)
            messages.success(request, ("Your Profile has been updated"))
            return redirect("home")
        return render(request, "update_user.html", context)

    else:
        messages.success(request, ("You must be logged in to view this page"))
        return redirect("home")


# **********************
# ******* ERROS ********
# **********************


# def handling_404(request, exception):
#     print("*** handling 404 ***")
#     print(exception)
#     return render(request, template_name="errors/404.html", status=404)


# **********************
# ****** TESTING *******
# **********************


def test_view(request):
    return HttpResponse("test view")