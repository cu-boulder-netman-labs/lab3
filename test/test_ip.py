import pytest
from validateIP import validate_ip

class TestValidIPs:
    """Test valid IP addresses."""

    @pytest.mark.parametrize("ip", [
        "192.168.0.1",
        "10.0.0.1",
        "172.16.0.1",
        "8.8.8.8",
        "1.1.1.1",
        "0.0.0.0",
        "223.255.255.255",
        "169.253.255.255",
        "126.255.255.255",
        "1.2.3.4",
        "100.100.100.100",
    ])
    def test_valid_ips(self, ip):
        """Valid IPs should return True."""
        assert validate_ip(ip) is True, f"{ip} should be valid"


class TestInvalidFormat:
    """Test IPs with invalid format."""

    @pytest.mark.parametrize("ip", [
        "1.1.1",  # Only 3 octets
        "1.1.1.1.1",  # 5 octets
        "192.168.0",  # Missing octet
        "1.1.1.",  # Trailing dot
        ".1.1.1.1",  # Leading dot
        "1..1.1",  # Empty octet
        "",  # Empty string
    ])
    def test_wrong_number_of_octets(self, ip):
        """IPs with wrong number of octets should be invalid."""
        assert validate_ip(ip) is False, f"{ip} should be invalid"

    @pytest.mark.parametrize("ip", [
        "a.b.c.d",
        "1.1.1a.1",
        "1.1.1.1a",
        "192.168.-1.1",
    ])
    def test_non_numeric_characters(self, ip):
        """IPs with non-numeric characters should be invalid."""
        assert validate_ip(ip) is False, f"{ip} should be invalid"

    @pytest.mark.parametrize("ip", [
        "192,168,0,1",  # Commas
        "192 168 0 1",  # Spaces
    ])
    def test_wrong_separator(self, ip):
        """IPs with wrong separators should be invalid."""
        assert validate_ip(ip) is False, f"{ip} should be invalid"


class TestOutOfRange:
    """Test IPs with octets outside valid range."""

    @pytest.mark.parametrize("ip", [
        "256.1.1.1",
        "1.256.1.1",
        "1.1.256.1",
        "1.1.1.256",
        "300.168.0.1",
        "192.168.0.999",
        "1.1.1.300",
    ])
    def test_octets_above_255(self, ip):
        """IPs with octets > 255 should be invalid."""
        assert validate_ip(ip) is False, f"{ip} should be invalid"


class TestLeadingZeros:
    """Test IPs with leading zeros."""

    @pytest.mark.parametrize("ip", [
        "192.168.001.1",
        "192.168.01.1",
        "01.1.1.1",
        "192.168.0.01",
        "001.002.003.004",
    ])
    def test_leading_zeros_invalid(self, ip):
        """IPs with leading zeros should be invalid."""
        assert validate_ip(ip) is False, f"{ip} should be invalid (leading zeros)"

    @pytest.mark.parametrize("ip", [
        "0.0.0.0",
        "0.0.0.1",
        "192.0.0.1",
        "1.0.0.0",
    ])
    def test_single_zero_octets_valid(self, ip):
        """Single '0' octets should be valid."""
        assert validate_ip(ip) is True, f"{ip} should be valid (single zeros ok)"


class TestLoopbackRange:
    """Test loopback range 127.0.0.0/8."""

    @pytest.mark.parametrize("ip", [
        "127.0.0.1",
        "127.0.0.0",
        "127.255.255.255",
        "127.1.1.1",
        "127.100.50.25",
    ])
    def test_loopback_rejected(self, ip):
        """Loopback IPs should be rejected."""
        assert validate_ip(ip) is False, f"{ip} should be invalid (loopback)"


class TestLinkLocalRange:
    """Test link-local range 169.254.0.0/16."""

    @pytest.mark.parametrize("ip", [
        "169.254.0.0",
        "169.254.255.255",
        "169.254.1.1",
        "169.254.100.50",
    ])
    def test_link_local_rejected(self, ip):
        """Link-local IPs should be rejected."""
        assert validate_ip(ip) is False, f"{ip} should be invalid (link-local)"

    @pytest.mark.parametrize("ip", [
        "169.0.0.1",
        "169.253.0.0",
        "169.255.0.0",
        "169.1.1.1",
    ])
    def test_outside_link_local_valid(self, ip):
        """169.x.x.x outside 169.254.x.x should be valid."""
        assert validate_ip(ip) is True, f"{ip} should be valid (not link-local)"


class TestMulticastRange:
    """Test multicast range 224.0.0.0/4 (224-239)."""

    @pytest.mark.parametrize("ip", [
        "224.0.0.0",
        "224.0.0.1",
        "239.255.255.255",
        "230.1.1.1",
        "235.100.50.25",
    ])
    def test_multicast_rejected(self, ip):
        """Multicast IPs should be rejected."""
        assert validate_ip(ip) is False, f"{ip} should be invalid (multicast)"

    def test_before_multicast_valid(self):
        """IP just before multicast range should be valid."""
        assert validate_ip("223.255.255.255") is True

    def test_after_multicast_invalid(self):
        """IP just after multicast is experimental, should be invalid."""
        assert validate_ip("240.0.0.0") is False


class TestExperimentalRange:
    """Test experimental/reserved range 240.0.0.0/4 (240-255)."""

    @pytest.mark.parametrize("ip", [
        "240.0.0.0",
        "240.0.0.1",
        "255.255.255.255",
        "255.255.255.254",
        "250.1.1.1",
        "254.254.254.254",
    ])
    def test_experimental_rejected(self, ip):
        """Experimental/reserved IPs should be rejected."""
        assert validate_ip(ip) is False, f"{ip} should be invalid (experimental/reserved)"


class TestBoundaryValues:
    """Test boundary values around restricted ranges."""

    def test_before_loopback(self):
        """126.x.x.x should be valid."""
        assert validate_ip("126.255.255.255") is True

    def test_after_loopback(self):
        """128.x.x.x should be valid."""
        assert validate_ip("128.0.0.0") is True

    def test_before_multicast(self):
        """223.x.x.x should be valid."""
        assert validate_ip("223.255.255.255") is True

    @pytest.mark.parametrize("ip,expected", [
        ("126.255.255.255", True),  # Just before loopback
        ("127.0.0.0", False),  # Start of loopback
        ("128.0.0.0", True),  # Just after loopback
        ("223.255.255.255", True),  # Just before multicast
        ("224.0.0.0", False),  # Start of multicast
        ("239.255.255.255", False),  # End of multicast
        ("240.0.0.0", False),  # Start of experimental
    ])
    def test_range_boundaries(self, ip, expected):
        """Test boundaries of all restricted ranges."""
        assert validate_ip(ip) is expected


class TestPrivateNetworks:
    """Test that private network addresses are valid."""

    @pytest.mark.parametrize("ip", [
        "10.0.0.0",
        "10.255.255.255",
        "172.16.0.0",
        "172.31.255.255",
        "192.168.0.0",
        "192.168.255.255",
    ])
    def test_private_networks_valid(self, ip):
        """Private network IPs should be valid."""
        assert validate_ip(ip) is True, f"{ip} should be valid (private network)"


class TestEdgeCases:
    """Additional edge case tests."""

    def test_all_zeros(self):
        """0.0.0.0 should be valid."""
        assert validate_ip("0.0.0.0") is True

    @pytest.mark.parametrize("ip,expected,reason", [
        ("255.255.255.255", False, "broadcast/reserved"),
        ("255.255.255.254", False, "reserved range"),
        ("223.223.223.223", True, "high but valid"),
    ])
    def test_high_values(self, ip, expected, reason):
        """Test high octet values."""
        assert validate_ip(ip) is expected, f"{ip} - {reason}"

    @pytest.mark.parametrize("ip", [
        "1.1.1.1",
        "100.100.100.100",
        "88.88.88.88",
    ])
    def test_repeated_digits(self, ip):
        """IPs with repeated digits should work correctly."""
        assert validate_ip(ip) is True

    @pytest.mark.parametrize("ip", [
        "192.0.0.1",
        "1.0.1.0",
        "0.1.0.1",
    ])
    def test_mixed_zeros_and_values(self, ip):
        """Test mixed zeros and other values."""
        assert validate_ip(ip) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])