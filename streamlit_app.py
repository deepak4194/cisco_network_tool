import streamlit as st
import os
import zipfile
import tempfile
import shutil
import time
from pathlib import Path
import io
import traceback

# Import your existing modules
from config_parser import ConfigParser
from topology_builder import TopologyBuilder
from validator import ConfigValidator
from load_balancer import LoadBalancer
from simulator import NetworkSimulator
from visualizer import NetworkVisualizer
from utils import setup_logging, save_json

def main():
    # Page configuration
    st.set_page_config(
        page_title="Cisco Network Topology Analyzer",
        page_icon="🌐",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #dc3545;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ffc107;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown('<h1 class="main-header">🌐 Cisco Network Topology Analyzer</h1>', unsafe_allow_html=True)
    
    # Project description
    st.markdown("""
    <div class="info-box">
    <h3>📋 Project Overview</h3>
    <p>This tool automatically analyzes Cisco network configurations to:</p>
    <ul>
        <li><b>🔧 Parse Configuration Files:</b> Extract device settings, interfaces, and protocols</li>
        <li><b>🗺️ Generate Network Topology:</b> Create visual network diagrams in Packet Tracer style</li>
        <li><b>✅ Validate Configurations:</b> Detect issues like duplicate IPs, MTU mismatches, and loops</li>
        <li><b>📊 Analyze Traffic Load:</b> Recommend load balancing and optimization strategies</li>
        <li><b>⚡ Simulate Network:</b> Test fault injection and Day-1 operations</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown("## ⚙️ Analysis Options")
        
        # Analysis options
        run_simulation = st.checkbox("🔄 Run Network Simulation", value=False)
        simulation_duration = st.slider("Simulation Duration (seconds)", 10, 300, 60)
        
        generate_detailed = st.checkbox("📈 Generate Detailed Reports", value=True)
        
        st.markdown("---")
        st.markdown("## 📞 Contact")
        st.markdown("**Cisco Virtual Internship 2025**")
        st.markdown("Network Topology Analysis Tool")
    
    # File upload section
    st.markdown('<h2 class="sub-header">📁 Upload Configuration Files</h2>', unsafe_allow_html=True)
    
    # Instructions
    with st.expander("📖 How to Upload Configuration Files", expanded=False):
        st.markdown("""
        ### 📝 File Naming Convention:
        Your configuration files should follow this structure:
        
        ```
        📁 Your Upload Folder/
        ├── 📁 R1/
        │   └── config.dump
        ├── 📁 R2/
        │   └── config.dump
        ├── 📁 R3/
        │   └── config.dump
        ├── 📁 Switch0/
        │   └── config.dump
        ├── 📁 Switch1/
        │   └── config.dump
        ├── 📁 PC0/
        │   └── config.dump
        └── 📁 Server0/
            └── config.dump
        ```
        
        **OR as flat files:**
        ```
        📁 Your ZIP File/
        ├── R1_config.dump
        ├── R2_config.dump
        ├── R3_config.dump
        ├── Switch0_config.dump
        └── PC0_config.dump
        ```
        
        ### 💡 Tips:
        - **Device Names:** Start routers with 'R', switches with 'Switch', PCs with 'PC', servers with 'Server'
        - **Config Files:** Each device folder must contain a `config.dump` file
        - **Upload Method:** You can upload individual files or a ZIP containing all device folders
        - **File Format:** Standard Cisco configuration format
        """)
    
    # File upload options
    upload_method = st.radio(
        "Choose upload method:",
        ["📎 Upload Individual Files", "📦 Upload ZIP File"],
        horizontal=True
    )
    
    uploaded_files = None
    config_dir = None
    
    if upload_method == "📎 Upload Individual Files":
        uploaded_files = st.file_uploader(
            "Select configuration files",
            type=['dump', 'txt', 'cfg'],
            accept_multiple_files=True,
            help="Upload multiple config.dump files. File names should indicate device (e.g., R1_config.dump, Switch0_config.dump)"
        )
    else:
        zip_file = st.file_uploader(
            "Upload ZIP file containing device folders",
            type=['zip'],
            help="Upload a ZIP file containing folders named after devices (R1, R2, Switch0, etc.) with config.dump files inside"
        )
        if zip_file:
            # Validate ZIP structure first
            st.write("🔍 **Analyzing ZIP file structure...**")
            if validate_zip_structure(zip_file):
                uploaded_files = [zip_file]
    
    # Process uploaded files
    if uploaded_files:
        with st.spinner("Processing uploaded files..."):
            config_dir = process_uploaded_files(uploaded_files, upload_method)
        
        if config_dir:
            device_count = len([d for d in os.listdir(config_dir) 
                              if os.path.isdir(os.path.join(config_dir, d))])
            st.markdown(f'<div class="success-box">✅ Successfully processed {device_count} device configurations!</div>', unsafe_allow_html=True)
            
            # Show uploaded files
            with st.expander("📋 Uploaded Device Configurations", expanded=True):
                for device_dir in os.listdir(config_dir):
                    device_path = os.path.join(config_dir, device_dir)
                    if os.path.isdir(device_path):
                        config_file = os.path.join(device_path, "config.dump")
                        if os.path.exists(config_file):
                            file_size = os.path.getsize(config_file)
                            st.success(f"✅ {device_dir} ({file_size} bytes)")
                        else:
                            st.error(f"❌ {device_dir} (missing config.dump)")
            
            # Analysis button
            if st.button("🚀 Start Network Analysis", type="primary", use_container_width=True):
                run_analysis(config_dir, run_simulation, simulation_duration, generate_detailed)
        else:
            st.markdown('<div class="error-box">❌ Failed to process uploaded files. Please check the file format and structure.</div>', unsafe_allow_html=True)

def validate_zip_structure(zip_file):
    """Validate and show ZIP file structure"""
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            contents = zip_ref.namelist()
            
            st.write("📋 **ZIP File Contents:**")
            
            # Show structure
            folders = set()
            files = []
            
            for item in contents:
                if item.endswith('/'):
                    folders.add(item.rstrip('/'))
                else:
                    files.append(item)
                    if '/' in item:
                        folder = '/'.join(item.split('/')[:-1])
                        folders.add(folder)
            
            # Display folder structure
            if folders:
                st.write("📁 **Folders found:**")
                for folder in sorted(folders):
                    st.write(f"  📁 {folder}")
            
            # Display files
            if files:
                st.write("📄 **Files found:**")
                for file in sorted(files):
                    st.write(f"  📄 {file}")
            
            return True
            
    except Exception as e:
        st.error(f"Error reading ZIP file: {str(e)}")
        return False

def process_uploaded_files(uploaded_files, upload_method):
    """Process uploaded files and create temporary directory structure"""
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        config_dir = os.path.join(temp_dir, "config")
        os.makedirs(config_dir, exist_ok=True)
        
        if upload_method == "📦 Upload ZIP File":
            # Handle ZIP file
            zip_file = uploaded_files[0]
            
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                # Get all file names in the ZIP
                zip_contents = zip_ref.namelist()
                st.write(f"🔍 Found {len(zip_contents)} items in ZIP file")  # Debug info
                
                # Check if ZIP contains folders or flat files
                has_folders = any('/' in name and not name.endswith('/') for name in zip_contents)
                
                if has_folders:
                    # ZIP contains folder structure - extract directly
                    zip_ref.extractall(config_dir)
                    
                    # Check if there's a nested folder structure
                    extracted_items = os.listdir(config_dir)
                    if len(extracted_items) == 1 and os.path.isdir(os.path.join(config_dir, extracted_items[0])):
                        # Move contents up one level if there's a single parent folder
                        parent_folder = os.path.join(config_dir, extracted_items[0])
                        if os.path.isdir(parent_folder):
                            for item in os.listdir(parent_folder):
                                shutil.move(os.path.join(parent_folder, item), 
                                          os.path.join(config_dir, item))
                            os.rmdir(parent_folder)
                
                else:
                    # ZIP contains flat files - organize them by device names
                    for file_name in zip_contents:
                        if not file_name.endswith('/'):  # Skip directories
                            # Extract device name from filename
                            base_name = os.path.basename(file_name)
                            
                            # Try different naming patterns
                            if '_' in base_name:
                                device_name = base_name.split('_')[0]
                            elif base_name.startswith(('R', 'r')) and any(char.isdigit() for char in base_name):
                                # Router naming pattern (R1, R2, etc.)
                                device_name = ''.join(filter(lambda x: x.isalpha() or x.isdigit(), base_name.split('.')[0]))
                            else:
                                device_name = base_name.replace('.dump', '').replace('.txt', '').replace('.cfg', '')
                            
                            # Create device directory
                            device_dir = os.path.join(config_dir, device_name)
                            os.makedirs(device_dir, exist_ok=True)
                            
                            # Extract and save the file
                            with zip_ref.open(file_name) as source, \
                                 open(os.path.join(device_dir, "config.dump"), "wb") as target:
                                target.write(source.read())
                            
                            st.write(f"✅ Processed {device_name} from {file_name}")  # Debug info
        
        else:
            # Handle individual files
            for uploaded_file in uploaded_files:
                # Extract device name from filename
                file_name = uploaded_file.name
                if '_' in file_name:
                    device_name = file_name.split('_')[0]
                else:
                    device_name = file_name.replace('.dump', '').replace('.txt', '').replace('.cfg', '')
                
                # Create device directory
                device_dir = os.path.join(config_dir, device_name)
                os.makedirs(device_dir, exist_ok=True)
                
                # Save config file
                config_path = os.path.join(device_dir, "config.dump")
                with open(config_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
        
        # Verify the structure
        device_count = 0
        for item in os.listdir(config_dir):
            item_path = os.path.join(config_dir, item)
            if os.path.isdir(item_path):
                config_file = os.path.join(item_path, "config.dump")
                if os.path.exists(config_file):
                    device_count += 1
        
        st.write(f"📊 Successfully created {device_count} device configurations")  # Debug info
        
        return config_dir if device_count > 0 else None
        
    except Exception as e:
        st.error(f"Error processing files: {str(e)}")
        st.error(traceback.format_exc())  # Show full error for debugging
        return None

def run_analysis(config_dir, run_simulation, simulation_duration, generate_detailed):
    """Run the complete network analysis"""
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Results containers
        results = {}
        
        # Step 1: Parse Configuration Files
        status_text.text("Step 1/6: Parsing configuration files...")
        progress_bar.progress(10)
        
        config_parser = ConfigParser()
        parsed_data = config_parser.parse_directory(config_dir)
        results['parsed_data'] = parsed_data
        
        if not parsed_data['devices']:
            st.error("❌ No devices found in configuration files!")
            return
        
        st.success(f"✅ Parsed {len(parsed_data['devices'])} devices successfully")
        
        # Step 2: Build Network Topology
        status_text.text("Step 2/6: Building network topology...")
        progress_bar.progress(25)
        
        topology_builder = TopologyBuilder()
        topology = topology_builder.build_topology(parsed_data)
        network_info = topology_builder.get_network_info()
        results['topology'] = topology_builder
        results['network_info'] = network_info
        
        st.success(f"✅ Built topology: {network_info['nodes']} nodes, {network_info['edges']} edges")
        
        # Step 3: Validate Configuration
        status_text.text("Step 3/6: Validating configurations...")
        progress_bar.progress(40)
        
        validator = ConfigValidator()
        validation_results = validator.validate_configuration(parsed_data, topology_builder)
        results['validation'] = validation_results
        
        st.success(f"✅ Found {validation_results['total_issues']} issues, {validation_results['total_warnings']} warnings")
        
        # Step 4: Load Balancing Analysis
        status_text.text("Step 4/6: Analyzing traffic load...")
        progress_bar.progress(55)
        
        load_balancer = LoadBalancer()
        load_analysis = load_balancer.analyze_traffic_load(topology_builder)
        results['load_analysis'] = load_analysis
        
        st.success(f"✅ Analyzed {len(load_analysis['link_analysis'])} network links")
        
        # Step 5: Generate Visualizations
        status_text.text("Step 5/6: Generating visualizations...")
        progress_bar.progress(70)
        
        visualizer = NetworkVisualizer()
        
        # Generate topology visualization
        topo_path = visualizer.visualize_topology(
            topology_builder, parsed_data['devices'], "network_topology.png"
        )
        
        # Generate hierarchy visualization
        hierarchy_path = visualizer.visualize_hierarchy(
            topology_builder, "network_hierarchy.png"
        )
        
        # Generate load analysis visualization
        load_path = visualizer.visualize_load_analysis(
            load_analysis, "load_analysis.png"
        )
        
        results['visualizations'] = {
            'topology': topo_path,
            'hierarchy': hierarchy_path,
            'load_analysis': load_path
        }
        
        st.success("✅ Generated network visualizations")
        
        # Step 6: Network Simulation (Optional)
        if run_simulation:
            status_text.text("Step 6/6: Running network simulation...")
            progress_bar.progress(85)
            
            simulator = NetworkSimulator()
            simulator.load_topology(parsed_data)
            simulator.start_simulation()
            
            # Run simulation for specified duration
            time.sleep(simulation_duration)
            
            # Get simulation statistics
            sim_stats = simulator.get_simulation_statistics()
            simulator.stop_simulation()
            
            results['simulation'] = sim_stats
            st.success(f"✅ Completed {simulation_duration}s network simulation")
        
        # Complete
        status_text.text("✅ Analysis completed successfully!")
        progress_bar.progress(100)
        
        # Display results
        display_results(results, generate_detailed)
        
    except Exception as e:
        st.error(f"❌ Analysis failed: {str(e)}")
        st.exception(e)

def display_results(results, generate_detailed):
    """Display analysis results in the web interface"""
    
    st.markdown("---")
    st.markdown('<h2 class="sub-header">📊 Analysis Results</h2>', unsafe_allow_html=True)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🖥️ Devices", results['network_info']['nodes'])
    
    with col2:
        st.metric("🔗 Connections", results['network_info']['edges'])
    
    with col3:
        st.metric("⚠️ Issues", results['validation']['total_issues'])
    
    with col4:
        st.metric("🚨 Warnings", results['validation']['total_warnings'])
    
    # Tabs for different result sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🗺️ Network Topology", "✅ Validation Results", "📊 Load Analysis", "📈 Network Hierarchy", "💾 Download Results"])
    
    with tab1:
        st.markdown("### Network Topology Visualization")
        if os.path.exists(results['visualizations']['topology']):
            st.image(results['visualizations']['topology'], caption="Cisco Packet Tracer Style Network Topology")
        
        # Network information
        if generate_detailed:
            st.markdown("### 📋 Network Information")
            net_info = results['network_info']
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Network Density:** {net_info['density']:.2f}")
                st.info(f"**Connected:** {'Yes' if net_info['is_connected'] else 'No'}")
            
            with col2:
                if net_info['diameter']:
                    st.info(f"**Network Diameter:** {net_info['diameter']}")
                
                # Hierarchy breakdown
                hierarchy = net_info['hierarchy']
                st.info(f"**Core Devices:** {len(hierarchy['core'])}")
                st.info(f"**Distribution:** {len(hierarchy['distribution'])}")
                st.info(f"**Access:** {len(hierarchy['access'])}")
    
    with tab2:
        st.markdown("### Configuration Validation Results")
        
        validation = results['validation']
        
        # Issues
        if validation['issues']:
            st.markdown("#### 🔴 Critical Issues")
            for issue in validation['issues']:
                st.markdown(f"""
                <div class="error-box">
                <strong>{issue['type'].replace('_', ' ').title()}:</strong> {issue['description']}<br>
                <strong>Recommendation:</strong> {issue['recommendation']}
                </div>
                """, unsafe_allow_html=True)
        
        # Warnings
        if validation['warnings']:
            st.markdown("#### 🟡 Warnings")
            for warning in validation['warnings']:
                st.markdown(f"""
                <div class="warning-box">
                <strong>{warning['type'].replace('_', ' ').title()}:</strong> {warning['description']}<br>
                <strong>Recommendation:</strong> {warning['recommendation']}
                </div>
                """, unsafe_allow_html=True)
        
        if not validation['issues'] and not validation['warnings']:
            st.success("🎉 No issues or warnings found! Your network configuration looks good.")
    
    with tab3:
        st.markdown("### Traffic Load Analysis")
        
        if os.path.exists(results['visualizations']['load_analysis']):
            st.image(results['visualizations']['load_analysis'], caption="Network Load Analysis")
        
        # Load balancing recommendations
        load_analysis = results['load_analysis']
        if load_analysis['recommendations']:
            st.markdown("#### 💡 Load Balancing Recommendations")
            for rec in load_analysis['recommendations']:
                st.markdown(f"""
                <div class="info-box">
                <strong>{rec['type'].replace('_', ' ').title()}:</strong> {rec['recommendation']}<br>
                <strong>Suggested Action:</strong> {rec['suggested_action']}
                </div>
                """, unsafe_allow_html=True)
    
    with tab4:
        st.markdown("### Network Hierarchy")
        if os.path.exists(results['visualizations']['hierarchy']):
            st.image(results['visualizations']['hierarchy'], caption="Network Hierarchy Visualization")
    
    with tab5:
        st.markdown("### 💾 Download Analysis Results")
        
        # Create downloadable files
        create_download_files(results)
        
        # Download buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if os.path.exists("network_topology.png"):
                with open("network_topology.png", "rb") as file:
                    st.download_button(
                        label="📥 Download Topology Diagram",
                        data=file.read(),
                        file_name="network_topology.png",
                        mime="image/png"
                    )
        
        with col2:
            if os.path.exists("validation_report.json"):
                with open("validation_report.json", "rb") as file:
                    st.download_button(
                        label="📥 Download Validation Report",
                        data=file.read(),
                        file_name="validation_report.json",
                        mime="application/json"
                    )
        
        with col3:
            if os.path.exists("network_analysis_summary.txt"):
                with open("network_analysis_summary.txt", "rb") as file:
                    st.download_button(
                        label="📥 Download Summary Report",
                        data=file.read(),
                        file_name="network_analysis_summary.txt",
                        mime="text/plain"
                    )

def create_download_files(results):
    """Create downloadable files from analysis results"""
    
    # Save validation report
    save_json(results['validation'], "validation_report.json")
    
    # Save network analysis summary
    with open("network_analysis_summary.txt", "w") as f:
        f.write("CISCO NETWORK TOPOLOGY ANALYSIS REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        # Network overview
        f.write("NETWORK OVERVIEW:\n")
        f.write(f"- Total Devices: {results['network_info']['nodes']}\n")
        f.write(f"- Total Connections: {results['network_info']['edges']}\n")
        f.write(f"- Network Density: {results['network_info']['density']:.2f}\n")
        f.write(f"- Network Connected: {'Yes' if results['network_info']['is_connected'] else 'No'}\n\n")
        
        # Validation summary
        f.write("VALIDATION SUMMARY:\n")
        f.write(f"- Critical Issues: {results['validation']['total_issues']}\n")
        f.write(f"- Warnings: {results['validation']['total_warnings']}\n\n")
        
        # Issues
        if results['validation']['issues']:
            f.write("CRITICAL ISSUES:\n")
            for issue in results['validation']['issues']:
                f.write(f"- {issue['type']}: {issue['description']}\n")
        
        # Warnings
        if results['validation']['warnings']:
            f.write("\nWARNINGS:\n")
            for warning in results['validation']['warnings']:
                f.write(f"- {warning['type']}: {warning['description']}\n")
        
        # Recommendations
        f.write("\nRECOMMENDATIONS:\n")
        for rec in results['load_analysis']['recommendations']:
            f.write(f"- {rec['type']}: {rec['recommendation']}\n")

if __name__ == "__main__":
    main()
