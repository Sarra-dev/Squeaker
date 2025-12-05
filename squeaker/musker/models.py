from datetime import timedelta
import re
from time import timezone
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.urls import reverse

class Meep(models.Model):
    user = models.ForeignKey(
        User, related_name="meeps",
        on_delete=models.DO_NOTHING
    )
    body = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User , related_name="meep_like" , blank=True)
    image = models.ImageField(upload_to='meep_images/', blank=True, null=True)

    # track or count likes 
    def number_of_likes(self):
        return self.likes.count()
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Extract and save hashtags after meep is saved
        self.extract_hashtags()
    
    def extract_hashtags(self):
        """Extract hashtags from meep body"""
        hashtag_pattern = r'#(\w+)'
        hashtags = re.findall(hashtag_pattern, self.body)
        
        for tag in hashtags:
            hashtag, created = Hashtag.objects.get_or_create(
                name=tag.lower()
            )
            MeepHashtag.objects.get_or_create(
                meep=self,
                hashtag=hashtag
            )
    def __str__(self):
        return(
            f"{self.user} "
            f"({self.created_at:%Y-%m-%d %H:%M}): "
            f"{self.body}..."
        )
class Hashtag(models.Model):
    """Store unique hashtags"""
    name = models.CharField(max_length=100, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"#{self.name}"
    
    def get_meep_count(self, days=7):
        """Get count of meeps with this hashtag in the last N days"""
        time_threshold = timezone.now() - timedelta(days=days)
        return self.meephashtag_set.filter(
            meep__created_at__gte=time_threshold
        ).count()
    
    def get_recent_meeps(self, limit=10):
        """Get recent meeps with this hashtag"""
        return Meep.objects.filter(
            meephashtag__hashtag=self
        ).order_by('-created_at')[:limit]

class MeepHashtag(models.Model):
    """Junction table linking meeps to hashtags"""
    meep = models.ForeignKey(Meep, on_delete=models.CASCADE)
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['meep', 'hashtag']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'hashtag']),
            models.Index(fields=['hashtag', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.hashtag} in {self.meep}"
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
    image = models.ImageField(upload_to='meep_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  # newest first

    def __str__(self):
        return f"{self.user.username} → {self.meep.id}"
    
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
    )
    
    recipient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    meep = models.ForeignKey(
        'Meep', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='notifications'
    )
    comment = models.ForeignKey(
        'Comment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.sender.username} {self.notification_type} - {self.recipient.username}"
    
    def get_message(self):
        """Return a human-readable notification message"""
        if self.notification_type == 'like':
            return f"{self.sender.username} liked your meep"
        elif self.notification_type == 'comment':
            return f"{self.sender.username} commented on your meep"
        elif self.notification_type == 'follow':
            return f"{self.sender.username} started following you"
        return "New notification"
    
    def get_link(self):
        """
        Returns where to go when user clicks the notification:
        - Like/comment → go to meep_show/<id>
        - Follow → go to sender profile
        """

        if self.meep:
            return reverse("meep_show", args=[self.meep.id])

        if self.notification_type == "follow":
            return reverse("profile", args=[self.sender.id])

        # fallback (safety)
        return reverse("notifications")