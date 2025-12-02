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

class Comment(models.Model):
    meep = models.ForeignKey("Meep", on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  # newest first

    def __str__(self):
        return f"{self.user.username} → {self.meep.id}"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username} → {self.recipient.username}: {self.content[:30]}"

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    last_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversation_last')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        users = self.participants.all()
        return f"Conversation: {', '.join([u.username for u in users])}"
    
    def get_other_user(self, current_user):
        """Get the other participant in a 1-on-1 conversation"""
        return self.participants.exclude(id=current_user.id).first()
    
    def unread_count(self, user):
        """Count unread messages for a specific user"""
        return Message.objects.filter(
            sender__in=self.participants.all(),
            recipient=user,
            is_read=False
        ).count()