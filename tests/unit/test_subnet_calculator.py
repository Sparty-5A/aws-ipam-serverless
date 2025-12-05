"""
Unit tests for subnet calculator functionality
"""
import pytest
from lambda_functions.subnet_manager.subnet_calculator import (
    calculate_subnets,
    validate_cidr,
    calculate_available_ips,
    get_network_address,
    get_broadcast_address,
)


class TestSubnetCalculator:
    """Test suite for subnet calculator functions"""

    def test_validate_cidr_valid(self):
        """Test valid CIDR notation"""
        assert validate_cidr("192.168.1.0/24") == True
        assert validate_cidr("10.0.0.0/8") == True
        assert validate_cidr("172.16.0.0/12") == True

    def test_validate_cidr_invalid(self):
        """Test invalid CIDR notation"""
        assert validate_cidr("192.168.1.0") == False
        assert validate_cidr("192.168.1.0/33") == False
        assert validate_cidr("256.1.1.1/24") == False
        assert validate_cidr("not-an-ip/24") == False

    def test_calculate_available_ips(self):
        """Test available IP calculation"""
        # /24 network: 256 total - 2 (network + broadcast) = 254 usable
        assert calculate_available_ips(24) == 254
        
        # /30 network: 4 total - 2 = 2 usable (point-to-point)
        assert calculate_available_ips(30) == 2
        
        # /16 network: 65536 - 2 = 65534 usable
        assert calculate_available_ips(16) == 65534

    def test_get_network_address(self):
        """Test network address calculation"""
        assert get_network_address("192.168.1.100", 24) == "192.168.1.0"
        assert get_network_address("10.5.7.200", 16) == "10.5.0.0"
        assert get_network_address("172.16.45.89", 12) == "172.16.0.0"

    def test_get_broadcast_address(self):
        """Test broadcast address calculation"""
        assert get_broadcast_address("192.168.1.0", 24) == "192.168.1.255"
        assert get_broadcast_address("10.0.0.0", 8) == "10.255.255.255"
        assert get_broadcast_address("172.16.0.0", 12) == "172.31.255.255"

    def test_calculate_subnets_even_split(self):
        """Test subnet calculation with even split"""
        parent = "192.168.1.0/24"
        count = 4
        
        subnets = calculate_subnets(parent, count)
        
        assert len(subnets) == 4
        assert subnets[0]["network"] == "192.168.1.0/26"
        assert subnets[1]["network"] == "192.168.1.64/26"
        assert subnets[2]["network"] == "192.168.1.128/26"
        assert subnets[3]["network"] == "192.168.1.192/26"
        
        # Each /26 should have 62 usable IPs
        for subnet in subnets:
            assert subnet["usable_ips"] == 62

    def test_calculate_subnets_large_network(self):
        """Test subnet calculation on large network"""
        parent = "10.0.0.0/16"
        count = 256
        
        subnets = calculate_subnets(parent, count)
        
        assert len(subnets) == 256
        # Each subnet should be /24
        assert all(subnet["prefix_length"] == 24 for subnet in subnets)
        
        # First subnet should start at 10.0.0.0
        assert subnets[0]["network"] == "10.0.0.0/24"
        
        # Last subnet should be 10.0.255.0
        assert subnets[-1]["network"] == "10.0.255.0/24"

    def test_calculate_subnets_invalid_count(self):
        """Test error handling for invalid subnet count"""
        with pytest.raises(ValueError):
            calculate_subnets("192.168.1.0/24", 0)
        
        with pytest.raises(ValueError):
            calculate_subnets("192.168.1.0/24", -5)

    def test_calculate_subnets_too_many(self):
        """Test error when requesting too many subnets"""
        # /30 only has 4 IPs, can't split into 10 subnets
        with pytest.raises(ValueError):
            calculate_subnets("192.168.1.0/30", 10)

    @pytest.mark.parametrize("cidr,expected_mask", [
        (8, "255.0.0.0"),
        (16, "255.255.0.0"),
        (24, "255.255.255.0"),
        (30, "255.255.255.252"),
    ])
    def test_cidr_to_netmask_conversion(self, cidr, expected_mask):
        """Test CIDR to netmask conversion"""
        # This would be implemented in your calculator
        # Just showing test structure
        pass


class TestSubnetValidation:
    """Test suite for subnet validation"""

    def test_subnet_overlap_detection(self):
        """Test detecting overlapping subnets"""
        subnet1 = "192.168.1.0/24"
        subnet2 = "192.168.1.128/25"  # Overlaps with subnet1
        
        # Your validation function would detect overlap
        # assert subnets_overlap(subnet1, subnet2) == True
        pass

    def test_subnet_within_parent(self):
        """Test checking if subnet is within parent network"""
        parent = "10.0.0.0/16"
        child = "10.0.5.0/24"
        
        # Should be within parent
        # assert is_subnet_of(child, parent) == True
        pass


class TestIPRangeCalculation:
    """Test suite for IP range calculations"""

    def test_first_usable_ip(self):
        """Test calculation of first usable IP"""
        # First usable IP in 192.168.1.0/24 is 192.168.1.1
        network = "192.168.1.0"
        # assert get_first_usable_ip(network, 24) == "192.168.1.1"
        pass

    def test_last_usable_ip(self):
        """Test calculation of last usable IP"""
        # Last usable IP in 192.168.1.0/24 is 192.168.1.254
        network = "192.168.1.0"
        # assert get_last_usable_ip(network, 24) == "192.168.1.254"
        pass


# Fixtures for common test data
@pytest.fixture
def sample_networks():
    """Provide sample network data for tests"""
    return {
        "small": "192.168.1.0/24",
        "medium": "10.0.0.0/16",
        "large": "172.16.0.0/12",
        "tiny": "192.168.1.0/30",
    }


@pytest.fixture
def sample_subnets():
    """Provide sample subnet data for tests"""
    return [
        {"network": "192.168.1.0/26", "name": "subnet1"},
        {"network": "192.168.1.64/26", "name": "subnet2"},
        {"network": "192.168.1.128/26", "name": "subnet3"},
    ]
