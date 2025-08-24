import os
import re
from typing import Dict, List, Optional
from utils import setup_logging, is_valid_ip

logger = setup_logging()

class ConfigParser:
    def __init__(self):
        self.devices = {}
        self.interfaces = {}
        
    def parse_directory(self, config_dir: str) -> Dict:
        """Parse all configuration files in directory"""
        logger.info(f"Parsing configuration directory: {config_dir}")
        
        for device_dir in os.listdir(config_dir):
            device_path = os.path.join(config_dir, device_dir)
            if os.path.isdir(device_path):
                config_file = os.path.join(device_path, "config.dump")
                if os.path.exists(config_file):
                    self.parse_device_config(device_dir, config_file)
                else:
                    logger.warning(f"Missing config file for device: {device_dir}")
        
        return {
            'devices': self.devices,
            'interfaces': self.interfaces
        }
    
    def parse_device_config(self, device_name: str, config_file: str):
        """Parse individual device configuration"""
        logger.info(f"Parsing device: {device_name}")
        
        device_info = {
            'name': device_name,
            'type': self._determine_device_type(device_name),
            'interfaces': {},
            'routing_protocols': [],
            'vlans': {},
            'hostname': device_name
        }
        
        try:
            with open(config_file, 'r') as f:
                content = f.read()
                
            # Parse interfaces
            self._parse_interfaces(device_info, content)
            
            # Parse routing protocols
            self._parse_routing_protocols(device_info, content)
            
            # Parse VLANs
            self._parse_vlans(device_info, content)
            
            # Parse hostname
            hostname_match = re.search(r'hostname\s+(\S+)', content)
            if hostname_match:
                device_info['hostname'] = hostname_match.group(1)
            
            self.devices[device_name] = device_info
            
        except Exception as e:
            logger.error(f"Error parsing {config_file}: {str(e)}")
    
    def _determine_device_type(self, device_name: str) -> str:
        """Determine if device is router or switch"""
        if device_name.lower().startswith('r'):
            return 'router'
        elif device_name.lower().startswith('s'):
            return 'switch'
        else:
            return 'unknown'
    
    def _parse_interfaces(self, device_info: Dict, content: str):
        """Parse interface configurations"""
        interface_blocks = re.findall(r'interface\s+(\S+)(.*?)(?=interface|\Z)', content, re.DOTALL)
        
        for interface_name, interface_config in interface_blocks:
            interface_info = {
                'name': interface_name,
                'ip_address': None,
                'subnet_mask': None,
                'bandwidth': None,
                'mtu': 1500,  # default
                'vlan': None,
                'status': 'up'
            }
            
            # Parse IP address
            ip_match = re.search(r'ip\s+address\s+(\S+)\s+(\S+)', interface_config)
            if ip_match:
                interface_info['ip_address'] = ip_match.group(1)
                interface_info['subnet_mask'] = ip_match.group(2)
            
            # Parse bandwidth
            bw_match = re.search(r'bandwidth\s+(\d+)', interface_config)
            if bw_match:
                interface_info['bandwidth'] = int(bw_match.group(1))
            
            # Parse MTU
            mtu_match = re.search(r'mtu\s+(\d+)', interface_config)
            if mtu_match:
                interface_info['mtu'] = int(mtu_match.group(1))
            
            # Parse VLAN
            vlan_match = re.search(r'switchport\s+access\s+vlan\s+(\d+)', interface_config)
            if vlan_match:
                interface_info['vlan'] = int(vlan_match.group(1))
            
            # Check if interface is shutdown
            if 'shutdown' in interface_config:
                interface_info['status'] = 'down'
            
            device_info['interfaces'][interface_name] = interface_info
            
            # Store in global interfaces dict for topology building
            if interface_info['ip_address']:
                self.interfaces[f"{device_info['name']}_{interface_name}"] = {
                    'device': device_info['name'],
                    'interface': interface_name,
                    **interface_info
                }
    
    def _parse_routing_protocols(self, device_info: Dict, content: str):
        """Parse routing protocol configurations"""
        # OSPF
        if re.search(r'router\s+ospf', content):
            ospf_match = re.search(r'router\s+ospf\s+(\d+)', content)
            process_id = ospf_match.group(1) if ospf_match else "1"
            device_info['routing_protocols'].append({
                'protocol': 'ospf',
                'process_id': process_id
            })
        
        # BGP
        bgp_match = re.search(r'router\s+bgp\s+(\d+)', content)
        if bgp_match:
            device_info['routing_protocols'].append({
                'protocol': 'bgp',
                'as_number': bgp_match.group(1)
            })
    
    def _parse_vlans(self, device_info: Dict, content: str):
        """Parse VLAN configurations"""
        vlan_matches = re.findall(r'vlan\s+(\d+)\s+name\s+(\S+)', content)
        for vlan_id, vlan_name in vlan_matches:
            device_info['vlans'][int(vlan_id)] = {
                'id': int(vlan_id),
                'name': vlan_name
            }
