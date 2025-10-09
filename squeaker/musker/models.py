from django.db import models
from django.contrib.auth.models import User

#create A User Profile Model
class Profile(models.Model):
    user = models.OneToOneField(User , on_delete = models.CASCADE) # associate one user to only one profile
    follows = models.ManyToManyField("self",
            related_name="followed_by",
            symmetrical=False, # user don't have to follow who followed him
            blank=True) #you don't have to follow anybody
    def __str__(self):
        return self.user.username