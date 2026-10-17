import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Comment
@receiver(post_save,sender=Comment)
def comment_notification(sender,instance,created,**kwargs):
    if created and not instance.is_approved: logging.getLogger(__name__).info("New comment awaiting approval")
