"""
Input validation utilities for IP management
"""
import re
from typing import Dict, Optional, Tuple

class IPValidator:
    """Validate IP-related inputs"""

    VALID_STATUSES = ['active', 'reserved', 'deprecated', 'planned']

    @staticmethod
    def validate_ip_allocation(data: dict) -> Tuple[bool, Optional[str]]:
        """Validate IP allocation request"""
        required_fields = ['ip_address', 'subnet_id']

        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"

        ip = data['ip_address']
        if not IPValidator.is_valid_ipv4(ip):
            return False, f"Invalid IP address format: {ip}"

        hostname = data.get('hostname')
        if hostname and not IPValidator.is_valid_hostname(hostname):
            return False, f"Invalid hostname format: {hostname}"

        status = data.get('status', 'active')
        if status not in IPValidator.VALID_STATUSES:
            return False, f"Invalid status. Must be one of: {', '.join(IPValidator.VALID_STATUSES)}"

        mac = data.get('mac_address')
        if mac and not IPValidator.is_valid_mac(mac):
            return False, f"Invalid MAC address format: {mac}"

        return True, None

    @staticmethod
    def is_valid_ipv4(ip: str) -> bool:
        """Validate IPv4 address format"""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        octets = ip.split('.')
        return all(0 <= int(octet) <= 255 for octet in octets)

    @staticmethod
    def is_valid_hostname(hostname: str) -> bool:
        """Validate hostname format (RFC 1123)"""
        if len(hostname) > 253:
            return False
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(pattern, hostname))

    @staticmethod
    def is_valid_mac(mac: str) -> bool:
        """Validate MAC address format"""
        patterns = [
            r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$',
            r'^([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}$',
            r'^[0-9A-Fa-f]{12}$',
        ]
        return any(re.match(pattern, mac) for pattern in patterns)

    @staticmethod
    def normalize_mac(mac: str) -> str:
        """Normalize MAC address to xx:xx:xx:xx:xx:xx format"""
        mac_clean = mac.replace(':', '').replace('-', '').upper()
        return ':'.join(mac_clean[i:i+2] for i in range(0, 12, 2))
