import networkx as nx
import re
from typing import Dict, List
from collections import defaultdict
from utils import setup_logging, is_valid_ip

logger = setup_logging()

class ConfigValidator:
    def __init__(self):
        self.issues = []
        self.warnings = []
        
    def validate_configuration(self, parsed_data: Dict, topology) -> Dict:
        """Validate network configuration and identify issues"""
        logger.info("Starting configuration validation...")
        
        devices = parsed_data['devices']
        interfaces = parsed_data['interfaces']
        
        # Run all validation checks
        self._check_duplicate_ips(interfaces)
        self._check_mtu_mismatches(topology.graph)
        self._check_missing_components(devices)
        self._check_vlan_consistency(devices)
        self._check_gateway_configuration(devices)
        self._check_network_loops(topology.graph)
        self._suggest_protocol_optimization(devices)
        self._suggest_node_aggregation(topology.graph, devices)
        
        validation_result = {
            'issues': self.issues,
            'warnings': self.warnings,
            'total_issues': len(self.issues),
            'total_warnings': len(self.warnings)
        }
        
        logger.info(f"Validation complete: {len(self.issues)} issues, "
                   f"{len(self.warnings)} warnings found")
        
        return validation_result
    
    def _check_duplicate_ips(self, interfaces: Dict):
        """Check for duplicate IP addresses in same VLAN/subnet"""
        ip_map = defaultdict(list)
        
        for interface_key, interface in interfaces.items():
            if interface['ip_address']:
                key = f"{interface['ip_address']}_{interface.get('vlan', 'default')}"
                ip_map[key].append(interface['device'])
        
        for ip_vlan, devices in ip_map.items():
            if len(devices) > 1:
                ip_addr = ip_vlan.split('_')[0]
                vlan = ip_vlan.split('_')[1]
                self.issues.append({
                    'type': 'duplicate_ip',
                    'severity': 'high',
                    'description': f"Duplicate IP {ip_addr} in VLAN {vlan}",
                    'affected_devices': devices,
                    'recommendation': "Assign unique IP addresses to each interface"
                })
    
    def _check_mtu_mismatches(self, graph):
        """Check for MTU mismatches between connected interfaces"""
        for edge in graph.edges(data=True):
            mtu1 = edge[2].get('mtu1', 1500)
            mtu2 = edge[2].get('mtu2', 1500)
            
            if mtu1 != mtu2:
                self.warnings.append({
                    'type': 'mtu_mismatch',
                    'severity': 'medium',
                    'description': f"MTU mismatch between {edge[0]} ({mtu1}) and {edge[1]} ({mtu2})",
                    'affected_devices': [edge[0], edge[1]],
                    'recommendation': f"Set consistent MTU value (recommend {max(mtu1, mtu2)})"
                })
    
    def _check_missing_components(self, devices: Dict):
        """Check for missing network components"""
        device_types = [device['type'] for device in devices.values()]
        
        if 'router' not in device_types:
            self.warnings.append({
                'type': 'missing_component',
                'severity': 'medium',
                'description': "No routers found in configuration",
                'recommendation': "Ensure router configurations are included"
            })
        
        if 'switch' not in device_types:
            self.warnings.append({
                'type': 'missing_component',
                'severity': 'low',
                'description': "No switches found in configuration",
                'recommendation': "Consider adding switch configurations for complete topology"
            })
    
    def _check_vlan_consistency(self, devices: Dict):
        """Check VLAN configuration consistency"""
        vlan_configs = defaultdict(set)
        
        for device_name, device in devices.items():
            for vlan_id, vlan_info in device.get('vlans', {}).items():
                vlan_configs[vlan_id].add(vlan_info['name'])
        
        for vlan_id, names in vlan_configs.items():
            if len(names) > 1:
                self.issues.append({
                    'type': 'vlan_inconsistency',
                    'severity': 'medium',
                    'description': f"VLAN {vlan_id} has inconsistent names: {list(names)}",
                    'recommendation': f"Use consistent name for VLAN {vlan_id}"
                })
    
    def _check_gateway_configuration(self, devices: Dict):
        """Check gateway configuration on routers"""
        for device_name, device in devices.items():
            if device['type'] == 'router':
                has_gateway = False
                for interface_name, interface in device['interfaces'].items():
                    if interface['ip_address'] and interface['ip_address'].endswith('.1'):
                        has_gateway = True
                        break
                
                if not has_gateway:
                    self.warnings.append({
                        'type': 'gateway_config',
                        'severity': 'low',
                        'description': f"Router {device_name} may not have gateway interface configured",
                        'recommendation': "Verify gateway configuration on router interfaces"
                    })
    
    def _check_network_loops(self, graph):
        """Check for potential network loops"""
        cycles = list(nx.simple_cycles(graph.to_directed()))
        
        if cycles:
            for cycle in cycles[:5]:  # Report first 5 cycles
                self.warnings.append({
                    'type': 'network_loop',
                    'severity': 'medium',
                    'description': f"Potential network loop detected: {' -> '.join(cycle)}",
                    'recommendation': "Implement STP or remove redundant connections"
                })
    
    def _suggest_protocol_optimization(self, devices: Dict):
        """Suggest routing protocol optimizations"""
        total_devices = len(devices)
        bgp_devices = sum(1 for d in devices.values() 
                         if any(p['protocol'] == 'bgp' for p in d.get('routing_protocols', [])))
        ospf_devices = sum(1 for d in devices.values() 
                          if any(p['protocol'] == 'ospf' for p in d.get('routing_protocols', [])))
        
        if total_devices > 10 and bgp_devices == 0:
            self.warnings.append({
                'type': 'protocol_optimization',
                'severity': 'low',
                'description': "Large network detected without BGP",
                'recommendation': "Consider implementing BGP for better scalability"
            })
        
        if total_devices <= 5 and bgp_devices > 0:
            self.warnings.append({
                'type': 'protocol_optimization',
                'severity': 'low',
                'description': "BGP may be overkill for small network",
                'recommendation': "OSPF might be more appropriate for this network size"
            })
    
    def _suggest_node_aggregation(self, graph, devices: Dict):
        """Suggest node aggregation opportunities"""
        for node in graph.nodes():
            neighbors = list(graph.neighbors(node))
            if len(neighbors) == 1:
                neighbor = neighbors[0]
                if (devices[node]['type'] == devices[neighbor]['type'] == 'switch'):
                    self.warnings.append({
                        'type': 'node_aggregation',
                        'severity': 'low',
                        'description': f"Switches {node} and {neighbor} could be aggregated",
                        'recommendation': f"Consider combining {node} and {neighbor} into single switch"
                    })
