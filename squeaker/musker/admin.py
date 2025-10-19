from django.contrib import admin
from django.contrib.auth.models import Group ,User
from .models import Profile, Meep

#unregister groups
admin.site.unregister(Group)

#Mix profile info into user info
class ProfileInline(admin.StackedInline):
    model = Profile

#extend User Model
class UserAdmin(admin.ModelAdmin):
    model = User
    #just display username fields on admin page
    fields = ["username"]
    inlines = [ProfileInline]

#unregister initial User
admin.site.unregister(User)
#Reregister User and Profile 
admin.site.register(User, UserAdmin)
#admin.site.register(Profile)

admin.site.register(Meep)

