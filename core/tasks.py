"""Celery tasks for asynchronous container operations"""
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def create_instance_task(self, instance_id):
    """
    Asynchronous task to create and start a Docker container instance.

    Args:
        instance_id: ID of the Instance model

    Returns:
        dict: Result with success status and message
    """
    from core.models import Instance, AuditLog
    from core.services.docker_manager import DockerManager
    from core.services.port_manager import PortManager

    try:
        instance = Instance.objects.get(id=instance_id)
        template = instance.template

        # Allocate ports
        port_manager = PortManager()
        try:
            host_ports = port_manager.allocate_ports(template.default_ports)
            instance.host_ports = host_ports
            instance.save()
        except ValueError as e:
            instance.status = 'error'
            instance.error_message = f"Port allocation failed: {str(e)}"
            instance.save()
            logger.error(f"Port allocation failed for instance {instance_id}: {e}")
            return {'success': False, 'error': str(e)}

        # Create persistent volume if template requires it
        docker_manager = DockerManager()
        volume_name = None

        if template.volume_mounts:
            volume_name = f"{instance.user.username}_{template.name}_{instance.id}_data"
            created_volume, vol_error = docker_manager.create_volume(volume_name)

            if created_volume:
                instance.volume_name = volume_name
                instance.save()
                logger.info(f"Created persistent volume {volume_name} for instance {instance_id}")
            else:
                instance.status = 'error'
                instance.error_message = f"Volume creation failed: {vol_error}"
                instance.save()
                logger.error(f"Volume creation failed for instance {instance_id}: {vol_error}")
                return {'success': False, 'error': vol_error}

        # Start Docker container
        container_name = f"{instance.user.username}_{template.name}_{instance.id}"

        container_id, error_msg = docker_manager.start_container(
            template=template,
            host_ports=host_ports,
            environment_vars=instance.environment_vars,
            name=container_name,
            volume_name=volume_name
        )

        if container_id:
            instance.container_id = container_id
            instance.status = 'running'
            instance.error_message = ''
            instance.save()

            # Log the action
            AuditLog.objects.create(
                user=instance.user,
                action='create',
                instance=instance,
                details=f"Started container {container_id[:12]}"
            )

            logger.info(f"Successfully created instance {instance_id} with container {container_id[:12]}")
            return {'success': True, 'container_id': container_id}
        else:
            instance.status = 'error'
            instance.error_message = error_msg
            instance.save()
            logger.error(f"Failed to create instance {instance_id}: {error_msg}")
            return {'success': False, 'error': error_msg}

    except ObjectDoesNotExist:
        logger.error(f"Instance {instance_id} not found")
        return {'success': False, 'error': 'Instance not found'}

    except Exception as e:
        logger.error(f"Unexpected error creating instance {instance_id}: {e}")
        # Retry the task
        try:
            raise self.retry(exc=e, countdown=60)
        except self.MaxRetriesExceededError:
            if 'instance' in locals():
                instance.status = 'error'
                instance.error_message = f"Failed after retries: {str(e)}"
                instance.save()
            return {'success': False, 'error': f'Max retries exceeded: {str(e)}'}


@shared_task
def stop_instance_task(instance_id):
    """
    Asynchronous task to stop a Docker container instance.

    Args:
        instance_id: ID of the Instance model

    Returns:
        dict: Result with success status and message
    """
    from core.models import Instance, AuditLog
    from core.services.docker_manager import DockerManager

    try:
        instance = Instance.objects.get(id=instance_id)

        if not instance.container_id:
            return {'success': False, 'error': 'No container ID found'}

        docker_manager = DockerManager()
        success, error_msg = docker_manager.stop_container(instance.container_id)

        if success:
            instance.status = 'stopped'
            instance.save()

            # Log the action
            AuditLog.objects.create(
                user=instance.user,
                action='stop',
                instance=instance,
                details=f"Stopped container {instance.container_id[:12]}"
            )

            logger.info(f"Successfully stopped instance {instance_id}")
            return {'success': True}
        else:
            instance.error_message = error_msg
            instance.save()
            logger.error(f"Failed to stop instance {instance_id}: {error_msg}")
            return {'success': False, 'error': error_msg}

    except ObjectDoesNotExist:
        logger.error(f"Instance {instance_id} not found")
        return {'success': False, 'error': 'Instance not found'}

    except Exception as e:
        logger.error(f"Unexpected error stopping instance {instance_id}: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def restart_instance_task(instance_id):
    """
    Asynchronous task to restart a Docker container instance.

    Args:
        instance_id: ID of the Instance model

    Returns:
        dict: Result with success status and message
    """
    from core.models import Instance, AuditLog
    from core.services.docker_manager import DockerManager

    try:
        instance = Instance.objects.get(id=instance_id)

        if not instance.container_id:
            return {'success': False, 'error': 'No container ID found'}

        docker_manager = DockerManager()
        success, error_msg = docker_manager.restart_container(instance.container_id)

        if success:
            instance.status = 'running'
            instance.error_message = ''
            instance.save()

            # Log the action
            AuditLog.objects.create(
                user=instance.user,
                action='start',
                instance=instance,
                details=f"Restarted container {instance.container_id[:12]}"
            )

            logger.info(f"Successfully restarted instance {instance_id}")
            return {'success': True}
        else:
            instance.error_message = error_msg
            instance.save()
            logger.error(f"Failed to restart instance {instance_id}: {error_msg}")
            return {'success': False, 'error': error_msg}

    except ObjectDoesNotExist:
        logger.error(f"Instance {instance_id} not found")
        return {'success': False, 'error': 'Instance not found'}

    except Exception as e:
        logger.error(f"Unexpected error restarting instance {instance_id}: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def delete_instance_task(instance_id, user_id, delete_volume=False):
    """
    Asynchronous task to delete a Docker container instance.

    Args:
        instance_id: ID of the Instance model
        user_id: ID of the user performing the action
        delete_volume: Whether to delete the persistent volume (default: False to preserve data)

    Returns:
        dict: Result with success status and message
    """
    from core.models import Instance, AuditLog
    from core.services.docker_manager import DockerManager
    from django.contrib.auth.models import User

    try:
        instance = Instance.objects.get(id=instance_id)
        container_id = instance.container_id
        volume_name = instance.volume_name

        docker_manager = DockerManager()

        # Delete container
        if container_id:
            success, error_msg = docker_manager.delete_container(container_id, force=True)

            if not success:
                logger.warning(f"Failed to delete container {container_id[:12]}: {error_msg}")
                # Continue with cleanup even if container deletion fails

        # Delete volume if requested
        if delete_volume and volume_name:
            success, error_msg = docker_manager.delete_volume(volume_name)
            if success:
                logger.info(f"Deleted volume {volume_name} for instance {instance_id}")
            else:
                logger.warning(f"Failed to delete volume {volume_name}: {error_msg}")
        elif volume_name:
            logger.info(f"Preserving volume {volume_name} for potential future use")

        # Log the action before deleting
        try:
            user = User.objects.get(id=user_id)
            details = f"Deleted instance {instance.name or instance.id} with container {container_id[:12] if container_id else 'N/A'}"
            if volume_name and not delete_volume:
                details += f" (preserved volume {volume_name})"
            elif volume_name and delete_volume:
                details += f" (deleted volume {volume_name})"

            AuditLog.objects.create(
                user=user,
                action='delete',
                template=instance.template,
                details=details
            )
        except:
            pass

        # Delete the instance from database
        instance.delete()

        logger.info(f"Successfully deleted instance {instance_id}")
        return {'success': True}

    except ObjectDoesNotExist:
        logger.error(f"Instance {instance_id} not found")
        return {'success': False, 'error': 'Instance not found'}

    except Exception as e:
        logger.error(f"Unexpected error deleting instance {instance_id}: {e}")
        return {'success': False, 'error': str(e)}
