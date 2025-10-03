"""Port management utilities for assigning random ports to container instances"""
import random
from django.conf import settings
from django.db.models import Q
from core.models import Instance


class PortManager:
    """Manages port allocation for Docker containers"""

    def __init__(self):
        self.port_range_start = settings.PORT_RANGE_START
        self.port_range_end = settings.PORT_RANGE_END

    def get_used_ports(self):
        """Get all currently used ports from the database"""
        used_ports = set()
        instances = Instance.objects.filter(
            Q(status='running') | Q(status='pending')
        )

        for instance in instances:
            if instance.host_ports:
                for port in instance.host_ports.values():
                    used_ports.add(int(port))

        return used_ports

    def get_available_port(self):
        """Get a single random available port"""
        used_ports = self.get_used_ports()
        available_ports = set(range(self.port_range_start, self.port_range_end + 1)) - used_ports

        if not available_ports:
            raise ValueError("No available ports in the configured range")

        return random.choice(list(available_ports))

    def allocate_ports(self, port_mapping):
        """
        Allocate random host ports for the given container port mapping.

        Args:
            port_mapping: Dict of service_name -> container_port (e.g., {"vscode": 8080})

        Returns:
            Dict of service_name -> host_port (e.g., {"vscode": 49152})
        """
        used_ports = self.get_used_ports()
        available_ports = list(
            set(range(self.port_range_start, self.port_range_end + 1)) - used_ports
        )

        if len(available_ports) < len(port_mapping):
            raise ValueError(
                f"Not enough available ports. Need {len(port_mapping)}, "
                f"but only {len(available_ports)} available"
            )

        # Randomly shuffle and assign ports
        random.shuffle(available_ports)
        allocated_ports = {}

        for i, service_name in enumerate(port_mapping.keys()):
            allocated_ports[service_name] = available_ports[i]

        return allocated_ports

    def release_ports(self, instance):
        """
        Release ports used by an instance (called when instance is deleted)
        This is handled automatically when instance is deleted from DB,
        but this method can be used for explicit cleanup.
        """
        # Ports are automatically released when instance status changes or is deleted
        pass

    def check_port_availability(self, count=1):
        """
        Check if specified number of ports are available.

        Args:
            count: Number of ports needed

        Returns:
            bool: True if enough ports are available
        """
        used_ports = self.get_used_ports()
        available_count = (self.port_range_end - self.port_range_start + 1) - len(used_ports)
        return available_count >= count
