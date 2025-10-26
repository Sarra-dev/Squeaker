from django.shortcuts import redirect
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
def root_redirect(request):
    return redirect('login')  # redirect '/' to login page

urlpatterns = [
    path('', root_redirect),
    path('home/', views.home, name='home'),
    path('profile_list/', views.profile_list , name='profile_list'),
    path('profile/<int:pk>', views.profile, name='profile'),
     path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('login/', views.login_user, name='login'),
    path('register/', views.register_user, name='register'),
    path('logout/', views.logout_user, name='logout'),
]
