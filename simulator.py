import threading
import time
import queue
import json
import networkx as nx 
from typing import Dict, List
from utils import setup_logging

logger = setup_logging()

class NetworkDevice(threading.Thread):
    """Base class for network devices (routers/switches)"""
    
    def __init__(self, name: str, device_type: str, config: Dict):
        super().__init__()
        self.name = name
        self.device_type = device_type
        self.config = config
        self.running = False
        self.paused = False
        
        # Communication queues
        self.message_queue = queue.Queue()
        self.neighbors = {}
        
        # Statistics
        self.stats = {
            'packets_sent': 0,
            'packets_received': 0,
            'errors': 0,
            'uptime': 0
        }
        
        # Routing table
        self.routing_table = {}
        self.arp_table = {}
        
        logger.info(f"Initialized {device_type} {name}")
    
    def run(self):
        """Main thread execution"""
        self.running = True
        start_time = time.time()
        
        logger.info(f"{self.name} starting...")
        
        # Day-1 initialization
        self.day1_initialization()
        
        while self.running:
            if not self.paused:
                try:
                    # Process incoming messages
                    self.process_messages()
                    
                    # Send periodic updates
                    self.send_periodic_updates()
                    
                    # Update statistics
                    self.stats['uptime'] = time.time() - start_time
                    
                except Exception as e:
                    logger.error(f"{self.name} error: {str(e)}")
                    self.stats['errors'] += 1
            
            time.sleep(0.1)  # Small delay to prevent busy waiting
        
        logger.info(f"{self.name} stopped")
    
    def day1_initialization(self):
        """Perform Day-1 network initialization"""
        logger.info(f"{self.name} performing Day-1 initialization")
        
        # Send ARP requests for directly connected networks
        self.send_arp_requests()
        
        # Start routing protocol processes
        self.start_routing_protocols()
        
        # Discover neighbors
        self.discover_neighbors()
    
    def send_arp_requests(self):
        """Send ARP requests for neighbor discovery"""
        for interface_name, interface in self.config.get('interfaces', {}).items():
            if interface.get('ip_address') and interface.get('status') == 'up':
                message = {
                    'type': 'arp_request',
                    'source': self.name,
                    'interface': interface_name,
                    'ip': interface['ip_address'],
                    'timestamp': time.time()
                }
                self.broadcast_message(message)
                logger.debug(f"{self.name} sent ARP request for {interface['ip_address']}")
    
    def start_routing_protocols(self):
        """Initialize routing protocols"""
        for protocol in self.config.get('routing_protocols', []):
            if protocol['protocol'] == 'ospf':
                self.start_ospf(protocol)
            elif protocol['protocol'] == 'bgp':
                self.start_bgp(protocol)
    
    def start_ospf(self, config: Dict):
        """Start OSPF process"""
        message = {
            'type': 'ospf_hello',
            'source': self.name,
            'process_id': config.get('process_id', '1'),
            'timestamp': time.time()
        }
        self.broadcast_message(message)
        logger.debug(f"{self.name} started OSPF process {config.get('process_id', '1')}")
    
    def start_bgp(self, config: Dict):
        """Start BGP process"""
        message = {
            'type': 'bgp_open',
            'source': self.name,
            'as_number': config.get('as_number'),
            'timestamp': time.time()
        }
        self.broadcast_message(message)
        logger.debug(f"{self.name} started BGP AS {config.get('as_number')}")
    
    def discover_neighbors(self):
        """Discover and establish neighbor relationships"""
        message = {
            'type': 'neighbor_discovery',
            'source': self.name,
            'device_type': self.device_type,
            'timestamp': time.time()
        }
        self.broadcast_message(message)
    
    def process_messages(self):
        """Process incoming messages"""
        try:
            while not self.message_queue.empty():
                message = self.message_queue.get_nowait()
                self.handle_message(message)
                self.stats['packets_received'] += 1
        except queue.Empty:
            pass
    
    def handle_message(self, message: Dict):
        """Handle different types of messages"""
        msg_type = message.get('type')
        
        if msg_type == 'arp_request':
            self.handle_arp_request(message)
        elif msg_type == 'ospf_hello':
            self.handle_ospf_hello(message)
        elif msg_type == 'bgp_open':
            self.handle_bgp_open(message)
        elif msg_type == 'neighbor_discovery':
            self.handle_neighbor_discovery(message)
        else:
            logger.debug(f"{self.name} received unknown message type: {msg_type}")
    
    def handle_arp_request(self, message: Dict):
        """Handle ARP request"""
        # Simplified ARP handling
        if message['source'] != self.name:
            self.arp_table[message['ip']] = message['source']
            logger.debug(f"{self.name} learned ARP entry: {message['ip']} -> {message['source']}")
    
    def handle_ospf_hello(self, message: Dict):
        """Handle OSPF Hello message"""
        if message['source'] != self.name:
            self.neighbors[message['source']] = {
                'type': 'ospf',
                'last_seen': time.time(),
                'process_id': message.get('process_id')
            }
            logger.debug(f"{self.name} established OSPF neighbor with {message['source']}")
    
    def handle_bgp_open(self, message: Dict):
        """Handle BGP Open message"""
        if message['source'] != self.name:
            self.neighbors[message['source']] = {
                'type': 'bgp',
                'last_seen': time.time(),
                'as_number': message.get('as_number')
            }
            logger.debug(f"{self.name} established BGP neighbor with {message['source']}")
    
    def handle_neighbor_discovery(self, message: Dict):
        """Handle neighbor discovery message"""
        if message['source'] != self.name:
            self.neighbors[message['source']] = {
                'type': 'general',
                'device_type': message.get('device_type'),
                'last_seen': time.time()
            }
            logger.debug(f"{self.name} discovered neighbor {message['source']}")
    
    def send_periodic_updates(self):
        """Send periodic routing updates"""
        # Simplified - send updates every 30 seconds
        if hasattr(self, '_last_update'):
            if time.time() - self._last_update < 30:
                return
        
        self._last_update = time.time()
        
        # Send routing updates to neighbors
        for neighbor in self.neighbors:
            message = {
                'type': 'routing_update',
                'source': self.name,
                'routing_table': self.routing_table,
                'timestamp': time.time()
            }
            self.send_message_to_neighbor(neighbor, message)
    
    def broadcast_message(self, message: Dict):
        """Broadcast message to all neighbors"""
        for neighbor_name in self.neighbors:
            self.send_message_to_neighbor(neighbor_name, message)
        self.stats['packets_sent'] += len(self.neighbors)
    
    def send_message_to_neighbor(self, neighbor_name: str, message: Dict):
        """Send message to specific neighbor"""
        # This would be implemented with actual IPC in a real system
        # For simulation, we'll just log it
        logger.debug(f"{self.name} -> {neighbor_name}: {message['type']}")
        self.stats['packets_sent'] += 1
    
    def inject_fault(self, fault_type: str, **kwargs):
        """Inject fault for testing"""
        logger.info(f"Injecting fault '{fault_type}' on {self.name}")
        
        if fault_type == 'interface_down':
            interface = kwargs.get('interface')
            if interface in self.config.get('interfaces', {}):
                self.config['interfaces'][interface]['status'] = 'down'
                logger.info(f"{self.name} interface {interface} is now down")
        
        elif fault_type == 'device_failure':
            self.running = False
            logger.info(f"{self.name} device failed")
    
    def pause(self):
        """Pause device operation"""
        self.paused = True
        logger.info(f"{self.name} paused")
    
    def resume(self):
        """Resume device operation"""
        self.paused = False
        logger.info(f"{self.name} resumed")
    
    def stop(self):
        """Stop device operation"""
        self.running = False
        logger.info(f"{self.name} stopping")
    
    def get_statistics(self) -> Dict:
        """Get device statistics"""
        return {
            'name': self.name,
            'type': self.device_type,
            'stats': self.stats.copy(),
            'neighbors': len(self.neighbors),
            'routing_entries': len(self.routing_table),
            'arp_entries': len(self.arp_table)
        }


class NetworkSimulator:
    """Main network simulation engine"""
    
    def __init__(self):
        self.devices = {}
        self.running = False
        self.paused = False
        
    def load_topology(self, parsed_data: Dict):
        """Load network topology and create device threads"""
        logger.info("Loading topology into simulator...")
        
        devices_config = parsed_data['devices']
        
        for device_name, device_config in devices_config.items():
            device = NetworkDevice(
                device_name,
                device_config['type'],
                device_config
            )
            self.devices[device_name] = device
        
        # Set up neighbor relationships based on topology
        self._setup_neighbor_relationships(parsed_data)
        
        logger.info(f"Loaded {len(self.devices)} devices")
    
    def _setup_neighbor_relationships(self, parsed_data: Dict):
        """Set up neighbor relationships between devices"""
        interfaces = parsed_data['interfaces']
        
        # Group interfaces by network
        networks = {}
        for interface_key, interface in interfaces.items():
            if interface['ip_address']:
                network_key = f"{interface['ip_address']}/{interface['subnet_mask']}"
                if network_key not in networks:
                    networks[network_key] = []
                networks[network_key].append(interface['device'])
        
        # Set up neighbors for each device
        for network_devices in networks.values():
            for device1 in network_devices:
                for device2 in network_devices:
                    if device1 != device2 and device1 in self.devices and device2 in self.devices:
                        self.devices[device1].neighbors[device2] = {
                            'type': 'direct',
                            'last_seen': time.time()
                        }
    
    def start_simulation(self):
        """Start network simulation"""
        if self.running:
            logger.warning("Simulation already running")
            return
        
        logger.info("Starting network simulation...")
        self.running = True
        
        # Start all device threads
        for device in self.devices.values():
            device.start()
        
        logger.info("Network simulation started")
    
    def pause_simulation(self):
        """Pause simulation"""
        logger.info("Pausing simulation...")
        self.paused = True
        
        for device in self.devices.values():
            device.pause()
    
    def resume_simulation(self):
        """Resume simulation"""
        logger.info("Resuming simulation...")
        self.paused = False
        
        for device in self.devices.values():
            device.resume()
    
    def stop_simulation(self):
        """Stop simulation"""
        logger.info("Stopping simulation...")
        self.running = False
        
        for device in self.devices.values():
            device.stop()
            device.join(timeout=5)  # Wait for thread to finish
    
    def inject_fault(self, device_name: str, fault_type: str, **kwargs):
        """Inject fault into specific device"""
        if device_name in self.devices:
            self.devices[device_name].inject_fault(fault_type, **kwargs)
        else:
            logger.error(f"Device {device_name} not found")
    
    def get_simulation_statistics(self) -> Dict:
        """Get comprehensive simulation statistics"""
        stats = {
            'simulation_running': self.running,
            'simulation_paused': self.paused,
            'total_devices': len(self.devices),
            'device_statistics': {}
        }
        
        for device_name, device in self.devices.items():
            stats['device_statistics'][device_name] = device.get_statistics()
        
        return stats
