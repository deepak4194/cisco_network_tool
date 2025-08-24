import networkx as nx
from typing import Dict, List, Tuple
from utils import setup_logging, is_same_network

logger = setup_logging()

class TopologyBuilder:
    def __init__(self):
        self.graph = nx.Graph()
        self.hierarchy = {'core': [], 'distribution': [], 'access': []}
        
    def build_topology(self, parsed_data: Dict) -> nx.Graph:
        """Build network topology from parsed configuration data"""
        devices = parsed_data['devices']
        interfaces = parsed_data['interfaces']
        
        logger.info("Building network topology...")
        
        # Add nodes (devices)
        for device_name, device_info in devices.items():
            self.graph.add_node(device_name, **device_info)
        
        # Add edges (connections) based on IP networks - FIXED VERSION
        self._add_connections(interfaces)
        
        # Determine hierarchy
        self._determine_hierarchy(devices)
        
        # Calculate shortest paths
        self._calculate_paths()
        
        logger.info(f"Topology built: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges")
        return self.graph
    
    def _add_connections(self, interfaces: Dict):
        """Add connections between devices based on IP networks - FIXED VERSION"""
        interface_list = list(interfaces.values())
        
        for i, int1 in enumerate(interface_list):
            for int2 in interface_list[i+1:]:
                if (int1['ip_address'] and int2['ip_address'] and 
                    int1['device'] != int2['device']):
                    
                    # Check if they're in the same network
                    if is_same_network(int1['ip_address'], int2['ip_address'], 
                                     int1['subnet_mask']):
                        
                        # IMPORTANT: Only connect if at least one is a router or switch
                        device1_type = self._get_device_type(int1['device'])
                        device2_type = self._get_device_type(int2['device'])
                        
                        # Only create connections between:
                        # 1. Router to Router
                        # 2. Router to Switch  
                        # 3. Switch to End Device
                        # NOT End Device to End Device
                        should_connect = False
                        
                        if (device1_type == 'router' and device2_type == 'router'):
                            should_connect = True  # Router-to-router WAN links
                        elif (device1_type == 'router' and device2_type == 'switch'):
                            should_connect = True  # Router-to-switch connections
                        elif (device1_type == 'switch' and device2_type == 'router'):
                            should_connect = True  # Switch-to-router connections
                        elif (device1_type == 'switch' and 
                              device2_type in ['pc', 'server', 'laptop', 'unknown']):
                            should_connect = True  # Switch-to-end-device
                        elif (device1_type in ['pc', 'server', 'laptop', 'unknown'] and 
                              device2_type == 'switch'):
                            should_connect = True  # End-device-to-switch
                        
                        if should_connect:
                            # Calculate link bandwidth
                            bw1 = int1['bandwidth'] or 100000
                            bw2 = int2['bandwidth'] or 100000
                            link_bandwidth = min(bw1, bw2)
                            
                            self.graph.add_edge(
                                int1['device'], 
                                int2['device'],
                                bandwidth=link_bandwidth,
                                interface1=int1['interface'],
                                interface2=int2['interface'],
                                mtu1=int1['mtu'],
                                mtu2=int2['mtu'],
                                weight=1.0/link_bandwidth
                            )
                            
                            logger.info(f"Connected {int1['device']} to {int2['device']} "
                                      f"(BW: {link_bandwidth})")

    def _get_device_type(self, device_name: str) -> str:
        """Helper method to determine device type"""
        name_lower = device_name.lower()
        if name_lower.startswith('r') and len(device_name) <= 3:
            return 'router'
        elif name_lower.startswith('switch') or name_lower.startswith('sw'):
            return 'switch'
        elif name_lower.startswith('pc'):
            return 'pc'
        elif name_lower.startswith('server'):
            return 'server'
        elif name_lower.startswith('laptop'):
            return 'laptop'
        else:
            return 'unknown'
    
    def _determine_hierarchy(self, devices: Dict):
        """Determine network hierarchy based on connectivity"""
        degree_centrality = nx.degree_centrality(self.graph)
        
        # Sort devices by connectivity (degree)
        sorted_devices = sorted(degree_centrality.items(), 
                              key=lambda x: x[1], reverse=True)
        
        total_devices = len(sorted_devices)
        
        for i, (device, centrality) in enumerate(sorted_devices):
            if i < total_devices * 0.2:  # Top 20% are core
                self.hierarchy['core'].append(device)
            elif i < total_devices * 0.6:  # Next 40% are distribution
                self.hierarchy['distribution'].append(device)
            else:  # Remaining are access
                self.hierarchy['access'].append(device)
        
        logger.info(f"Hierarchy - Core: {self.hierarchy['core']}, "
                   f"Distribution: {self.hierarchy['distribution']}, "
                   f"Access: {self.hierarchy['access']}")
    
    def _calculate_paths(self):
        """Calculate shortest paths between all node pairs"""
        try:
            self.shortest_paths = dict(nx.all_pairs_shortest_path(self.graph))
            logger.info("Shortest paths calculated successfully")
        except Exception as e:
            logger.error(f"Error calculating shortest paths: {str(e)}")
            self.shortest_paths = {}
    
    def get_alternative_paths(self, source: str, target: str, k: int = 3) -> List[List[str]]:
        """Get k alternative paths between source and target"""
        try:
            paths = list(nx.shortest_simple_paths(self.graph, source, target))
            return paths[:k]
        except:
            return []
    
    def get_network_info(self) -> Dict:
        """Get comprehensive network information"""
        return {
            'nodes': len(self.graph.nodes),
            'edges': len(self.graph.edges),
            'hierarchy': self.hierarchy,
            'density': nx.density(self.graph),
            'is_connected': nx.is_connected(self.graph),
            'diameter': nx.diameter(self.graph) if nx.is_connected(self.graph) else None
        }
