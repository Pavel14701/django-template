import contextlib
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile
from django.conf import settings


def createProfile(sender, instance, created, **kwargs):
    if created:
        user = instance
        profile = Profile.objects.create(
            user=user,
            username=user.username,
            email=user.email,
            name=user.first_name,
        )


def updateUser(sender, instance, created, **kwargs):
    profile = instance
    if created == False:
        user:User = profile.user
        user.first_name = profile.name
        user.username = profile.username
        user.email = profile.email
        user.phone = profile.phone
        user.save()


def deleteUser(sender, instance, **kwargs):
    with contextlib.suppress(Exception):
        user = instance.user
        user.delete()


post_save.connect(createProfile, sender=User)
post_save.connect(updateUser, sender=Profile)
post_delete.connect(deleteUser, sender=Profile)