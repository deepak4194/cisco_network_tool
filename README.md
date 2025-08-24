# Cisco Network Topology Analyzer

![](https://img.shields.io/badge/python-3.8%2B-blue)  ![](https://static.streamlit.io/badges/streamlit_badge_black.svg)  ![](https://img.shields.io/badge/Cisco%20Virtual%20Internship-2025-1BA1F2)

# Overview

A comprehensive tool developed for the Cisco Virtual Internship 2025.

Features:
- Parses Cisco router/switch configurations
- Generates professional network topologies
- Detects config issues and suggests improvements
- Performs network simulations
- Web UI via Streamlit

# Installation

Clone repo, create venv, install packages:
```
git clone https://github.com/yourusername/cisco-network-analyzer.git
cd cisco-network-analyzer
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

# Usage

Run app:
```
streamlit run streamlit_app.py
```

Or CLI:
```
python main.py sample_configs
```

# File Structure

Configs should be uploaded as:
- Folder per device: E.g., `R1/config.dump`
- Or a zip with all folders
- Or flat files named `R1_config.dump`

# Contact

For help: deepakmandarapu231@gmail.com
