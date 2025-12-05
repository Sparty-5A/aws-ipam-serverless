"""
IP subnet calculation utilities
Leverages network engineering expertise!
"""
import ipaddress
from typing import Dict, List

class SubnetCalculator:
    """Handle all subnet math operations"""

    @staticmethod
    def parse_cidr(cidr: str) -> Dict:
        """Parse CIDR notation and return network details"""
        try:
            network = ipaddress.IPv4Network(cidr, strict=False)

            return {
                "network": str(network.network_address),
                "prefix_length": network.prefixlen,
                "netmask": str(network.netmask),
                "wildcard": str(network.hostmask),
                "first_usable": str(network.network_address + 1) if network.num_addresses > 2 else str(network.network_address),
                "last_usable": str(network.broadcast_address - 1) if network.num_addresses > 2 else str(network.broadcast_address),
                "broadcast": str(network.broadcast_address),
                "total_ips": network.num_addresses,
                "usable_ips": network.num_addresses - 2 if network.num_addresses > 2 else network.num_addresses,
            }
        except ValueError as e:
            raise ValueError(f"Invalid CIDR notation: {str(e)}")

    @staticmethod
    def is_ip_in_subnet(ip: str, cidr: str) -> bool:
        """Check if IP address belongs to subnet"""
        try:
            ip_obj = ipaddress.IPv4Address(ip)
            network = ipaddress.IPv4Network(cidr, strict=False)
            return ip_obj in network
        except ValueError:
            return False

    @staticmethod
    def calculate_utilization(allocated_count: int, total_usable: int) -> float:
        """Calculate subnet utilization percentage"""
        if total_usable == 0:
            return 0.0
        return round((allocated_count / total_usable) * 100, 2)

    @staticmethod
    def get_next_available_ip(cidr: str, allocated_ips: List[str]) -> str:
        """Find next available IP in subnet"""
        network = ipaddress.IPv4Network(cidr, strict=False)
        allocated_set = set(allocated_ips)

        for ip in network.hosts():
            if str(ip) not in allocated_set:
                return str(ip)

        raise ValueError("No available IPs in subnet")

    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IP address format"""
        try:
            ipaddress.IPv4Address(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def subnet_overlap(cidr1: str, cidr2: str) -> bool:
        """Check if two subnets overlap"""
        try:
            network1 = ipaddress.IPv4Network(cidr1, strict=False)
            network2 = ipaddress.IPv4Network(cidr2, strict=False)
            return network1.overlaps(network2)
        except ValueError:
            return False

def get_subnet_id(cidr: str) -> str:
    """Convert CIDR to subnet_id for DynamoDB key"""
    return cidr.replace("/", "_")

def cidr_from_subnet_id(subnet_id: str) -> str:
    """Convert subnet_id back to CIDR"""
    return subnet_id.replace("_", "/")
