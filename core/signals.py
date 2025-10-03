"""Signals for automatic profile creation and cleanup"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from core.models import Profile, Instance
from core.services.docker_manager import DockerManager
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a Profile when a new User is created"""
    if created:
        Profile.objects.create(user=instance)
        logger.info(f"Created profile for user {instance.username}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the profile whenever the user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_delete, sender=Instance)
def cleanup_container_on_delete(sender, instance, **kwargs):
    """
    Clean up Docker container when an Instance is deleted.
    This is a fallback in case the delete task doesn't run.
    """
    if instance.container_id:
        try:
            docker_manager = DockerManager()
            docker_manager.delete_container(instance.container_id, force=True)
            logger.info(f"Cleaned up container {instance.container_id[:12]} for deleted instance {instance.id}")
        except Exception as e:
            logger.error(f"Failed to cleanup container {instance.container_id[:12]}: {e}")
