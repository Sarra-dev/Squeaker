from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

class Meep(models.Model):
    user = models.ForeignKey(
        User, related_name="meeps",
        on_delete=models.DO_NOTHING
    )
    body = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User , related_name="meep_like" , blank=True)

    # track or count likes 
    def number_of_likes(self):
        return self.likes.count()
    
    def __str__(self):
        return(
            f"{self.user} "
            f"({self.created_at:%Y-%m-%d %H:%M}): "
            f"{self.body}..."
        )

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    follows = models.ManyToManyField(
        "self",
        related_name="followed_by",
        symmetrical=False,
        blank=True
    )
    
    # New fields for profile customization
    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True
    )
    cover_image = models.ImageField(
        upload_to='cover_images/',
        blank=True,
        null=True
    )
    bio = models.TextField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(max_length=200, blank=True)
    date_modified = models.DateTimeField(auto_now=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    def __str__(self):
        return self.user.username
    
    @property
    def followers_count(self):
        return self.followed_by.count()
    
    @property
    def following_count(self):
        return self.follows.count()

# Create profile when new user signs up
def create_profile(sender, instance, created, **kwargs):
    if created:
        user_profile = Profile(user=instance)
        user_profile.save()
        # Have the user follow themselves
        user_profile.follows.set([instance.profile.id])
        user_profile.save()

post_save.connect(create_profile, sender=User)