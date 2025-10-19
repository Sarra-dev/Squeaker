from django.urls import path
from django.conf.urls import handler404

from . import views

# from musker.views import handling_404

general_patterns = [
    path("", views.home, name="home"),
    path("user_search/", views.user_search, name="user_search"),
    path("unfollow/<int:pk>", views.unfollow, name="unfollow"),
    path("follow/<int:pk>", views.follow, name="follow"),
    path("test_view/", views.test_view, name="test_view"),
]

# Group profile URLs
profile_patterns = [
    path("profile_list/", views.profile_list, name="profile_list"),
    path("profile/<int:pk>", views.profile, name="profile"),
    path(
        "profile/followers_list/<int:pk>", views.followers_list, name="followers_list"
    ),
    path("profile/follows_list/<int:pk>", views.follows_list, name="follows_list"),
]

# Group user authentication URLs
user_patterns = [
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("register/", views.register_user, name="register"),
    path("update_user/", views.update_user, name="update_user"),
]

# Group meep-related URLs
meep_patterns = [
    path("meep_like/<int:pk>", views.meep_like, name="meep_like"),
    path("meep_show/<int:pk>", views.meep_show, name="meep_show"),
    path("meep_delete/<int:pk>", views.meep_delete, name="meep_delete"),
    path("meep_edit/<int:pk>", views.meep_edit, name="meep_edit"),
    path("meep_search/", views.meep_search, name="meep_search"),
]

# Combine all URL patterns into the main urlpatterns
urlpatterns = general_patterns + profile_patterns + user_patterns + meep_patterns


# handler404 = "musker.views.handling_404"
# handler404 = handling_404