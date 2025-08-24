from typing import Dict, List
from utils import setup_logging

logger = setup_logging()

class LoadBalancer:
    def __init__(self):
        self.traffic_demands = {}
        self.overloaded_links = []
        
    def analyze_traffic_load(self, topology, traffic_config: Dict = None) -> Dict:
        """Analyze traffic load and suggest load balancing strategies"""
        logger.info("Analyzing traffic load...")
        
        graph = topology.graph
        
        # If no traffic config provided, use default assumptions
        if not traffic_config:
            traffic_config = self._generate_default_traffic()
        
        self.traffic_demands = traffic_config
        
        # Check each link capacity
        link_analysis = {}
        for edge in graph.edges(data=True):
            link_id = f"{edge[0]}-{edge[1]}"
            bandwidth = edge[2]['bandwidth']
            
            # Estimate traffic demand (simplified)
            estimated_demand = self._estimate_link_demand(edge[0], edge[1], traffic_config)
            utilization = estimated_demand / bandwidth if bandwidth > 0 else 0
            
            link_analysis[link_id] = {
                'bandwidth': bandwidth,
                'demand': estimated_demand,
                'utilization': utilization,
                'status': 'overloaded' if utilization > 0.8 else 'normal'
            }
            
            if utilization > 0.8:
                self.overloaded_links.append({
                    'link': link_id,
                    'utilization': utilization,
                    'bandwidth': bandwidth,
                    'demand': estimated_demand
                })
        
        # Generate recommendations
        recommendations = self._generate_load_balancing_recommendations(topology, link_analysis)
        
        return {
            'link_analysis': link_analysis,
            'overloaded_links': self.overloaded_links,
            'recommendations': recommendations
        }
    
    def _generate_default_traffic(self) -> Dict:
        """Generate default traffic assumptions"""
        return {
            'endpoint_traffic': {
                'web_server': 50000,    # 50 Mbps
                'database': 30000,      # 30 Mbps  
                'user_devices': 5000,   # 5 Mbps per device
                'backup_server': 20000  # 20 Mbps
            },
            'application_types': {
                'web': {'priority': 'medium', 'burst_factor': 2.0},
                'database': {'priority': 'high', 'burst_factor': 1.5},
                'backup': {'priority': 'low', 'burst_factor': 1.2}
            }
        }
    
    def _estimate_link_demand(self, node1: str, node2: str, traffic_config: Dict) -> int:
        """Estimate traffic demand on a link (simplified calculation)"""
        # This is a simplified estimation - in real scenarios, you'd use
        # traffic matrices, flow analysis, etc.
        base_demand = 10000  # 10 Mbps base
        
        # Add demands based on node types and positions
        if 'R' in node1 or 'R' in node2:  # Router involved
            base_demand += 20000
        
        if 'core' in str(node1).lower() or 'core' in str(node2).lower():
            base_demand += 30000
        
        return base_demand
    
    def _generate_load_balancing_recommendations(self, topology, link_analysis: Dict) -> List[Dict]:
        """Generate load balancing recommendations"""
        recommendations = []
        
        for overloaded in self.overloaded_links:
            link_name = overloaded['link']
            nodes = link_name.split('-')
            
            # Find alternative paths
            alt_paths = topology.get_alternative_paths(nodes[0], nodes[1], k=3)
            
            if len(alt_paths) > 1:
                recommendations.append({
                    'type': 'load_balancing',
                    'overloaded_link': link_name,
                    'utilization': overloaded['utilization'],
                    'recommendation': f"Distribute traffic across alternative paths",
                    'alternative_paths': alt_paths[1:],  # Exclude primary path
                    'suggested_action': "Implement ECMP (Equal Cost Multi-Path) routing"
                })
            else:
                recommendations.append({
                    'type': 'capacity_upgrade',
                    'overloaded_link': link_name,
                    'utilization': overloaded['utilization'],
                    'recommendation': f"Upgrade link capacity",
                    'current_bandwidth': overloaded['bandwidth'],
                    'suggested_bandwidth': int(overloaded['demand'] * 1.5),
                    'suggested_action': "Increase link bandwidth or add parallel links"
                })
        
        # QoS recommendations
        if self.overloaded_links:
            recommendations.append({
                'type': 'qos',
                'recommendation': "Implement Quality of Service (QoS) policies",
                'suggested_action': "Prioritize critical traffic and limit non-essential traffic",
                'priority_classes': [
                    "High: Database and critical applications",
                    "Medium: Web traffic and user applications", 
                    "Low: Backup and maintenance traffic"
                ]
            })
        
        return recommendations
