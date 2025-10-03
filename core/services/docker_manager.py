"""Docker container management service"""
import docker
from docker.errors import DockerException, NotFound, APIError
import logging

logger = logging.getLogger(__name__)


class DockerManager:
    """Manages Docker container lifecycle operations"""

    def __init__(self):
        try:
            self.client = docker.from_env()
        except DockerException as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise

    def create_volume(self, volume_name):
        """
        Create a Docker volume for persistent storage.

        Args:
            volume_name: Name for the volume

        Returns:
            tuple: (volume_name, error_message)
        """
        try:
            volume = self.client.volumes.create(name=volume_name)
            logger.info(f"Created volume {volume_name}")
            return volume.name, None
        except APIError as e:
            error_msg = f"Failed to create volume {volume_name}: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error creating volume: {str(e)}"
            logger.error(error_msg)
            return None, error_msg

    def delete_volume(self, volume_name):
        """
        Delete a Docker volume.

        Args:
            volume_name: Name of the volume to delete

        Returns:
            tuple: (success, error_message)
        """
        try:
            volume = self.client.volumes.get(volume_name)
            volume.remove()
            logger.info(f"Deleted volume {volume_name}")
            return True, None
        except NotFound:
            logger.warning(f"Volume {volume_name} not found (may already be deleted)")
            return True, None
        except APIError as e:
            error_msg = f"Failed to delete volume {volume_name}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error deleting volume: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def start_container(self, template, host_ports, environment_vars=None, name=None, volume_name=None):
        """
        Start a Docker container from a template.

        Args:
            template: Template model instance
            host_ports: Dict mapping service_name -> host_port
            environment_vars: Dict of environment variables (optional)
            name: Container name (optional)
            volume_name: Docker volume name for persistent storage (optional)

        Returns:
            tuple: (container_id, error_message)
                container_id is None if error occurred
        """
        try:
            # Build port mapping for Docker (container_port -> host_port)
            port_bindings = {}
            for service_name, container_port in template.default_ports.items():
                if service_name in host_ports:
                    port_bindings[f"{container_port}/tcp"] = host_ports[service_name]

            # Merge environment variables
            env_vars = {}
            if template.environment_vars:
                env_vars.update(template.environment_vars)
            if environment_vars:
                env_vars.update(environment_vars)

            # Convert env dict to list format for Docker
            env_list = [f"{k}={v}" for k, v in env_vars.items()] if env_vars else None

            # Container resource limits
            mem_limit = f"{template.memory_limit}m"
            cpu_quota = int(template.cpu_limit * 100000)  # CPU quota in microseconds

            # Build volume mounts if volume is provided
            volumes = None
            if volume_name and template.volume_mounts:
                volumes = {}
                for container_path in template.volume_mounts.values():
                    volumes[volume_name] = {'bind': container_path, 'mode': 'rw'}
                logger.info(f"Mounting volume {volume_name} to {list(template.volume_mounts.values())}")

            # Start the container
            container = self.client.containers.run(
                image=template.docker_image,
                detach=True,
                ports=port_bindings,
                environment=env_list,
                mem_limit=mem_limit,
                cpu_quota=cpu_quota,
                name=name,
                volumes=volumes,
                restart_policy={"Name": "unless-stopped"},
            )

            logger.info(f"Started container {container.id[:12]} from image {template.docker_image}")
            return container.id, None

        except NotFound as e:
            error_msg = f"Docker image not found: {template.docker_image}"
            logger.error(f"{error_msg} - {e}")
            return None, error_msg

        except APIError as e:
            error_msg = f"Docker API error: {str(e)}"
            logger.error(error_msg)
            return None, error_msg

        except Exception as e:
            error_msg = f"Unexpected error starting container: {str(e)}"
            logger.error(error_msg)
            return None, error_msg

    def stop_container(self, container_id):
        """
        Stop a running container.

        Args:
            container_id: Docker container ID

        Returns:
            tuple: (success, error_message)
        """
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=10)
            logger.info(f"Stopped container {container_id[:12]}")
            return True, None

        except NotFound:
            error_msg = f"Container {container_id[:12]} not found"
            logger.warning(error_msg)
            return False, error_msg

        except APIError as e:
            error_msg = f"Failed to stop container: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected error stopping container: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def restart_container(self, container_id):
        """
        Restart a container.

        Args:
            container_id: Docker container ID

        Returns:
            tuple: (success, error_message)
        """
        try:
            container = self.client.containers.get(container_id)
            container.restart(timeout=10)
            logger.info(f"Restarted container {container_id[:12]}")
            return True, None

        except NotFound:
            error_msg = f"Container {container_id[:12]} not found"
            logger.warning(error_msg)
            return False, error_msg

        except APIError as e:
            error_msg = f"Failed to restart container: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected error restarting container: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def delete_container(self, container_id, force=False):
        """
        Delete a container.

        Args:
            container_id: Docker container ID
            force: Force removal even if running

        Returns:
            tuple: (success, error_message)
        """
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            logger.info(f"Deleted container {container_id[:12]}")
            return True, None

        except NotFound:
            # Container already deleted
            logger.warning(f"Container {container_id[:12]} not found (may already be deleted)")
            return True, None

        except APIError as e:
            error_msg = f"Failed to delete container: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected error deleting container: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def get_container_status(self, container_id):
        """
        Get the current status of a container.

        Args:
            container_id: Docker container ID

        Returns:
            str: Container status ('running', 'stopped', 'error', etc.)
        """
        try:
            container = self.client.containers.get(container_id)
            status = container.status.lower()
            return status

        except NotFound:
            return 'not_found'

        except Exception as e:
            logger.error(f"Error getting container status: {e}")
            return 'error'

    def get_container_logs(self, container_id, tail=100):
        """
        Get logs from a container.

        Args:
            container_id: Docker container ID
            tail: Number of lines to retrieve from the end

        Returns:
            str: Container logs
        """
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=True)
            return logs.decode('utf-8', errors='ignore')

        except NotFound:
            return f"Container {container_id[:12]} not found"

        except Exception as e:
            logger.error(f"Error getting container logs: {e}")
            return f"Error retrieving logs: {str(e)}"

    def pull_image(self, image_name):
        """
        Pull a Docker image from registry.

        Args:
            image_name: Name of the Docker image

        Returns:
            tuple: (success, error_message)
        """
        try:
            self.client.images.pull(image_name)
            logger.info(f"Pulled image {image_name}")
            return True, None

        except APIError as e:
            error_msg = f"Failed to pull image {image_name}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected error pulling image: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
