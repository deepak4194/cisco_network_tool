import matplotlib.pyplot as plt
import networkx as nx
from typing import Dict
import os
import math 
from utils import setup_logging
import matplotlib.patches as mpatches

logger = setup_logging()

class NetworkVisualizer:
    def __init__(self):
        self.device_colors = {
            'router': '#FF6B6B',      # Red for routers
            'switch': '#4ECDC4',      # Teal for switches  
            'pc': '#95A5A6',          # Gray for PCs
            'server': '#9B59B6',      # Purple for servers
            'laptop': '#F39C12',      # Orange for laptops
            'unknown': '#BDC3C7'      # Light gray for unknown
        }
        
        self.device_shapes = {
            'router': 's',    # Square for routers
            'switch': 'o',    # Circle for switches
            'pc': '^',        # Triangle for PCs
            'server': 'D',    # Diamond for servers
            'laptop': 'v',    # Inverted triangle for laptops
            'unknown': 'o'    # Circle for unknown
        }

    def _determine_device_type(self, device_name: str, device_info: Dict = None) -> str:
        """Determine device type from name and configuration"""
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
        elif device_info and device_info.get('type'):
            return device_info['type']
        else:
            return 'unknown'

    def _create_packet_tracer_layout(self, graph, devices: Dict) -> Dict:
        """Create hierarchical layout with better spacing"""
        
        # Categorize devices by type
        routers = []
        switches = []
        end_devices = []
        
        for device_name, device_info in devices.items():
            if device_name not in graph.nodes():
                continue
                
            device_type = self._determine_device_type(device_name, device_info)
            
            if device_type == 'router':
                routers.append(device_name)
            elif device_type == 'switch':
                switches.append(device_name)
            else:
                end_devices.append(device_name)
        
        pos = {}
        
        # Position routers at the top with more spacing (Core layer)
        router_y = 6  # Moved higher
        if routers:
            router_spacing = 5.0 if len(routers) > 1 else 0  # Increased spacing
            start_x = -(len(routers) - 1) * router_spacing / 2
            for i, router in enumerate(routers):
                pos[router] = (start_x + i * router_spacing, router_y)
        
        # Position switches in the middle with more spacing
        switch_y = 3  # More separation from routers
        if switches:
            switch_spacing = 4.0 if len(switches) > 1 else 0  # Increased spacing
            start_x = -(len(switches) - 1) * switch_spacing / 2
            for i, switch in enumerate(switches):
                pos[switch] = (start_x + i * switch_spacing, switch_y)
        
        # Position end devices at the bottom with more spacing
        end_y = 0
        if end_devices:
            end_spacing = 2.5 if len(end_devices) > 1 else 0  # Increased spacing
            start_x = -(len(end_devices) - 1) * end_spacing / 2
            for i, device in enumerate(end_devices):
                pos[device] = (start_x + i * end_spacing, end_y)
        
        return pos

    def _create_clean_edge_labels(self, graph, interfaces: Dict = None) -> Dict:
        """Create clean, non-overlapping edge labels"""
        edge_labels = {}
        
        for edge in graph.edges(data=True):
            device1, device2 = edge[0], edge[1]
            int1 = edge[2].get('interface1', '')
            int2 = edge[2].get('interface2', '')
            
            # Determine connection type for better labeling
            device1_type = self._determine_device_type(device1)
            device2_type = self._determine_device_type(device2)
            
            if int1 and int2:
                # Simplify interface names
                int1_short = int1.replace('FastEthernet', 'Fa').replace('GigabitEthernet', 'Gi')
                int2_short = int2.replace('FastEthernet', 'Fa').replace('GigabitEthernet', 'Gi')
                
                # For router-to-router connections, use shorter labels
                if device1_type == 'router' and device2_type == 'router':
                    edge_labels[(device1, device2)] = f"{int1_short}\n{int2_short}"  # Use newline
                else:
                    edge_labels[(device1, device2)] = f"{int1_short}↔{int2_short}"
            else:
                # Use bandwidth as fallback
                bandwidth = edge[2].get('bandwidth', 100000)
                if bandwidth >= 1000000:
                    edge_labels[(device1, device2)] = f"{bandwidth//1000000}G"
                else:
                    edge_labels[(device1, device2)] = f"{bandwidth//1000}k"
        
        return edge_labels

    def visualize_topology(self, topology, devices: Dict, save_path: str = "network_topology.png"):
        """Create improved Packet Tracer style topology with better spacing"""
        
        plt.figure(figsize=(16, 12))  # Larger figure for more space
        graph = topology.graph
        
        # Create layout with better spacing
        pos = self._create_packet_tracer_layout(graph, devices)
        
        # Create clean edge labels
        edge_labels = self._create_clean_edge_labels(graph)
        
        # Draw connections with color coding
        edge_colors = []
        edge_widths = []
        
        for edge in graph.edges(data=True):
            bandwidth = edge[2].get('bandwidth', 100000)
            if bandwidth >= 1000000:
                edge_colors.append('#2ECC71')  # Green for high bandwidth
                edge_widths.append(4)
            elif bandwidth >= 100000:
                edge_colors.append('#F39C12')  # Orange for medium bandwidth
                edge_widths.append(3)
            else:
                edge_colors.append('#E74C3C')  # Red for low bandwidth
                edge_widths.append(2)
        
        # Draw edges
        nx.draw_networkx_edges(graph, pos, edge_color=edge_colors, 
                              width=edge_widths, alpha=0.8)
        
        # Draw nodes by device type with larger sizes
        for device_type, color in self.device_colors.items():
            device_nodes = []
            for device_name, device_info in devices.items():
                if (device_name in graph.nodes() and 
                    self._determine_device_type(device_name, device_info) == device_type):
                    device_nodes.append(device_name)
            
            if device_nodes:
                node_size = 2500 if device_type == 'router' else 2000 if device_type == 'switch' else 1500
                nx.draw_networkx_nodes(graph, pos, nodelist=device_nodes,
                                     node_color=color, 
                                     node_shape=self.device_shapes.get(device_type, 'o'),
                                     node_size=node_size, alpha=0.9)
        
        # Draw device labels with better formatting
        label_pos = {}
        for node, (x, y) in pos.items():
            label_pos[node] = (x, y + 0.3)  # Slightly offset labels
        
        nx.draw_networkx_labels(graph, label_pos, font_size=12, font_weight='bold', 
                               font_color='black')
        
        # Draw edge labels with better formatting
        nx.draw_networkx_edge_labels(graph, pos, edge_labels, font_size=10, 
                                    font_weight='bold',
                                    bbox=dict(boxstyle='round,pad=0.3', 
                                             facecolor='lightyellow', 
                                             edgecolor='gray',
                                             alpha=0.9),
                                    verticalalignment='center',
                                    horizontalalignment='center')
        
        # Add comprehensive legend
        legend_elements = []
        
        # Device type legend
        for device_type, color in self.device_colors.items():
            has_device = any(self._determine_device_type(name, info) == device_type 
                           for name, info in devices.items() if name in graph.nodes())
            if has_device:
                legend_elements.append(mpatches.Patch(color=color, label=device_type.title()))
        
        # Bandwidth legend
        legend_elements.extend([
            plt.Line2D([0], [0], color='#2ECC71', lw=4, label='High BW (≥1Gbps)'),
            plt.Line2D([0], [0], color='#F39C12', lw=3, label='Medium BW (≥100Mbps)'),
            plt.Line2D([0], [0], color='#E74C3C', lw=2, label='Low BW (<100Mbps)')
        ])
        
        plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1),
                  fontsize=11, frameon=True, fancybox=True, shadow=True)
        
        # Add layer labels with better positioning
        layer_positions = {
            'CORE\nLAYER': (-8, 6),
            'DISTRIBUTION/\nACCESS LAYER': (-8, 3),
            'END\nDEVICES': (-8, 0)
        }
        
        layer_colors = {
            'CORE\nLAYER': 'lightcoral',
            'DISTRIBUTION/\nACCESS LAYER': 'lightblue', 
            'END\nDEVICES': 'lightgreen'
        }
        
        for label, (x, y) in layer_positions.items():
            if any(abs(pos[node][1] - y) < 0.5 for node in pos):
                plt.text(x, y, label, fontsize=12, fontweight='bold', 
                        ha='center', va='center',
                        bbox=dict(boxstyle='round,pad=0.5', 
                                 facecolor=layer_colors[label], 
                                 alpha=0.8, edgecolor='black'))
        
        plt.title("Network Topology - Cisco Packet Tracer Style", 
                 size=18, weight='bold', pad=20)
        plt.axis('off')
        
        # Set proper limits to show all elements clearly
        all_x = [pos[node][0] for node in pos]
        all_y = [pos[node][1] for node in pos]
        plt.xlim(min(all_x) - 3, max(all_x) + 3)
        plt.ylim(min(all_y) - 1.5, max(all_y) + 1.5)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        logger.info(f"Improved topology saved to {save_path}")
        
        return save_path

    def visualize_hierarchy(self, topology, save_path: str = "network_hierarchy.png"):
        """Visualize network hierarchy with improved spacing"""
        
        plt.figure(figsize=(16, 10))  # Larger figure
        
        graph = topology.graph
        hierarchy = topology.hierarchy
        
        # Create hierarchical positions with more spacing
        pos = {}
        layer_y = {'core': 4, 'distribution': 2.5, 'access': 1}
        layer_colors = {'core': '#E74C3C', 'distribution': '#F39C12', 'access': '#27AE60'}
        
        for layer_name, devices in hierarchy.items():
            if devices:
                y_pos = layer_y[layer_name]
                # Increase spacing between devices
                if len(devices) == 1:
                    pos[devices[0]] = (0, y_pos)
                else:
                    x_spacing = 6.0 / max(len(devices) - 1, 1)  # Increased spacing
                    start_x = -3.0
                    for i, device in enumerate(devices):
                        pos[device] = (start_x + i * x_spacing, y_pos)
        
        # Draw nodes by hierarchy layer with larger sizes
        for layer_name, devices in hierarchy.items():
            if devices:
                nx.draw_networkx_nodes(graph, pos, nodelist=devices,
                                     node_color=layer_colors[layer_name],
                                     node_size=2500, alpha=0.9)
        
        # Draw edges
        nx.draw_networkx_edges(graph, pos, alpha=0.7, width=3, edge_color='gray')
        
        # Draw labels
        nx.draw_networkx_labels(graph, pos, font_size=14, font_weight='bold', 
                               font_color='white')
        
        # Add layer labels with better positioning
        for layer_name, y_pos in layer_y.items():
            if hierarchy[layer_name]:
                plt.text(-4.5, y_pos, layer_name.upper(), fontsize=16, 
                        fontweight='bold', ha='center', va='center',
                        bbox=dict(boxstyle='round,pad=0.6', 
                                 facecolor=layer_colors[layer_name], 
                                 alpha=0.8, edgecolor='black'))
        
        # Add legend
        legend_elements = []
        for layer_name, color in layer_colors.items():
            if hierarchy[layer_name]:
                legend_elements.append(mpatches.Patch(color=color, label=layer_name.title()))
        
        plt.legend(handles=legend_elements, loc='upper right', fontsize=12,
                  frameon=True, fancybox=True, shadow=True)
        
        plt.title("Network Hierarchy", size=18, weight='bold', pad=20)
        plt.axis('off')
        plt.xlim(-5.5, 5.5)
        plt.ylim(0, 5)
        plt.tight_layout()
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        logger.info(f"Improved hierarchy visualization saved to {save_path}")
        
        return save_path

    def visualize_load_analysis(self, load_analysis: Dict, save_path: str = "load_analysis.png"):
        """Visualize network load analysis with better formatting"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        link_analysis = load_analysis['link_analysis']
        
        # Plot 1: Link Utilization
        links = list(link_analysis.keys())
        utilizations = [link_analysis[link]['utilization'] for link in links]
        
        colors = ['#E74C3C' if u > 0.8 else '#F39C12' if u > 0.6 else '#27AE60' 
                 for u in utilizations]
        
        bars1 = ax1.bar(range(len(links)), utilizations, color=colors, alpha=0.8, width=0.6)
        ax1.set_xlabel('Network Links', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Utilization (%)', fontsize=12, fontweight='bold')
        ax1.set_title('Link Utilization Analysis', fontsize=14, fontweight='bold')
        ax1.set_xticks(range(len(links)))
        ax1.set_xticklabels([link.replace('-', '\n') for link in links], 
                           rotation=0, ha='center', fontsize=10)
        ax1.axhline(y=0.8, color='red', linestyle='--', alpha=0.7, 
                   linewidth=2, label='Overload Threshold (80%)')
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Bandwidth vs Demand
        bandwidths = [link_analysis[link]['bandwidth']/1000 for link in links]
        demands = [link_analysis[link]['demand']/1000 for link in links]
        
        x_pos = range(len(links))
        width = 0.35
        
        bars2 = ax2.bar([x - width/2 for x in x_pos], bandwidths, width, 
                       label='Available Bandwidth', alpha=0.8, color='#3498DB')
        bars3 = ax2.bar([x + width/2 for x in x_pos], demands, width,
                       label='Traffic Demand', alpha=0.8, color='#E67E22')
        
        ax2.set_xlabel('Network Links', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Bandwidth (Mbps)', fontsize=12, fontweight='bold')
        ax2.set_title('Bandwidth vs Demand Analysis', fontsize=14, fontweight='bold')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels([link.replace('-', '\n') for link in links], 
                           rotation=0, ha='center', fontsize=10)
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        logger.info(f"Load analysis visualization saved to {save_path}")
        
        return save_path
