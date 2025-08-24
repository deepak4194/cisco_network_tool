import logging
import json
from ipaddress import IPv4Network, IPv4Address, AddressValueError
from typing import Dict, List, Any

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('network_tool.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def is_valid_ip(ip_str: str) -> bool:
    """Check if IP address is valid"""
    try:
        IPv4Address(ip_str)
        return True
    except AddressValueError:
        return False

def is_same_network(ip1: str, ip2: str, netmask: str) -> bool:
    """Check if two IPs are in the same network"""
    try:
        net1 = IPv4Network(f"{ip1}/{netmask}", strict=False)
        net2 = IPv4Network(f"{ip2}/{netmask}", strict=False)
        return net1.network_address == net2.network_address
    except:
        return False

def save_json(data: Dict, filename: str):
    """Save data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def load_json(filename: str) -> Dict:
    """Load data from JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
