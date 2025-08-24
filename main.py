#!/usr/bin/env python3
"""
Cisco Virtual Internship - Network Topology Tool
Main application entry point
"""

import argparse
import os
import sys
import time
from config_parser import ConfigParser
from topology_builder import TopologyBuilder
from validator import ConfigValidator
from load_balancer import LoadBalancer
from simulator import NetworkSimulator
from visualizer import NetworkVisualizer
from utils import setup_logging, save_json

def main():
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Cisco Network Topology Tool")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Cisco Network Topology Analysis Tool")
    parser.add_argument("config_dir", help="Directory containing device configuration files")
    parser.add_argument("--simulate", action="store_true", help="Run network simulation")
    parser.add_argument("--duration", type=int, default=60, help="Simulation duration in seconds")
    parser.add_argument("--output-dir", default="output", help="Output directory for results")
    
    args = parser.parse_args()
    
    # Validate input directory
    if not os.path.exists(args.config_dir):
        logger.error(f"Configuration directory not found: {args.config_dir}")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        # Step 1: Parse configuration files
        logger.info("=== STEP 1: Parsing Configuration Files ===")
        config_parser = ConfigParser()
        parsed_data = config_parser.parse_directory(args.config_dir)
        
        if not parsed_data['devices']:
            logger.error("No devices found in configuration directory")
            sys.exit(1)
        
        logger.info(f"Parsed {len(parsed_data['devices'])} devices")
        
        # Save parsed data
        save_json(parsed_data, os.path.join(args.output_dir, "parsed_config.json"))
        
        # Step 2: Build network topology
        logger.info("=== STEP 2: Building Network Topology ===")
        topology_builder = TopologyBuilder()
        topology = topology_builder.build_topology(parsed_data)
        
        network_info = topology_builder.get_network_info()
        logger.info(f"Network info: {network_info}")
        
        # Step 3: Validate configuration
        logger.info("=== STEP 3: Validating Configuration ===")
        validator = ConfigValidator()
        validation_results = validator.validate_configuration(parsed_data, topology_builder)
        
        logger.info(f"Found {validation_results['total_issues']} issues and "
                   f"{validation_results['total_warnings']} warnings")
        
        # Save validation results
        save_json(validation_results, os.path.join(args.output_dir, "validation_results.json"))
        
        # Print validation summary
        print("\n=== VALIDATION SUMMARY ===")
        for issue in validation_results['issues']:
            print(f"🔴 {issue['severity'].upper()}: {issue['description']}")
            print(f"   Recommendation: {issue['recommendation']}\n")
        
        for warning in validation_results['warnings']:
            print(f"🟡 {warning['severity'].upper()}: {warning['description']}")
            print(f"   Recommendation: {warning['recommendation']}\n")
        
        # Step 4: Load balancing analysis
        logger.info("=== STEP 4: Load Balancing Analysis ===")
        load_balancer = LoadBalancer()
        load_analysis = load_balancer.analyze_traffic_load(topology_builder)
        
        logger.info(f"Found {len(load_analysis['overloaded_links'])} overloaded links")
        
        # Save load analysis
        save_json(load_analysis, os.path.join(args.output_dir, "load_analysis.json"))
        
        # Print load balancing recommendations
        print("\n=== LOAD BALANCING RECOMMENDATIONS ===")
        for rec in load_analysis['recommendations']:
            print(f"📊 {rec['type'].upper()}: {rec['recommendation']}")
            print(f"   Action: {rec['suggested_action']}\n")
        
        # Step 5: Generate visualizations
        logger.info("=== STEP 5: Generating Visualizations ===")
        visualizer = NetworkVisualizer()
        
        # Generate topology visualization
        topo_path = visualizer.visualize_topology(
            topology_builder, parsed_data['devices'],
            os.path.join(args.output_dir, "network_topology.png")
        )
        
        # Generate hierarchy visualization
        hierarchy_path = visualizer.visualize_hierarchy(
            topology_builder,
            os.path.join(args.output_dir, "network_hierarchy.png")
        )
        
        # Generate load analysis visualization
        load_path = visualizer.visualize_load_analysis(
            load_analysis,
            os.path.join(args.output_dir, "load_analysis.png")
        )
        
        # Step 6: Network simulation (if requested)
        if args.simulate:
            logger.info("=== STEP 6: Network Simulation ===")
            
            simulator = NetworkSimulator()
            simulator.load_topology(parsed_data)
            
            print(f"Starting simulation for {args.duration} seconds...")
            simulator.start_simulation()
            
            # Run simulation
            try:
                # Let simulation run for specified duration
                time.sleep(args.duration // 3)
                
                # Inject a fault for testing
                print("Injecting fault: R1 interface down")
                simulator.inject_fault("R1", "interface_down", interface="eth0")
                
                # Continue simulation
                time.sleep(args.duration // 3)
                
                # Pause and resume test
                print("Pausing simulation...")
                simulator.pause_simulation()
                time.sleep(2)
                
                print("Resuming simulation...")
                simulator.resume_simulation()
                time.sleep(args.duration // 3)
                
            except KeyboardInterrupt:
                print("Simulation interrupted by user")
            
            finally:
                # Stop simulation and get statistics
                simulator.stop_simulation()
                sim_stats = simulator.get_simulation_statistics()
                
                # Save simulation results
                save_json(sim_stats, os.path.join(args.output_dir, "simulation_stats.json"))
                
                # Print simulation summary
                print("\n=== SIMULATION SUMMARY ===")
                for device_name, stats in sim_stats['device_statistics'].items():
                    print(f"📡 {device_name}: {stats['stats']['packets_sent']} sent, "
                          f"{stats['stats']['packets_received']} received, "
                          f"{stats['neighbors']} neighbors")
        
        # Final summary
        print("\n=== ANALYSIS COMPLETE ===")
        print(f"Results saved to: {args.output_dir}")
        print(f"- Configuration: parsed_config.json")
        print(f"- Validation: validation_results.json")
        print(f"- Load Analysis: load_analysis.json")
        print(f"- Topology Diagram: network_topology.png")
        print(f"- Hierarchy Diagram: network_hierarchy.png")
        print(f"- Load Analysis Chart: load_analysis.png")
        
        if args.simulate:
            print(f"- Simulation Stats: simulation_stats.json")
        
        logger.info("Analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main()
