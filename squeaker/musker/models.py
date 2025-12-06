import re
from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.urls import reverse

# -------------------------
# MEEP MODEL
# -------------------------
class Meep(models.Model):
    user = models.ForeignKey(User, related_name="meeps", on_delete=models.DO_NOTHING)
    body = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name="meep_likes", blank=True)
    image = models.ImageField(upload_to='meep_images/', blank=True, null=True)

    def number_of_likes(self):
        return self.likes.count()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.extract_hashtags()

    def extract_hashtags(self):
        hashtag_pattern = r'#(\w+)'
        hashtags = set(re.findall(hashtag_pattern, self.body))
        for tag in hashtags:
            hashtag_obj, _ = Hashtag.objects.get_or_create(name=tag.lower())
            MeepHashtag.objects.get_or_create(meep=self, hashtag=hashtag_obj)

    def __str__(self):
        return f"{self.user.username} ({self.created_at:%Y-%m-%d %H:%M}): {self.body[:20]}"


# -------------------------
# SHARE MODEL
# -------------------------
class Share(models.Model):
    user = models.ForeignKey(User, related_name="shares", on_delete=models.CASCADE)
    meep = models.ForeignKey(Meep, related_name="shares", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'meep')

    def __str__(self):
        return f"{self.user.username} shared Meep {self.meep.id}"


# -------------------------
# HASHTAG MODEL
# -------------------------
class Hashtag(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.name}"

    def get_meep_count(self, days=7):
        threshold = timezone.now() - timedelta(days=days)
        return self.meephashtag_set.filter(meep__created_at__gte=threshold).count()

    def get_recent_meeps(self, limit=10):
        return Meep.objects.filter(meephashtag__hashtag=self).order_by('-created_at')[:limit]


# -------------------------
# MEEP-HASHTAG BRIDGE MODEL
# -------------------------
class MeepHashtag(models.Model):
    meep = models.ForeignKey(Meep, on_delete=models.CASCADE)
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('meep', 'hashtag')
        ordering = ['-created_at']
        indexes = [models.Index(fields=['hashtag', '-created_at'])]

    def __str__(self):
        return f"{self.hashtag} in Meep {self.meep.id}"


# -------------------------
# PROFILE MODEL
# -------------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    follows = models.ManyToManyField("self", related_name="followed_by", symmetrical=False, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='cover_images/', blank=True, null=True)
    bio = models.TextField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
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


# -------------------------
# AUTO-CREATE PROFILE ON USER SIGNUP
# -------------------------
def create_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(user=instance)
        profile.follows.add(profile)  # user follows themselves
        profile.save()

post_save.connect(create_profile, sender=User)


# -------------------------
# COMMENT MODEL
# -------------------------
class Comment(models.Model):
    meep = models.ForeignKey(Meep, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    image = models.ImageField(upload_to='meep_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} → Meep {self.meep.id}"


# -------------------------
# MESSAGE MODEL
# -------------------------
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


# -------------------------
# CONVERSATION MODEL
# -------------------------
class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    last_message = models.ForeignKey(
        Message, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='conversation_last'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation: {', '.join([u.username for u in self.participants.all()])}"

    def get_other_user(self, current_user):
        return self.participants.exclude(id=current_user.id).first()

    def unread_count(self, user):
        return Message.objects.filter(recipient=user, is_read=False).count()


# -------------------------
# NOTIFICATION MODEL
# -------------------------
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    meep = models.ForeignKey(Meep, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]

    def __str__(self):
        return f"{self.sender.username} → {self.recipient.username} ({self.notification_type})"

    def get_message(self):
        if self.notification_type == 'like':
            return f"{self.sender.username} liked your meep"
        if self.notification_type == 'comment':
            return f"{self.sender.username} commented on your meep"
        if self.notification_type == 'follow':
            return f"{self.sender.username} started following you"
        return "New notification"

    def get_link(self):
        if self.meep:
            return reverse("meep_show", args=[self.meep.id])
        if self.notification_type == "follow":
            return reverse("profile", args=[self.sender.id])
        return reverse("notifications")
