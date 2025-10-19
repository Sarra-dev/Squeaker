from django.contrib import admin
from django.contrib.auth.models import Group, User
from .models import Profile, Meep

admin.site.unregister(Group)


# Mix Profile and User info
class ProfileInline(admin.StackedInline):
    model = Profile


# Extend user model
class UserAdmin(admin.ModelAdmin):
    model = User
    fields = ["username"]
    inlines = [ProfileInline]


admin.site.unregister(User)
# admin.site.register(User)
admin.site.register(User, UserAdmin)
admin.site.register(Meep)
# admin.site.register(Profile)