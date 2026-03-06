#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRIPT OTIMIZADO PARA GERAÇÃO DE TOPOLOGIAS DE REDE COM CLI e GUI
"""

import sys
import csv
import os
import re
import math
import logging
import uuid
import chardet
import json
import networkx as nx
import time
import random
import argparse
from datetime import datetime
from collections import defaultdict
import platform
import glob

versionctr = "B1.33"

# Try to import psutil for memory monitoring, but it's not mandatory
PSUTIL_AVAILABLE = False
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    pass  # psutil is not installed, but it's not critical



# =====================================================
# GLOBAL HELP TEXT (ADICIONAR NO INÍCIO DO SCRIPT)
# =====================================================

HELP_TEXT = """
NETWORK TOPOLOGY GENERATOR {versionctr}
====================================

OVERVIEW:
-----------
Tool for automatic generation of network diagrams (.drawio) from data:
- Equipment (elements.csv)
- Connections (connections.csv)
- Geographic locations (locations.csv)

⭐ MAIN FEATURES:
• 4 layout algorithms: Circular (c), Organic (o), Geographic (g), Hierarchical (h)
• To generate layouts (c, o, and h) only the connections.csv file with source and destination is required
• Custom colors and shapes per layer to determine node and connection customizations
• Multiple pages/views of layers in the same diagram
• Automatic regionalization (e.g.: CORE -> CORE_SOUTHEAST)
• Graphical user interface (GUI) and command line (CLI)
• Support for background maps (background images)
• Advanced filtering of elements/layers

🚀 HOW TO USE:
------------
1. GRAPHICAL MODE (GUI):
   Run without arguments:
      python network-topology-generator.py

2. TERMINAL MODE (CLI):
   python network-topology-generator.py [OPTIONS] CONNECTIONS_FILE.csv

🛠️ CLI ARGUMENTS:
--------------------
  -y          Include nodes without connections (orphans)
  -v          Verbose mode (logs on screen)
  -l          Generate logs in file
  -t LAYOUTS  Specify which layout to generate (c=circular, o=organic, g=geographic, h=hierarchical)
              Ex: -t cog → generates circular + organic + geographic
  -r          Enable layer regionalization
  -g PATH     Custom directory for input files
  -s PATH     Custom path for locations.csv
  -e PATH     Custom path for elements.csv
  -c PATH     Custom path for config.json
  -w PATH     Custom directory for output Draw.io files
  -o OPTIONS  View options:
              n = hide node names
              c = hide connection layers
              Ex: -o nc → enables both options
  -d          Ignore customizations in CSVs (use only config.json)
  -f FILTER   Filter to select elements/layers:
              in = include only elements starting with filters
              rn = remove elements starting with filters
              ic = include only layers starting with filters
              rc = remove layers starting with filters
              Ex: -f "in:RTIC;RTOC" → only elements starting with RTIC or RTOC
              Ex: -f "rc:METRO;INNER" → removes elements from METRO or INNER layers
  -h          Shows this help message

📂 INPUT FILES:
----------------------
1. connections.csv (MANDATORY):
   Format: endpoint-a;endpoint-b;connectiontext;strokeWidth;strokeColor;dashed;fontStyle;fontSize
   Example: RTIC-SPO99-99;RTOC-SPO98-99;Main Link;2;#036897;0;1;14

2. elements.csv (OPTIONAL):
   Format: element;layer;level;color;siteid;alias
   Example: RTIC-SPO99-99;INNER-CORE;1;#FF0000;SP01;Core-SP

3. locations.csv (OPTIONAL):
   Format: siteid;Location;GeographicRegion;Latitude;Longitude
   Example: SP01;SAOPAULO;Southeast;23.32.33.S;46.38.44.W

⚙️ CONFIG.JSON (ADVANCED CUSTOMIZATION):
----------------------------------------
Complete control of topology appearance and behavior:

🔧 BASIC STRUCTURE:
{{
  "LAYER_COLORS": {{"INNER-CORE": "#036897", "default": "#036897"}},
  "LAYER_STYLES": {{
    "INNER-CORE": {{
      "shape": "mxgraph.cisco19.rect",
      "prIcon": "router",	
      "width": 50,
      "height": 50
    }}
  }},
  "PAGE_DEFINITIONS": [{{"name": "GENERAL VIEW", "visible_layers": null}}]
}}

📌 MAIN SECTIONS:

1. LAYER_COLORS:
   • Defines HEX colors (#RRGGBB) for each layer
   • Ex: "INNER-CORE": "#036897"

2. LAYER_STYLES:
   • Configures equipment appearance by layer
   • Key properties:
     - shape: Equipment shape (e.g., mxgraph.cisco.routers.router)
     - prIcon: Internal icon (e.g., router, switch, server)
     - width/height: Icon size
     - fillColor: Fill color (overrides LAYER_COLORS)

3. LAYER_DEFAULT_BY_PREFIX:
   • Automatic mapping of equipment to layers
   • Ex: "RTIC": {{"layer": "INNER-CORE", "level": 1}}

4. CONNECTION_STYLES:
   • Defines connection style by layer
   • Ex: "INNER-CORE": {{"color": "#036897", "strokeWidth": "2"}}

5. PAGE_DEFINITIONS:
   • Defines diagram pages/views
   • "visible_layers": null = show all layers
   • Ex: {{"name": "NORTH VIEW", "visible_layers": ["CORE_NORTH"]}}

6. LAYOUT PARAMETERS (Customize each algorithm):
   • CIRCULAR_LAYOUT: center_x, center_y, base_radius, radius_increment
   • ORGANIC_LAYOUT: k_base, iterations_per_node, scale_per_node
   • GEOGRAPHIC_LAYOUT: canvas_width, canvas_height, background_image
   • HIERARCHICAL_LAYOUT: vertical_spacing, horizontal_spacing

7. LEGEND_CONFIG:
   • Configures legend position and appearance
   • Ex: "position": {{"x": 50, "y": 30}}

🔍 AVAILABLE SHAPES (mxgraph):
    • Routers: mxgraph.cisco.routers.router
    • Switches: mxgraph.cisco19.rect (prIcon: l2_switch)
    • Servers: mxgraph.office.machines.server
    • Firewalls: mxgraph.cisco.security.firewall
    • DWDM: mxgraph.cisco.misc.dwdm_filter

🛠️ PRACTICAL EXAMPLES:
--------------------
1. Simple generation:
   python network-topology-generator.py -t cog -r networks.csv

2. Windows with advanced options:
   python network-topology-generator.py -y -t gh -e "C:\\data\\equipment.csv" network.csv

3. Activating logs and regionalization:
   python network-topology-generator.py -l -r -t co campus_sp.csv

4. Filtering specific elements:
   python network-topology-generator.py -f "in:RTIC;RTOC" -t c backbone.csv

5. Removing specific layers:
   python network-topology-generator.py -f "rc:METRO;ACCESS" -t o campus.csv

⚠️ COMMON TROUBLESHOOTING:
-------------------------------
Problem: "JSON decoding error"
Solution: Validate your config.json at https://jsonlint.com/

Problem: Geographic layout not generated
Solution: Check coordinate format in locations.csv

Problem: Disorganized diagram
Solution: Adjust parameters in config.json:
  • Circular: increase radius_increment
  • Organic: increase k_base
  • Geographic: increase min_distance

📤 GENERATED OUTPUT:
----------------
    Naming pattern: FileName_TIMESTAMP_layout.drawio
    Example: network_sp_20250615143045_geographic.drawio

📌 How to generate test files for script loading
Use the National Backbone Topology Generator, available at:
    https://github.com/flashbsb/Backbone-Network-Topology-Generator

🌎 OFFICIAL REPOSITORY: 
    https://github.com/flashbsb/Network-Topology-Generator-for-Drawio
""".format(versionctr=versionctr)

# Logging configuration will be done in main() with timestamp
logger = logging.getLogger(__name__)

# Function to log memory usage
def log_memory_usage(message=""):
    """Records memory usage with an optional message"""
    if not PSUTIL_AVAILABLE:
        return
    
    try:
        process = psutil.Process(os.getpid())
        mem = process.memory_info().rss / 1024 / 1024  # MB
        logger.debug("🧠 %sMemory usage: %.2f MB", f"{message} - " if message else "", mem)
    except Exception as e:
        logger.error("Failed to measure memory: %s", str(e))

# XML templates for generating the draw.io file
DRAWIO_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="{timestamp}" agent="Mozilla/5.0" etag="{etag}" version="21.3.7">
"""

DRAWIO_DIAGRAM_TEMPLATE = """  <diagram name="{page_name}" id="{diagram_id}">
    <mxGraphModel dx="1422" dy="793" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="0" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="1">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
"""

DRAWIO_FOOTER = """
</mxfile>
"""


def run_gui():
    # IMPORT AND DEFINE EVERYTHING RELATED TO GUI HERE
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk, scrolledtext
    from collections import defaultdict
    import platform
    import json
    import os
    import sys
    from datetime import datetime
    
    # =====================================================
    # GUI IMPLEMENTATION
    # =====================================================
    
    class TopologyGUI:
        def __init__(self, root):
            self.root = root
            self.root.title(f"Network Topology Generator for Drawio - {versionctr}") 
            self.root.geometry("550x800")
            self.root.resizable(True, True)
            
            # Default settings
            self.config = self.load_config()
            self.connection_files = []
            self.elements_file = "elements.csv" if os.path.exists("elements.csv") else ""
            self.locations_file = "locations.csv" if os.path.exists("locations.csv") else ""
            
            # Control variables
            self.include_orphans = tk.BooleanVar(value=False)
            self.regionalization = tk.BooleanVar(value=False)
            self.circular_layout = tk.BooleanVar(value=True)
            self.organic_layout = tk.BooleanVar(value=False)
            self.geographic_layout = tk.BooleanVar(value=False)
            self.hierarchical_layout = tk.BooleanVar(value=False)
            self.generate_logs = tk.BooleanVar(value=False)
            self.ignore_optional = tk.BooleanVar(value=False)
            self.hide_connection_layers = tk.BooleanVar(value=False)
            self.hide_node_names = tk.BooleanVar(value=False)
            
            # Filter variables initialization
            self.filter_type = tk.StringVar(value="none")  # "none", "in", "rn", "ic", "rc"
            self.filter_value = tk.StringVar()
            
            # Check resource availability
            self.has_elements = os.path.exists("elements.csv")
            self.has_locations = os.path.exists("locations.csv")
            self.has_config = os.path.exists("config.json")
            
            # Create interface
            self.create_widgets()
            
            # Update initial controls state
            self.update_ui_state()
            
            # Add reference to help text
            self.help_text = HELP_TEXT
            
        def load_config(self):
            """Tries to load config.json or returns default if not exists"""
            config_file = 'config.json'
            default_config = {
                "LAYER_STYLES": {},
                "LAYER_COLORS": {"default": "#036897"},
                "PAGE_DEFINITIONS": [{"name": "GENERAL VIEW", "visible_layers": None}],
                "CIRCULAR_LAYOUT": {"center_x": 500, "center_y": 500, "base_radius": 100, "radius_increment": 50},
                "ORGANIC_LAYOUT": {"k_base": 0.25, "k_min": 0.8, "k_max": 2.5, "iterations_per_node": 10},
                "GEOGRAPHIC_LAYOUT": {"canvas_width": 1000, "canvas_height": 800, "margin": 50, "min_distance": 30},
                "NODE_STYLE": {"shape": "mxgraph.cisco.routers.router", "fillColor": "#ffffff", "strokeColor": "#000000"},
                "CONNECTION_STYLE_BASE": {"edgeStyle": "orthogonalEdgeStyle", "curved": "0", "rounded": "0"},
                "CONNECTION_STYLES": {"default": {"color": "#000000", "strokeWidth": "2"}},
                "LEGEND_CONFIG": {"position": {"x": 50, "y": 30}, "item_spacing": 40}
            }
            
            try:
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    
                    # Log configuration info
                    logger.debug("⚙️ Loaded configurations:")
                    logger.debug("  - Pages: %s", [p['name'] for p in config["PAGE_DEFINITIONS"]])
                    logger.debug("  - Layer colors: %s", list(config["LAYER_COLORS"].keys()))
                    
                    # Log layout parameters
                    for layout in ["CIRCULAR_LAYOUT", "ORGANIC_LAYOUT", "GEOGRAPHIC_LAYOUT", "HIERARCHICAL_LAYOUT"]:
                        if layout in config:
                            logger.debug("  - %s: %s", layout, json.dumps(config[layout], indent=2))
                    
                    return config
                return default_config
            except Exception as e:
                logger.exception("Error loading configuration", exc_info=True)
                return default_config
    
        def _on_mousewheel(self, event, canvas):
            """Handles mouse wheel scrolling events for the canvas"""
            if sys.platform.startswith('linux'):
                if event.num == 4:  # Scroll up
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5: # Scroll down
                    canvas.yview_scroll(1, "units")
            else:
                # Windows and macOS
                delta = event.delta
                if sys.platform == "darwin":  # macOS adjustment
                    delta = -delta
                    
                if delta > 0:
                    canvas.yview_scroll(-1, "units")
                else:
                    canvas.yview_scroll(1, "units")
    
        def create_widgets(self):
            # Configure style
            style = ttk.Style()
            style.configure("Title.TLabel", font=("Arial", 16, "bold"), foreground="#036897")
            style.configure("Section.TLabelframe.Label", font=("Arial", 10, "bold"), foreground="#036897")
            style.configure("Accent.TButton", font=("Arial", 10, "bold"), foreground="#000000", background="#036897")
            style.configure("Help.TButton", font=("Arial", 10, "bold"), foreground="#000000", background="#FF8C00")
    
            # Main frame with scrollbar - SCROLL FIX
            main_frame = ttk.Frame(self.root)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
            # Canvas and scrollbar
            canvas = tk.Canvas(main_frame, highlightthickness=0)
            scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
    
            # Configure scroll system
            def _configure_canvas(e):
                # Updates scroll region and forces resize
                canvas.configure(scrollregion=canvas.bbox("all"))
                canvas.yview_moveto(0)  # Keeps at top on resize
            scrollable_frame.bind("<Configure>", _configure_canvas)
    
            # Create window inside canvas for internal frame
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    
            # Configure scrollbar
            canvas.configure(yscrollcommand=scrollbar.set)
    
            # Allow internal frame to expand with content
            scrollable_frame.bind("<Configure>", 
                lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
                
            # Configure grid expansion
            scrollable_frame.grid_rowconfigure(0, weight=1)
            scrollable_frame.grid_columnconfigure(0, weight=1)

            # Bind scroll events correctly
            def _bind_mousewheel(widget):
                # Bind events for Windows and macOS
                widget.bind("<MouseWheel>", lambda e: self._on_mousewheel(e, canvas))
                
                # Bind specific events for Linux
                widget.bind("<Button-4>", lambda e: self._on_mousewheel(e, canvas))
                widget.bind("<Button-5>", lambda e: self._on_mousewheel(e, canvas))

            # Bind events to all relevant components
            _bind_mousewheel(canvas)
            _bind_mousewheel(scrollable_frame)
            _bind_mousewheel(main_frame)
            _bind_mousewheel(self.root)
    
            # Force focus on main frame
            main_frame.bind("<Enter>", lambda e: main_frame.focus_set())
    
            # Pack elements correctly
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
    
            # ========= HEADER =========
            header_frame = ttk.Frame(scrollable_frame)
            header_frame.grid(row=0, column=0, columnspan=2, sticky="we", pady=(0, 10))
            
            # Title and help button side by side
            title = ttk.Label(
                header_frame, 
                text=f"  Network Topology Generator",
                style="Title.TLabel"
            )
            title.pack(side="left", padx=(0, 10))
    
            help_btn = ttk.Button(
                header_frame, 
                text="Help", 
                command=self.show_help,
                style="Help.TButton",
                width=8
            )
            help_btn.pack(side="right")
    
            # ========= RESOURCE STATUS =========
            status_frame = ttk.LabelFrame(
                scrollable_frame, 
                text="Resource Status",
                style="Section.TLabelframe"
            )
            status_frame.grid(row=1, column=0, columnspan=2, sticky="we", padx=5, pady=5)
            status_frame.columnconfigure(1, weight=1)
    
            # Configure columns for alignment
            for i in range(3):
                status_frame.columnconfigure(i, weight=1 if i == 1 else 0)
    
            # File status
            ttk.Label(status_frame, text="config.json:").grid(row=0, column=0, sticky="w", padx=(10, 5), pady=2)
            config_status = ttk.Label(
                status_frame, 
                text="✔ Available" if self.has_config else "❌ Not found", 
                foreground="green" if self.has_config else "red"
            )
            config_status.grid(row=0, column=1, sticky="w", padx=5, pady=2)
            ttk.Label(status_frame, text="(Advanced customization)").grid(row=0, column=2, sticky="w", padx=(0, 10), pady=2)
            
            ttk.Label(status_frame, text="elements.csv:").grid(row=1, column=0, sticky="w", padx=(10, 5), pady=2)
            elementos_status = ttk.Label(
                status_frame, 
                text="✔ Available" if self.has_elements else "⚠ Optional not found", 
                foreground="green" if self.has_elements else "orange"
            )
            elementos_status.grid(row=1, column=1, sticky="w", padx=5, pady=2)
            ttk.Label(status_frame, text="(Equipment data)").grid(row=1, column=2, sticky="w", padx=(0, 10), pady=2)
            
            ttk.Label(status_frame, text="locations.csv:").grid(row=2, column=0, sticky="w", padx=(10, 5), pady=2)
            localidades_status = ttk.Label(
                status_frame, 
                text="✔ Available" if self.has_locations else "⚠ Optional not found", 
                foreground="green" if self.has_locations else "orange"
            )
            localidades_status.grid(row=2, column=1, sticky="w", padx=5, pady=2)
            ttk.Label(status_frame, text="(Geographic data)").grid(row=2, column=2, sticky="w", padx=(0, 10), pady=2)
    
            # ========= INPUT FILES =========
            files_frame = ttk.LabelFrame(
                scrollable_frame, 
                text="Input Files",
                style="Section.TLabelframe"
            )
            files_frame.grid(row=2, column=0, columnspan=2, sticky="we", padx=5, pady=10)
            
            # Connections (mandatory)
            conn_frame = ttk.Frame(files_frame)
            conn_frame.pack(fill="x", padx=5, pady=5)
            ttk.Label(conn_frame, text="Connection File(s)*:").pack(side="left", padx=(0, 10))
            ttk.Button(conn_frame, text="Select...", command=self.select_connection_files).pack(side="left", padx=(0, 10))
            self.connections_label = ttk.Label(conn_frame, text="None selected", foreground="gray", wraplength=350)
            self.connections_label.pack(side="left", fill="x", expand=True)
            
            # Elements (optional)
            elem_frame = ttk.Frame(files_frame)
            elem_frame.pack(fill="x", padx=5, pady=5)
            ttk.Label(elem_frame, text="Elements File:").pack(side="left", padx=(0, 10))
            ttk.Button(elem_frame, text="Select...", command=self.select_elements_file).pack(side="left", padx=(0, 10))
            self.elementos_label = ttk.Label(
                elem_frame, 
                text=self.elements_file if self.elements_file else "Default (elements.csv)", 
                foreground="blue", 
                wraplength=350
            )
            self.elementos_label.pack(side="left", fill="x", expand=True)
            
            # Locations (optional)
            loc_frame = ttk.Frame(files_frame)
            loc_frame.pack(fill="x", padx=5, pady=(5, 10))
            ttk.Label(loc_frame, text="Locations File:").pack(side="left", padx=(0, 10))
            ttk.Button(loc_frame, text="Select...", command=self.select_locations_file).pack(side="left", padx=(0, 10))
            self.localidades_label = ttk.Label(
                loc_frame, 
                text=self.locations_file if self.locations_file else "Default (locations.csv)", 
                foreground="blue", 
                wraplength=350
            )
            self.localidades_label.pack(side="left", fill="x", expand=True)
    
            # ========= GENERATION OPTIONS =========
            options_frame = ttk.LabelFrame(
                scrollable_frame, 
                text="Generation Options",
                style="Section.TLabelframe"
            )
            options_frame.grid(row=3, column=0, columnspan=2, sticky="we", padx=5, pady=10)
            
            # Column 1 - Main options
            col1_frame = ttk.Frame(options_frame)
            col1_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)
            
            self.orphans_check = ttk.Checkbutton(
                col1_frame, 
                text="Include nodes without connections", 
                variable=self.include_orphans
            )
            self.orphans_check.pack(anchor="w", padx=5, pady=5)
            
            self.regional_check = ttk.Checkbutton(
                col1_frame, 
                text="Layer regionalization", 
                variable=self.regionalization
            )
            self.regional_check.pack(anchor="w", padx=5, pady=5)
            
            self.ignore_optional_check = ttk.Checkbutton(
                col1_frame, 
                text="Ignore CSV customizations", 
                variable=self.ignore_optional
            )
            self.ignore_optional_check.pack(anchor="w", padx=5, pady=5)
            
            self.logs_check = ttk.Checkbutton(
                col1_frame, 
                text="Generate log file", 
                variable=self.generate_logs
            )
            self.logs_check.pack(anchor="w", padx=5, pady=5)
            
            # Column 2 - View options
            col2_frame = ttk.Frame(options_frame)
            col2_frame.pack(side="right", fill="both", expand=True, padx=10, pady=5)
            
            self.hide_names_check = ttk.Checkbutton(
                col2_frame, 
                text="Hide node names", 
                variable=self.hide_node_names
            )
            self.hide_names_check.pack(anchor="w", padx=5, pady=5)
            
            self.hide_conn_check = ttk.Checkbutton(
                col2_frame, 
                text="Hide connection layers", 
                variable=self.hide_connection_layers
            )
            self.hide_conn_check.pack(anchor="w", padx=5, pady=5)
            
            # ========= FILTERS =========
            filters_frame = ttk.LabelFrame(
                scrollable_frame, 
                text="Advanced Filters",
                style="Section.TLabelframe"
            )
            filters_frame.grid(row=7, column=0, columnspan=2, sticky="we", padx=5, pady=10)
    
            # Radiobutton group
            filter_type_frame = ttk.Frame(filters_frame)
            filter_type_frame.pack(fill="x", padx=10, pady=(10, 5))
    
            ttk.Label(filter_type_frame, text="Filter type:").pack(side="left", padx=(0, 15))
    
            filter_types = [
                ("No filter", "none"),
                ("Include elements (in)", "in"),
                ("Remove elements (rn)", "rn"),
                ("Include layers (ic)", "ic"),
                ("Remove layers (rc)", "rc")
            ]
    
            # Organize in 2 columns
            cols_frame = ttk.Frame(filter_type_frame)
            cols_frame.pack(side="left", fill="x", expand=True)
            
            col1 = ttk.Frame(cols_frame)
            col1.pack(side="left", fill="x", expand=True, padx=5)
            col2 = ttk.Frame(cols_frame)
            col2.pack(side="left", fill="x", expand=True, padx=5)
            
            for i, (text, value) in enumerate(filter_types):
                col = col1 if i < 3 else col2
                rb = ttk.Radiobutton(
                    col,
                    text=text,
                    variable=self.filter_type,
                    value=value,
                    command=self.update_filter_state
                )
                rb.pack(anchor="w", padx=5, pady=2)
    
            # Field for filter value
            filter_value_frame = ttk.Frame(filters_frame)
            filter_value_frame.pack(fill="x", padx=10, pady=(0, 10))
    
            ttk.Label(filter_value_frame, text="Values (separated by ;):").pack(side="left", padx=(0, 10))
    
            self.filter_entry = ttk.Entry(
                filter_value_frame, 
                textvariable=self.filter_value,
                width=40,
                state="disabled"
            )
            self.filter_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
    
            # ========= LAYOUTS =========
            layouts_frame = ttk.LabelFrame(
                scrollable_frame, 
                text="Output Layouts",
                style="Section.TLabelframe"
            )
            layouts_frame.grid(row=5, column=0, columnspan=2, sticky="we", padx=5, pady=10)
    
            # Mass selection controls
            ctrl_frame = ttk.Frame(layouts_frame)
            ctrl_frame.pack(fill="x", padx=10, pady=(5, 0))
            
            ttk.Label(ctrl_frame, text="Selection:").pack(side="left", padx=(0, 10))
            
            self.mark_all_btn = ttk.Button(
                ctrl_frame, 
                text="Mark All",
                command=self.mark_all_layouts,
                width=14
            )
            self.mark_all_btn.pack(side="left", padx=(0, 5))
            
            self.unmark_all_btn = ttk.Button(
                ctrl_frame, 
                text="Unmark All",
                command=self.unmark_all_layouts,
                width=18
            )
            self.unmark_all_btn.pack(side="left")
    
            # Individual checkboxes organized horizontally
            checks_frame = ttk.Frame(layouts_frame)
            checks_frame.pack(fill="x", padx=20, pady=10)
            
            self.circular_check = ttk.Checkbutton(
                checks_frame, 
                text="Circular", 
                variable=self.circular_layout
            )
            self.circular_check.pack(side="left", padx=20, pady=5)
            
            self.organic_check = ttk.Checkbutton(
                checks_frame, 
                text="Organic", 
                variable=self.organic_layout
            )
            self.organic_check.pack(side="left", padx=20, pady=5)
            
            self.geographic_check = ttk.Checkbutton(
                checks_frame, 
                text="Geographic", 
                variable=self.geographic_layout
            )
            self.geographic_check.pack(side="left", padx=20, pady=5)
            
            self.hierarchical_check = ttk.Checkbutton(
                checks_frame, 
                text="Hierarchical", 
                variable=self.hierarchical_layout
            )
            self.hierarchical_check.pack(side="left", padx=20, pady=5)
    
            # ========= MAIN ACTION =========
            action_frame = ttk.Frame(scrollable_frame)
            action_frame.grid(row=6, column=0, columnspan=2, sticky="we", padx=5, pady=1)
            
            # Centralized generation button
            generate_btn = ttk.Button(
                action_frame, 
                text="Generate Topologies", 
                command=self.generate_topologies,
                style="Accent.TButton",
                width=50
            )
            generate_btn.pack(pady=10, ipadx=10, ipady=8)
    
            # ========= STATUS BAR =========
            self.status_var = tk.StringVar(value="Ready to generate topologies")
            status_bar = ttk.Label(
                self.root, 
                textvariable=self.status_var, 
                relief="sunken", 
                anchor="w",
                padding=(10, 5)
            )
            status_bar.pack(side="bottom", fill="x")
            
            # Update initial state
            self.update_ui_state()
            self.update_filter_state()
            canvas.bind("<Motion>", lambda e: canvas.focus_set())  # Improves touchpad response
    
        
        # Add this new method in the class:
        def update_filter_state(self):
            """Updates the entry field state based on the filter type"""
            if self.filter_type.get() != "none":
                self.filter_entry.config(state="normal")
            else:
                self.filter_entry.config(state="disabled")
                self.filter_value.set("")                        
    
        def show_help(self):
            """Displays help window with complete content"""
            help_window = tk.Toplevel(self.root)
            help_window.title("Help - Network Topology Generator")
            help_window.geometry("900x700")
            help_window.resizable(True, True)
            
            # Main frame
            main_frame = ttk.Frame(help_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Scrolling text area
            text_area = scrolledtext.ScrolledText(
                main_frame,
                wrap=tk.WORD,
                font=("Consolas", 10),
                bg="#F0F0F0",
                padx=10,
                pady=10
            )
            text_area.pack(fill=tk.BOTH, expand=True)
            
            # Insert help text
            text_area.insert(tk.INSERT, self.help_text)
            text_area.configure(state="disabled")  # Read only
            
            # Close button
            close_btn = ttk.Button(
                main_frame,
                text="Close",
                command=help_window.destroy
            )
            close_btn.pack(pady=10)
    
    
        def mark_all_layouts(self):
            """Marks all available layouts with special handling for geographic"""
            self.circular_layout.set(True)
            self.organic_layout.set(True)
            self.hierarchical_layout.set(True)
            
            # Verify files availability directly
            if self.has_elements and self.has_locations:
                self.geographic_layout.set(True)
    
        def unmark_all_layouts(self):
            """Unmarks all available layouts"""
            self.circular_layout.set(False)
            self.organic_layout.set(False)
            self.hierarchical_layout.set(False)
            self.geographic_layout.set(False)
    
        def update_ui_state(self):
            # Update control states based on file availability
            self.has_elements = os.path.exists(self.elements_file) if self.elements_file else False
            self.has_locations = os.path.exists(self.locations_file) if self.locations_file else False
            
            # Enable/disable controls
            state_orphans = "normal" if self.has_elements else "disabled"
            self.orphans_check.configure(state=state_orphans)
            
            # Regionalization requires elements AND locations
            state_regional = "normal" if (self.has_elements and self.has_locations) else "disabled"
            self.regional_check.configure(state=state_regional)
            
            # Geographic layout requires elements AND locations
            state_geo = "normal" if (self.has_elements and self.has_locations) else "disabled"
            self.geographic_check.configure(state=state_geo)
            
            # Update variables if files do not exist
            if not self.has_locations:
                self.regionalization.set(False)
                self.geographic_layout.set(False)
            
            if not self.has_config:
                self.ignore_optional_check.configure(state="disabled")
                self.ignore_optional.set(False)
            
            # Update button states
            self.update_button_states()
    
        def update_button_states(self):
            """Updates button states based on resource availability"""
            self.mark_all_btn["state"] = "normal"
            self.unmark_all_btn["state"] = "normal"
            
        def select_connection_files(self):
            files = filedialog.askopenfilenames(
                title="Select Connection Files",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
            )
            if files:
                self.connection_files = list(files)
                file_names = ", ".join([os.path.basename(f) for f in files[:3]])
                if len(files) > 3:
                    file_names += f", ... (+{len(files)-3} more)"
                self.connections_label.config(text=file_names, foreground="blue")
                
                # New lines from instruction
                names = [os.path.basename(f) for f in files]
                if len(names) > 3:
                    display_text = f"{len(names)} files selected:\n" + ", ".join(names[:3]) + "..."
                else:
                    display_text = f"{len(names)} files selected:\n" + ",\n".join(names)
                        
                self.connections_label.config(text=display_text, foreground="blue")
                self.status_var.set(f"Selected {len(files)} connection files.")
                self.update_ui_state()
                    
        def clear_conexoes(self):
            self.connection_files = []
            self.connections_label.config(text="No files selected", foreground="blue")
            self.status_var.set("Connection files cleared.")
            self.update_ui_state()
        
        def select_elementos(self):
            from tkinter import filedialog
            filename = filedialog.askopenfilename(
                title="Select Elements File",
                filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*"))
            )
            if filename:
                self.elements_file = filename # Changed from self.elements_file.set(filename)
                self.elementos_label.config(text=os.path.basename(filename), foreground="blue") # Added to update label
                self.update_ui_state() # Added to update UI state
    
        def select_localidades(self):
            from tkinter import filedialog
            filename = filedialog.askopenfilename(
                title="Select Locations File",
                filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*"))
            )
            if filename:
                self.locations_file = filename # Changed from self.locations_file.set(filename)
                self.localidades_label.config(text=os.path.basename(filename), foreground="blue") # Added to update label
                # Re-evaluate available layouts if location is selected
                # if not self.config.get("GEOGRAPHIC_LAYOUT", {}).get("locked", 0): # This line was not in original context
                #     self.chk_geographic.config(state=tk.NORMAL) # This line was not in original context
                self.update_ui_state()
    
        def select_elements_file(self):
            file = filedialog.askopenfilename(
                title="Select Elements File",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
            )
            if file:
                self.elements_file = file
                self.elementos_label.config(text=os.path.basename(file), foreground="blue")
                self.update_ui_state()
    
        def select_locations_file(self):
            file = filedialog.askopenfilename(
                title="Select Locations File",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
            )
            if file:
                self.locations_file = file
                self.localidades_label.config(text=os.path.basename(file), foreground="blue")
                self.update_ui_state()
    
        def generate_topologies(self):
            hide_node_names = self.hide_node_names.get()
            hide_connection_layers = self.hide_connection_layers.get()
            
            if not self.connection_files:
                messagebox.showerror("Error", "Select at least one connection file!")
                return
                
            if not any([self.circular_layout.get(), self.organic_layout.get(), 
                       self.geographic_layout.get(), self.hierarchical_layout.get()]):
                messagebox.showerror("Error", "Select at least one layout type!")
                return
    
            # Get filter configuration BEFORE the loop
            filter_str = None
            if self.filter_type.get() != "none":
                filter_value = self.filter_value.get().strip()
                if not filter_value:
                    messagebox.showwarning("Warning", "Filter selected but no values defined!")
                    return
                filter_str = f"{self.filter_type.get()}:{filter_value}" 
    
     
            # Configure logging if necessary
            if self.generate_logs.get():
                log_file = f'topologia_gui_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
                file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
                file_handler.setLevel(logging.INFO)
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                logger.info("Logs enabled, writing to: %s", log_file)
    
                # New information log
                logger.info("Execution started via GUI")
                logger.info("Options used (different from default):")
                
                # Check differences from default
                if self.include_orphans.get():
                    logger.info("  Include orphan nodes")
                if self.regionalization.get():
                    logger.info("  Regionalization")
                    
                layouts = ""
                if self.circular_layout.get(): layouts += "c"
                if self.organic_layout.get(): layouts += "o"
                if self.geographic_layout.get(): layouts += "g"
                if self.hierarchical_layout.get(): layouts += "h"
                if layouts != "c":  # Default is only circular
                    logger.info("  Layouts: %s", layouts)
                    
                if self.elements_file != "elements.csv":
                    logger.info("  Elements: %s", self.elements_file)
                if self.locations_file != "locations.csv":
                    logger.info("  Locations: %s", self.locations_file)
                    
                if self.hide_node_names.get():
                    logger.info("  Hide node names")
                if self.hide_connection_layers.get():
                    logger.info("  Hide connection layers")
            
            # Log system information
            logger.debug("System: %s %s", sys.platform, platform.platform())
            logger.debug("Python: %s", sys.version)
            logger.debug("Dependencies: networkx=%s", nx.__version__)
            
            # Determine selected layouts
            layouts = ""
            if self.circular_layout.get(): layouts += "c"
            if self.organic_layout.get(): layouts += "o"
            if self.geographic_layout.get(): layouts += "g"
            if self.hierarchical_layout.get(): layouts += "h"
            
            # Create configuration instance
            config = self.load_config()
            
            # Process each file
            success = True
            total_files = len(self.connection_files)
            
            for idx, file in enumerate(self.connection_files):
                self.status_var.set(f"Processing file {idx+1}/{total_files}: {os.path.basename(file)}")
                self.root.update()
                
                try:
                    # FIX: Pass parameters in the correct order
                    result = self.process_single_file(
                        file, 
                        config, 
                        self.include_orphans.get(), 
                        layouts, 
                        self.regionalization.get(),
                        self.elements_file,
                        self.locations_file,
                        hide_node_names,          # Fixed
                        hide_connection_layers,    # Fixed
                        ignore_optional=self.ignore_optional.get(),
                        filter_string=filter_str
                    )
                    if not result:
                        success = False
                        self.status_var.set(f"Error processing: {os.path.basename(file)}")
                except Exception as e:
                    logger.error(f"Error processing {file}: {str(e)}", exc_info=True)
                    success = False
                    self.status_var.set(f"Critical error in: {os.path.basename(file)}")
            
            if success:
                messagebox.showinfo("Success", "All topologies generated successfully!")
                self.status_var.set("Processing completed successfully")
            else:
                messagebox.showwarning("Warning", "Some topologies may not have been generated correctly. Check logs.")
                self.status_var.set("Processing completed with errors")
                
            # Final memory log
            log_memory_usage("End of processing")
            
    
        def process_single_file(self, connections_file, config, include_orphans, layouts_choice, 
                                regionalization, elements_file, locations_file, 
                                hide_node_names, hide_connection_layers, ignore_optional,
                                filter_string=None):
            """Processes a complete connection file"""
            file_start = time.perf_counter()
            logger.info("⏱️ [START] Processing file: %s", connections_file)
            logger.debug("Parameters: orphans=%s, layouts=%s, regional=%s, hide_names=%s, hide_cnx=%s",
                        include_orphans, layouts_choice, regionalization, 
                        hide_node_names, hide_connection_layers)
            
            try:
                # Create generator instance with custom files
                generator = TopologyGenerator(
                    elements_file=elements_file, 
                    connections_file=connections_file, 
                    config=config, 
                    include_orphans=include_orphans, 
                    regionalization=regionalization,
                    locations_file=locations_file,
                    hide_node_names=hide_node_names,
                    hide_connection_layers=hide_connection_layers,
                    ignore_optional=ignore_optional,
                    filter_string=filter_string
                )
                
                if not generator.valid:
                    return False
                    
                if not generator.read_elements():
                    return False
                    
                if not generator.read_connections():
                    return False
                    
                base_name = os.path.splitext(connections_file)[0]
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                
                success = True
                
                # Layout mapping dictionary
                layout_map = {
                    'c': ('circular', 'Circular'),
                    'o': ('organico', 'Organic'),
                    'g': ('geografico', 'Geographic'),
                    'h': ('hierarquico', 'Hierarchical')
                }
                
                generated_layouts = []
                
                # Generate selected layouts
                for char in layouts_choice:
                    if char in layout_map:
                        layout_key, layout_name = layout_map[char]
                        
                        # Check geographic availability
                        if char == 'g' and not generator.has_geographic_data:
                            logger.warning("Geographic layout requested but no geographic data. Ignoring.")
                            continue
                        
                        layout_start = time.perf_counter()
                        output_file = f"{base_name}_{timestamp}_{layout_key}.drawio"
                        if generator.generate_drawio(output_file, layout_key):
                            gen_time = time.perf_counter() - layout_start
                            logger.info("✅ %s generated in %.2fs (%.1fKB)", 
                                      layout_name, gen_time, os.path.getsize(output_file)/1024)
                            generated_layouts.append(layout_name)
                        else:
                            success = False
                
                # Detailed performance log
                file_time = time.perf_counter() - file_start
                logger.info("✅ [SUCCESS] File processed in %.2fs | Layouts: %s | Nodes: %d | Connections: %d",
                          file_time, ', '.join(generated_layouts), 
                          len(generator.nodes), len(generator.connections))
                
                # Log elements without siteid
                if generator.nodes_without_siteid:
                    nodes_list = ", ".join(generator.nodes_without_siteid[:10])
                    if len(generator.nodes_without_siteid) > 10:
                        nodes_list += f", ... (+{len(generator.nodes_without_siteid) - 10} more)"
                    logger.debug("%d elements without siteid moved to special layer: %s", 
                                  len(generator.nodes_without_siteid), nodes_list)        
                
                return success
            except Exception as e:
                logger.exception("💥 [FAILURE] Error in processing")
                logger.error("Context: layouts=%s, regional=%s, elements=%s",
                           layouts_choice, regionalization, elements_file)
                return False
    # Code that initializes the GUI
    root = tk.Tk()
    app = TopologyGUI(root)
    root.mainloop()
    
# =====================================================
# CORE FUNCTIONALITY
# =====================================================

def load_config(config_file='config.json'):
    """Loads configurations from JSON file with robust error handling"""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        logger.info("Configurations loaded from %s", config_file)
        
        # Convert old LAYER_SHAPES structure to new LAYER_STYLES
        if "LAYER_SHAPES" in config and "LAYER_STYLES" not in config:
            config["LAYER_STYLES"] = {}
            for layer, shape in config["LAYER_SHAPES"].items():
                config["LAYER_STYLES"][layer] = {"shape": shape}
            logger.info("Converted LAYER_SHAPES to LAYER_STYLES")
            
        # Log configuration information
        logger.debug("⚙️ Loaded configurations:")
        logger.debug("  - Pages: %s", [p['name'] for p in config["PAGE_DEFINITIONS"]])
        logger.debug("  - Layer colors: %s", list(config["LAYER_COLORS"].keys()))
        
        # Log layout parameters
        for layout in ["CIRCULAR_LAYOUT", "ORGANIC_LAYOUT", "GEOGRAPHIC_LAYOUT", "HIERARCHICAL_LAYOUT"]:
            if layout in config:
                logger.debug("  - %s: %s", layout, json.dumps(config[layout], indent=2))
            
        return config
        
    except FileNotFoundError:
        logger.critical("Configuration file not found: %s", config_file)
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.critical("Error decoding JSON in %s: %s", config_file, str(e))
        sys.exit(1)
        
def verificar_dependencias():
    """Checks critical dependencies and informs how to install them"""
    dependencies = {
        "tkinter": "Graphical Interface (usually already included in Python)",
        "networkx": "Graph and layout management",
        "chardet": "File encoding detection"
    }
    
    missing = []
    for module, description in dependencies.items():
        try:
            __import__(module)
        except ImportError:
            missing.append((module, description))
    
    if missing:
        print("ERROR: Missing dependencies!")
        print("="*50)
        for module, description in missing:
            print(f"• {module} ({description})")
        
        print("\nInstall missing packages with:")
        print("pip install " + " ".join([m[0] for m in missing]))
        print("\nDownload full Python from: https://python.org/downloads")
        input("Press Enter to exit...")
        sys.exit(1)

class TopologyGenerator:
    def __init__(self, elements_file, connections_file, config, include_orphans=False, 
                 regionalization=False, locations_file='locations.csv',
                 hide_node_names=False, hide_connection_layers=False,
                 ignore_optional=False, filter_string=None):
        self.elements_file = elements_file
        self.connections_file = connections_file
        self.config = config
        self.include_orphans = include_orphans
        self.regionalization = regionalization
        self.locations_file = locations_file
        self.nodes = defaultdict(dict)
        self.connections = []
        self.layers = defaultdict(list)
        self.node_ids = {}
        self.layer_ids = {}
        self.circular_alignments = defaultdict(list)
        self.node_colors = defaultdict(list)
        self.valid = True
        self.locations_map = self._load_locations()
        self.has_geographic_data = False
        self.nodes_without_siteid = []  # New list for nodes without siteid
        self.ignore_optional = ignore_optional
        self.filter_string = filter_string
        self.hide_node_names = hide_node_names
        self.hide_connection_layers = hide_connection_layers
        logger.info(f"Options: hide_node_names={hide_node_names}, hide_connection_layers={hide_connection_layers}")
        
        self._initialize() 
        logger.info("Initialization complete")
        
    def apply_filters(self):
        """Applies filters to nodes and connections based on filter_string"""
        if not self.filter_string:
            return
            
        logger.info(f"Applying filter: {self.filter_string}")
        filter_type, filter_list = self.filter_string.split(':', 1)
        filters = [f.strip() for f in filter_list.split(';') if f.strip()]
        
        # Create copies for safe iteration
        all_nodes = list(self.nodes.keys())
        all_connections = list(self.connections)
        
        # Node filtering
        nodes_to_remove = set()
        for node in all_nodes:
            node_data = self.nodes[node]
            layer = node_data['layer']
            
            if filter_type == 'in':  # Filter for Node INclusion
                if not any(node.startswith(f) for f in filters):
                    nodes_to_remove.add(node)
                    
            elif filter_type == 'rn':  # Filter for Node Removal
                if any(node.startswith(f) for f in filters):
                    nodes_to_remove.add(node)
                    
            elif filter_type == 'ic':  # Filter for Layer INclusion
                if not any(layer.startswith(f) for f in filters):
                    nodes_to_remove.add(node)
                    
            elif filter_type == 'rc':  # Filter for Layer Removal
                if any(layer.startswith(f) for f in filters):
                    nodes_to_remove.add(node)
        
        # Remove marked nodes
        for node in nodes_to_remove:
            # Remove node from structures
            if node in self.nodes:
                del self.nodes[node]
            if node in self.node_ids:
                del self.node_ids[node]
            
            # Remove from layers
            for layer in list(self.layers.keys()):
                if node in self.layers[layer]:
                    self.layers[layer].remove(node)
                    if not self.layers[layer]:  # Remove empty layer
                        del self.layers[layer]
                        del self.layer_ids[layer]
        
        # Filter connections involving removed nodes
        self.connections = [
            conn for conn in all_connections
            if conn['source'] not in nodes_to_remove and conn['target'] not in nodes_to_remove
        ]
        
        logger.info(f"Filter applied: {len(nodes_to_remove)} nodes removed, "
                  f"{len(all_connections) - len(self.connections)} connections removed")    

    def _dms_to_decimal(self, dms_str, coord_type, site_id):
        """
        Converts DMS coordinates to decimal with robust handling
        
        Args:
            dms_str (str): Coordinate in DMS format
            coord_type (str): 'lat' or 'lon'
            site_id (str): Site ID for logs
            
        Returns:
            float: Decimal value or None if failed
        """
        if not dms_str or str(dms_str).strip() == '':
            logger.error("Empty coordinate for site %s", site_id)
            return None
        
        try:
            # Pre-process string
            dms_clean = str(dms_str).strip().upper()
            direction = None
            
            # Extract direction (N/S/E/W)
            if dms_clean[-1] in ['N', 'S', 'E', 'W']:
                direction = dms_clean[-1]
                dms_clean = dms_clean[:-1].strip()
            
            # Normalize format
            dms_clean = dms_clean.replace(',', '.').replace(' ', '')
            parts = [p for p in dms_clean.split('.') if p != '']
            
            if len(parts) < 2:
                logger.error("Invalid format for site %s: %s", site_id, dms_str)
                return None
            
            # Combine fractional parts
            if len(parts) > 3:
                seconds_str = '.'.join(parts[2:])
                parts = parts[:2] + [seconds_str]
            
            # Convert to floats
            try:
                degrees = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2]) if len(parts) > 2 else 0.0
            except ValueError as e:
                logger.error("Non-numeric value in %s: %s", site_id, dms_str)
                return None
            
            # Calculate decimal value
            decimal = degrees + minutes/60 + seconds/3600
            
            # Determine default direction if not specified
            if not direction:
                if coord_type == 'lat': direction = 'S'
                elif coord_type == 'lon': direction = 'W'
            
            # Apply sign according to direction
            if direction in ['S', 'W']:
                decimal = -decimal
                
            return decimal
            
        except Exception as e:
            logger.error("Conversion error for site %s: %s - %s", site_id, dms_str, str(e))
            return None
            
    def _update_node_layer(self, node_name, old_layer, new_layer, level):
        """Updates layer registration when a node's layer is changed"""
        # Remove from old layer
        if old_layer in self.layers and node_name in self.layers[old_layer]:
            self.layers[old_layer].remove(node_name)
        
        # Update layer in node
        self.nodes[node_name]['layer'] = new_layer
        
        # Register in new layer
        self._register_node(node_name, level)

    def _determine_layer_by_prefix(self, node_name):
        """Determines layer/level based on config prefixes"""
        prefix_map = self.config.get("LAYER_DEFAULT_BY_PREFIX", {})
        for prefix in sorted(prefix_map.keys(), key=len, reverse=True):
            if node_name.startswith(prefix):
                layer_info = prefix_map[prefix]
                return layer_info["layer"], layer_info["level"]
        
        # If not found, use default
        default_info = prefix_map.get("default", {"layer": "default", "level": 10})
        return default_info["layer"], default_info["level"]


    def _load_locations(self):
        """
        Loads localities mapping for geographic data
        
        Returns:
            dict: Locality mapping -> {region, latitude, longitude}
        """
        if not os.path.exists(self.locations_file):
            logger.warning("Localities file not provided. Geographic layout will not be available.")
            return {}
        
        try:
            encoding = self._detect_encoding(self.locations_file)
            logger.info("Reading locations from %s (encoding: %s)", 
                   os.path.basename(self.locations_file), encoding)
            mapping = {}
            with open(self.locations_file, 'r', encoding=encoding, errors='replace') as f:
                reader = csv.DictReader(f, delimiter=';')
                valid_count = 0
                invalid_count = 0
                
                for row in reader:
                    site_id = row.get('siteid', '').strip()
                    location = row.get('Location', '').strip()
                    region = row.get('GeographicRegion', '').strip()
                    lat_str = row.get('Latitude', '').strip()
                    lon_str = row.get('Longitude', '').strip()
                    
                    if not site_id:
                        site_id = f"Line {reader.line_num}"
                    
                    # Validate mandatory data
                    if not all([location, region, lat_str, lon_str]):
                        logger.warning("Incomplete data for site %s", site_id)
                        continue
                    
                    # Convert coordinates
                    lat_decimal = self._dms_to_decimal(lat_str, 'lat', site_id)
                    lon_decimal = self._dms_to_decimal(lon_str, 'lon', site_id)
                    
                    if None in [lat_decimal, lon_decimal]:
                        invalid_count += 1
                        continue
                    
                    # Store valid data
                    mapping[site_id] = {  # Changed to use siteid as key
                        'region': region,
                        'latitude': lat_decimal,
                        'longitude': lon_decimal
                    }
                    valid_count += 1
                
                logger.info("Mapping loaded: %d valid, %d invalid", valid_count, invalid_count)
            return mapping
        except Exception as e:
            logger.error("Error loading localities: %s", str(e))
            return {}

    def _initialize(self):
        """Checks files (elements.csv now optional)"""
        if not os.path.exists(self.connections_file):
            logger.error("Connection file not found: %s", self.connections_file)
            self.valid = False
            return
            
        # Always define a default encoding
        self.encoding_elements = 'utf-8'  # Default value
        
        # Conditional encoding detection
        if os.path.exists(self.elements_file):
            self.encoding_elements = self._detect_encoding(self.elements_file)
            
        self.encoding_connections = self._detect_encoding(self.connections_file)
        logger.info("Encodings detected: elements=%s, connections=%s", 
                   self.encoding_elements, self.encoding_connections)

    def _detect_encoding(self, file_path):
        """Detects CSV file encoding using chardet."""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            
            # Adjust common encodings that fail
            if encoding and encoding.lower() in ('ascii', 'windows-1252', 'iso-8859-1'):
                encoding = 'utf-8' # Force utf-8 to try first in common CSVs
                
            return encoding if encoding else 'utf-8'
        except Exception as e:
            logger.warning("Error detecting encoding for %s: %s. Using utf-8.", os.path.basename(file_path), e)
            return 'utf-8-sig'  # Safe default for Windows

    def _normalize_color(self, color_str):
        """
        Args:
            color_str (str): Color value
            
        Returns:
            str: Normalized color or 'none'
        """
        if color_str is None:
            return None
        if not isinstance(color_str, str):
            return str(color_str)
        if color_str.lower() == "none":
            return "none"
        if not color_str.startswith('#') and color_str != "":
            return f'#{color_str}'
        return color_str

    def read_elements(self):
        if not os.path.exists(self.elements_file):
            logger.warning("Elements file not found. Continuing without it.")
            return True
            
        try:
            with open(self.elements_file, 'r', encoding=self.encoding_elements, errors='replace') as f:
                # Verify mandatory headers
                header = f.readline().strip().split(';')
                if 'element' not in header:
                    logger.error("Header 'element' not found in elements.csv")
                    return False
                    
                f.seek(0)  # Return to start
                reader = csv.DictReader(f, delimiter=';')
                row_count = 0
                for row in reader:
                    row_count += 1
                    self._process_element_row(row)
                
                logger.info("Processed %d element lines", row_count)
                return True
                
        except Exception as e:
            logger.error("Failed to read elements: %s", str(e), exc_info=True)
            return False

    def _apply_regionalization(self, node_name, node_data):
        """Applies regional data if the flag is active (modifies the layer)"""
        if not self.regionalization or not self.locations_map:
            return
            
        # Verify if regionalization was already applied
        if node_data.get('regionalized'):
            return
            
        siteid = node_data.get('siteid', '')
        if siteid and siteid in self.locations_map:
            loc_data = self.locations_map[siteid]
            region = loc_data['region']
            old_layer = node_data['layer']
            
            # Apply only if it does not have a regional suffix yet
            if not old_layer.endswith(f"_{region}"):
                new_layer = f"{old_layer}_{region}"
                
                # Apply layer update
                self._update_node_layer(node_name, old_layer, new_layer, node_data['level'])
                logger.debug(f"Regionalization applied to {node_name}: {old_layer} -> {new_layer}")
                
                # Mark as regionalized
                node_data['regionalized'] = True
        else:
            # Move to special layer NO_SITEID
            old_layer = node_data['layer']
            new_layer = "NO_SITEID"
            self._update_node_layer(node_name, old_layer, new_layer, 10)  # Level 10
            logger.debug(f"Element without siteid moved to special layer: {node_name}")  # Changed to DEBUG
            self.nodes_without_siteid.append(node_name)

    def _apply_geodata(self, node_name, node_data):
        """Applies geographic data (coordinates) if available, without changing the layer"""
        if not self.locations_map:
            return
            
        siteid = node_data.get('siteid', '')
        if siteid and siteid in self.locations_map:
            loc_data = self.locations_map[siteid]
            # Only assigns the coordinates
            node_data['coordinates'] = (loc_data['latitude'], loc_data['longitude'])
            logger.debug(f"Geographic data applied to {node_name} via siteid: {siteid}")
        else:
            # Mark for special processing in geographic layout
            node_data['coordinates'] = None
            logger.debug(f"No geographic data for {node_name}")

    def _process_element_row(self, row):
        source = row['element'].strip()
        if not source:
            return
            
        # Use 'layer' instead of 'tipo'
        original_layer = row.get('layer', '').strip()
        level_str = row.get('level', '').strip()
        
        siteid = row.get('siteid', '').strip()  # New field
        if self.ignore_optional:
            source_color = None  # Ignore color defined in CSV
        else:
            source_color = row.get('color', '').strip()
        
        level = None
        if level_str:
            try:
                level = int(level_str)
            except ValueError:
                logger.warning(f"Invalid level value for {source}: '{level_str}'")
        
        # Determine layer/level if necessary
        need_layer_inference = not original_layer
        need_level_inference = level is None
        
        if need_layer_inference or need_level_inference:
            inferred_layer, inferred_level = self._determine_layer_by_prefix(source)
            if need_layer_inference:
                original_layer = inferred_layer
            if need_level_inference:
                level = inferred_level
                
        # ADDED VALIDATION
        if not original_layer:
            logger.error(f"Undefined layer for {source}")
            return
            
        if level is None:
            logger.warning(f"Undefined level for {source}, using default 10")
            level = 10
        
        if source_color:
            self.node_colors[source].append(source_color)
            
        # MAIN FIX: DO NOT apply regionalization here
        # Regionalization will be applied later in the flow
        final_layer = original_layer
        coordinates = None
        
        alias = row.get('alias', '').strip()  # Novo campo
        
        # Update node data
        if source not in self.nodes:
            self.nodes[source] = {
                'layer': final_layer,
                'level': level,
                'color': source_color if source_color else None,
                'coordinates': coordinates,
                'regionalized': False,
                'siteid': siteid,
                'alias': alias  # New field
            }
        else:
            self.nodes[source]['alias'] = alias  # Update alias
            self.nodes[source]['level'] = level
            if source_color:
                self.nodes[source]['color'] = source_color
            self.nodes[source]['siteid'] = siteid  # New field

        # Apply geographic data regardless of regionalization
        self._apply_geodata(source, self.nodes[source])
        
        # Apply regionalization ONLY if flag is active
        if self.regionalization:
            self._apply_regionalization(source, self.nodes[source])
        
        self._register_node(source, level)
        logger.info(f"Processed: {source} | Layer: {final_layer} | Level: {level} | Color: {source_color} | SiteID: {siteid}")
        if self.ignore_optional and row.get('color'):
            logger.debug("Ignoring defined color for %s (option -d)", source)
    
    def read_connections(self):
        try:
            logger.info(f"Opening file: {self.connections_file}")
            
            # Add debug log to check real path
            if not os.path.exists(self.connections_file):
                logger.error(f"File not found: {self.connections_file}")
                return False        
        
            with open(self.connections_file, 'r', encoding=self.encoding_connections, errors='replace') as f:
                reader = csv.DictReader(f, delimiter=';')
                row_count = 0
                for row in reader:
                    row_count += 1
                    # Support both hyphen and underscore in headers
                    source = row.get('endpoint-a', row.get('endpoint_a', '')).strip()
                    target = row.get('endpoint-b', row.get('endpoint_b', '')).strip()
                    
                    if not source or not target:
                        logger.warning(f"Row {row_count} skipped: source or target empty")
                        continue
                    
                    for node in [source, target]:
                        if node not in self.nodes:
                            layer, level = self._determine_layer_by_prefix(node)
                            node_data = {
                                'layer': layer,
                                'level': level,
                                'color': None,
                                'coordinates': None,
                                'regionalized': False,  # New field
                                'siteid': ''            # New field
                            }
                            self.nodes[node] = node_data
                            # Apply geographic data
                            self._apply_geodata(node, node_data)
                            # Register the created node
                            self._register_node(node, level)
                            
                        # Apply regionalization if active (only once)
                        if self.regionalization:
                            self._apply_regionalization(node, self.nodes[node])
                                
                    self._process_connection_row(row)
                
                logger.info("Processed %d connection rows", row_count)
                self._validate_data()
                
                # Geographic data verification
                self.has_geographic_data = any(
                    data.get('coordinates') is not None 
                    for data in self.nodes.values()
                )
                
                logger.info("Geographic data available: %s", 
                           "Yes" if self.has_geographic_data else "No")
                return True
                
        except Exception as e:
            logger.error("Failed to read connections: %s", str(e), exc_info=True)
            return False

    def _validate_colors(self):
        """Checks color consistency and reports discrepancies"""
        for node, colors in self.node_colors.items():
            if len(set(colors)) > 1:
                logger.warning("Color discrepancy for %s: %s", node, ', '.join(set(colors)))
                if node in self.nodes:
                    self.nodes[node]['color'] = colors[0]  # Use first color

    def _register_node(self, node_name, level):
        """Registers node in internal structures"""
        if node_name not in self.node_ids:
            self.node_ids[node_name] = str(uuid.uuid4())
            logger.debug(f"Registered node: {node_name} | ID: {self.node_ids[node_name]}")
            
        node_data = self.nodes[node_name]
        
        if node_data['layer'] not in self.layer_ids:
            self.layer_ids[node_data['layer']] = str(uuid.uuid4())
            
        if node_name not in self.layers[node_data['layer']]:
            self.layers[node_data['layer']].append(node_name)
            
        if node_name not in self.circular_alignments[level]:
            self.circular_alignments[level].append(node_name)

    def _process_connection_row(self, row):
        """Processes a connection row with normalized keys"""
        # Critical change: keep hyphens in column names
        normalized_row = {k.lower().replace(' ', ''): v for k, v in row.items()}
        
        # Use original names without removing hyphens
        # Try both variants (hyphen and underscore)
        source = normalized_row.get('endpoint-a', normalized_row.get('endpoint_a', '')).strip()
        target = normalized_row.get('endpoint-b', normalized_row.get('endpoint_b', '')).strip()
        
        if not source or not target:
            return
            
        # Create specific layer for connections
        original_layer = self.nodes[source]['layer']
        connection_layer = f"{original_layer}_CNX"

        # If the option is active, ignore optional properties
        if self.ignore_optional:
            conn_data = {
                'source': source,
                'target': target,
                'layer': connection_layer,
                'connection_text': normalized_row.get('connectiontext', normalized_row.get('connection_text', '')).strip(),
                'strokeWidth': None,
                'strokeColor': None,
                'dashed': '0',
                'fontStyle': '1',
                'fontSize': '14'
            }
        else:
            conn_data = {
                'source': source,
                'target': target,
                'layer': connection_layer,
                'connection_text': normalized_row.get('connectiontext', normalized_row.get('connection_text', '')).strip(),
                'strokeWidth': normalized_row.get('strokewidth', '').strip() if 'strokewidth' in normalized_row and normalized_row['strokewidth'] else None,
                'strokeColor': normalized_row.get('strokecolor', '').strip() if 'strokecolor' in normalized_row and normalized_row['strokecolor'] else None,
                'dashed': normalized_row.get('dashed', '0').strip() if 'dashed' in normalized_row else '0',
                'fontStyle': normalized_row.get('fontstyle', '1').strip() if 'fontstyle' in normalized_row else '1',
                'fontSize': normalized_row.get('fontsize', '14').strip() if 'fontsize' in normalized_row else '14'
            }
        
        self.connections.append(conn_data)
        
        # Register connection layer if new
        if connection_layer not in self.layer_ids:
            self.layer_ids[connection_layer] = str(uuid.uuid4())
        
        if connection_layer not in self.layers:
            self.layers[connection_layer] = []
        if self.ignore_optional and any(row.get(k) for k in ['strokeWidth', 'strokeColor', 'dashed']):
            logger.debug("Ignoring connection properties for %s-%s (option -d)", source, target)            

    def _validate_data(self):
        """Validates data and handles unconnected nodes, listing removed nodes"""
        all_nodes = set(self.nodes.keys())
        connected_nodes = set()
        for conn in self.connections:
            connected_nodes.add(conn['source'])
            connected_nodes.add(conn['target'])
            
        orphan_nodes = all_nodes - connected_nodes
        if orphan_nodes:
            orphan_list = sorted(orphan_nodes)
            orphan_count = len(orphan_list)
            
            # Show up to 10 nodes to avoid very long logs
            display_list = orphan_list[:10]
            display_text = ', '.join(display_list)
            if orphan_count > 10:
                display_text += f', ... (+{orphan_count - 10} more)'
            
            if self.include_orphans:
                logger.warning(  # Changed to logger.warning
                    "%d unconnected nodes included (option -y): %s", 
                    orphan_count, 
                    display_text
                )
            else:
                logger.warning(  # Changed to logger.warning
                    "%d unconnected nodes removed: %s", 
                    orphan_count, 
                    display_text
                )
                # Remove orphan nodes
                for node in orphan_list:
                    if node in self.nodes:
                        node_data = self.nodes[node]
                        layer = node_data['layer']
                        level = node_data['level']
                        
                        if layer in self.layers and node in self.layers[layer]:
                            self.layers[layer].remove(node)
                        
                        if level in self.circular_alignments and node in self.circular_alignments[level]:
                            self.circular_alignments[level].remove(node)
                        
                        del self.nodes[node]
                    
                    # REMOVE FROM LIST OF NODES WITHOUT SITEID
                    if node in self.nodes_without_siteid:
                        self.nodes_without_siteid.remove(node)
                    
                    if node in self.node_ids:
                        del self.node_ids[node]
                    
                    if node in self.node_colors:
                        del self.node_colors[node]
        else:
            logger.info("No unconnected nodes found")

    def calculate_circular_positions(self):
        """
        Calculates positions for circular layout based on levels
        
        Returns:
            dict: Node -> (x, y) mapping
        """
        start_time = time.perf_counter()
        logger.info("Calculating circular layout...")
        cfg = self.config["CIRCULAR_LAYOUT"]
        center_x, center_y = cfg["center_x"], cfg["center_y"]
        base_radius = cfg["base_radius"]
        radius_increment = cfg["radius_increment"]
        positions = {}
        
        # Group nodes by level
        level_nodes = defaultdict(list)
        for node, data in self.nodes.items():
            level = data['level']
            level_nodes[level].append(node)
        
        levels = sorted(level_nodes.keys())
        min_level = min(levels) if levels else 1
        max_level = max(levels) if levels else 1
        
        # Position nodes in concentric circles
        for level in levels:
            nodes = level_nodes[level]
            radius = base_radius + (level - min_level) * radius_increment
            angle_step = 2 * math.pi / len(nodes)
            offset_angle = -math.pi/2  # Start at the top
            
            for idx, node in enumerate(nodes):
                angle = offset_angle + idx * angle_step
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                positions[node] = (x, y)
        
        # Handle nodes without defined level
        placed_nodes = set(positions.keys())
        all_defined_nodes = set(self.nodes.keys())
        missing_nodes = all_defined_nodes - placed_nodes
        
        if missing_nodes:
            logger.warning("%d nodes without level, positioning at level %d", len(missing_nodes), max_level+1)
            level = max_level + 1
            radius = base_radius + (level - min_level) * radius_increment
            missing_list = sorted(missing_nodes)
            angle_step = 2 * math.pi / len(missing_list)
            
            for idx, node in enumerate(missing_list):
                angle = offset_angle + idx * angle_step
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                positions[node] = (x, y)
        
        elapsed = time.perf_counter() - start_time
        logger.debug("⚙️ Circular layout calculated in %.3fs | Levels: %d", 
                   elapsed, len(self.circular_alignments))
        return positions

    def calculate_organico_positions(self):
        """
        Calculates positions for organic layout using force algorithm
        
        Returns:
            dict: Node -> (x, y) mapping
        """
        start_time = time.perf_counter()
        logger.info("Calculating organic layout...")
        G = nx.Graph()
        G.add_nodes_from(self.nodes.keys())
        G.add_edges_from([(c['source'], c['target']) for c in self.connections])
        
        num_nodes = len(G.nodes)
        if num_nodes == 0:
            logger.warning("No nodes for organic layout")
            return {}
        
        cfg = self.config.get("ORGANIC_LAYOUT", {})
        k_base = cfg.get("k_base", 0.25)
        k_min = cfg.get("k_min", 0.8)
        k_max = cfg.get("k_max", 2.5)
        iterations_per_node = cfg.get("iterations_per_node", 10)
        iterations_min = cfg.get("iterations_min", 500)
        iterations_max = cfg.get("iterations_max", 2000)
        scale_per_node = cfg.get("scale_per_node", 0.5)
        scale_min = cfg.get("scale_min", 5.0)
        scale_max = cfg.get("scale_max", 30.0)
        base_width = cfg.get("base_width", 1400)
        base_height = cfg.get("base_height", 1000)
        
        # Calculate dynamic parameters based on the network
        k_value = max(k_min, min(k_max, k_base * math.sqrt(num_nodes)))
        iterations_value = max(iterations_min, min(iterations_max, num_nodes * iterations_per_node))
        scale_value = max(scale_min, min(scale_max, num_nodes * scale_per_node))
        
        logger.info("Organic parameters: k=%.2f, iterations=%d, scale=%.2f", 
                   k_value, iterations_value, scale_value)
        
        # Calculate layout with networkx
        pos = nx.spring_layout(
            G,
            k=k_value,
            iterations=iterations_value,
            seed=42,  # Fixed seed for reproducibility
            scale=scale_value,
            threshold=0.0001
        )
        
        # Normalize positions
        all_x = [x for x, _ in pos.values()]
        all_y = [y for _, y in pos.values()]
        
        if not all_x or not all_y:
            return {}
        
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        size_factor = max(1.0, math.log(num_nodes + 1))
        target_width = base_width * size_factor
        target_height = base_height * size_factor
        
        range_x = max_x - min_x if max_x != min_x else 1
        range_y = max_y - min_y if max_y != min_y else 1
        
        scale_x = target_width / range_x
        scale_y = target_height / range_y
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        offset_x = target_width/2 - center_x * scale_x
        offset_y = target_height/2 - center_y * scale_y
        
        result = {
            node: (
                pos[node][0] * scale_x + offset_x,
                pos[node][1] * scale_y + offset_y
            )
            for node in G.nodes
        }
        
        elapsed = time.perf_counter() - start_time
        logger.debug("⚙️ Organic layout calculated in %.3fs | Nodes: %d | Edges: %d", 
                   elapsed, len(G.nodes), len(G.edges))
        return result

    def calculate_geographic_positions(self):
        """Corrected version with special handling for SEM_SITEID"""
        start_time = time.perf_counter()
        logger.info("Calculating geographic layout...")
        cfg = self.config.get("GEOGRAPHIC_LAYOUT", {})
        
        # Identificar todos os nós que não possuem coordenadas (para a camada de revisão)
        nodes_without_coords = [n for n, d in self.nodes.items() if d.get('coordinates') is None]
        
        # Se não houver nós com coordenadas nem nós para revisão, encerra
        if not any(data.get('coordinates') is not None for data in self.nodes.values()) and not nodes_without_coords:
            return {}
        
        # ================================================
        # TRATAMENTO ESPECIAL PARA ELEMENTOS SEM LOCALIZAÇÃO (CAMADA DE REVISÃO)
        # ================================================
        # Calcular centro do canvas
        canvas_width = cfg.get("canvas_width", 5000)
        canvas_height = cfg.get("canvas_height", 5000)
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        
        # Posicionar elementos sem sites/coord no centro em espiral
        review_positions = {}
        spiral_radius = 200
        angle_step = 0.5
        
        for idx, node in enumerate(nodes_without_coords):
            # Mover para camada de REV se já não estiver em uma camada específica de erro
            old_layer = self.nodes[node]['layer']
            if old_layer != "TO_REVIEW":
                 self._update_node_layer(node, old_layer, "TO_REVIEW", 10)
                 
            angle = idx * angle_step
            radius = spiral_radius + idx * 50
            
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            
            review_positions[node] = (x, y)
            logger.info(f"Positioning unlocated element in REVIEW layer: {node} at ({x:.1f}, {y:.1f})")
        # ================================================
        
        # Filtra apenas nós válidos com coordenadas para o cálculo geográfico real
        valid_nodes = {n: d['coordinates'] for n, d in self.nodes.items() if d.get('coordinates') is not None}
        
        # Se não houver nós com coordenadas, retorna apenas as posições de revisão
        if not valid_nodes:
            return review_positions

        
        # Use .values() to access coordinates directly
        coords = valid_nodes.values()
        
        # Calculate bounding box
        lats = [c[0] for c in coords]  # Corrected!
        lons = [c[1] for c in coords]  # Corrected!
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        range_lat = max_lat - min_lat if max_lat != min_lat else 1
        range_lon = max_lon - min_lon if max_lon != min_lon else 1
        
        # Configurations
        margin = cfg["margin"]
        min_distance = cfg["min_distance"]
        
        # Map nodes by coordinate
        nodes_by_coord = defaultdict(list)
        for node, coord in valid_nodes.items():
            nodes_by_coord[coord].append(node)
        
        positions = review_positions # Start with review positions
        for coord, nodes in nodes_by_coord.items():
            lat, lon = coord
            
            # Normalize to canvas coordinates
            x = margin + (lon - min_lon) * (canvas_width - 2*margin) / range_lon
            y = canvas_height - margin - (lat - min_lat) * (canvas_height - 2*margin) / range_lat
            
            # Prevent overlapping nodes in the same location
            if len(nodes) > 1:
                angle_step = 360 / len(nodes)
                for i, node in enumerate(nodes):
                    angle_rad = math.radians(i * angle_step)
                    dx = min_distance * math.cos(angle_rad)
                    dy = min_distance * math.sin(angle_rad)
                    positions[node] = (x + dx, y + dy)
            else:
                positions[nodes[0]] = (x, y)
        
        logger.info("Geographic positions calculated for %d nodes", len(positions))
        
        # ================================================
        # OVERLAP PREVENTION ALGORITHM
        # ================================================
        logger.info("Applying overlap prevention...")
        node_sizes = {}
        for node in positions:
            style = self._get_node_style(self.nodes[node])
            node_sizes[node] = max(style["width"], style["height"])
        
        # Convert to list for iteration
        nodes = list(positions.keys())
        changed = True
        max_iterations = 20
        iter_count = 0
        
        while changed and iter_count < max_iterations:
            changed = False
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    node1 = nodes[i]
                    node2 = nodes[j]
                    
                    x1, y1 = positions[node1]
                    x2, y2 = positions[node2]
                    
                    # Calculate Euclidean distance
                    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    
                    # Calculate minimum required distance
                    min_required = node_sizes[node1]/2 + node_sizes[node2]/2 + cfg.get("min_node_distance", 150)
                    
                    if distance < min_required:
                        changed = True
                        # Calculate direction vector
                        dx = x2 - x1
                        dy = y2 - y1
                        if dx == 0 and dy == 0:
                            # Rare case of same position
                            angle = random.uniform(0, 2 * math.pi)
                            dx = math.cos(angle)
                            dy = math.sin(angle)
                            distance = 1
                        
                        # Displacement factor (proportional to overlap)
                        move_factor = (min_required - distance) / distance
                        
                        # Apply displacement keeping the midpoint
                        move_x = dx * move_factor * 0.5
                        move_y = dy * move_factor * 0.5
                        
                        # Update positions
                        positions[node1] = (
                            positions[node1][0] - move_x,
                            positions[node1][1] - move_y
                        )
                        positions[node2] = (
                            positions[node2][0] + move_x,
                            positions[node2][1] + move_y
                        )
            iter_count += 1
        
        logger.info(f"Overlap prevention completed in {iter_count} iterations")
        # ================================================
        
        elapsed = time.perf_counter() - start_time
        logger.debug("⚙️ Geographic layout calculated in %.3fs | Nodes with coord: %d | Without coord: %d", 
                   elapsed, len(valid_nodes), len(nodes_without_coords))
        return positions


    def calculate_hierarchical_positions(self):
        """Calculates positions for hierarchical layout"""
        start_time = time.perf_counter()
        logger.info("Calculating hierarchical layout...")
        cfg = self.config.get("HIERARCHICAL_LAYOUT", {})
        vertical_spacing = cfg.get("vertical_spacing", 200)
        horizontal_spacing = cfg.get("horizontal_spacing", 100)
        top_margin = cfg.get("top_margin", 50)
        left_margin = cfg.get("left_margin", 50)
        
        # Group nodes by level
        nodes_by_level = defaultdict(list)
        max_width_per_level = defaultdict(int)
        for node, data in self.nodes.items():
            level = data.get('level', 10)  # Default to level 10
            nodes_by_level[level].append(node)
            
            # Pre-calculate node sizes
            style = self._get_node_style(data)
            max_width_per_level[level] = max(max_width_per_level[level], style["width"])
        
        # Sort levels from smallest (top) to largest (bottom)
        sorted_levels = sorted(nodes_by_level.keys())
        
        # Calculate positions
        positions = {}
        current_y = top_margin
        
        for level in sorted_levels:
            nodes = nodes_by_level[level]
            level_width = max_width_per_level[level]
            
            # Calculate total required width
            total_width = len(nodes) * level_width + (len(nodes) - 1) * horizontal_spacing
            start_x = left_margin + (cfg.get("canvas_width", 2000) - total_width) / 2
            
            # Distribute nodes horizontally
            x = start_x
            for node in nodes:
                data = self.nodes[node]
                style = self._get_node_style(data)
                
                # Position node center
                pos_x = x + style["width"] / 2
                pos_y = current_y + style["height"] / 2
                
                positions[node] = (pos_x, pos_y)
                x += style["width"] + horizontal_spacing
            
            # Advance to next level
            current_y += max(self._get_node_style(self.nodes[node])["height"] for node in nodes) + vertical_spacing
        
        elapsed = time.perf_counter() - start_time
        logger.debug("⚙️ Hierarchical layout calculated in %.3fs | Levels: %d", 
                   elapsed, len(nodes_by_level))
        return positions


    def _get_node_style(self, node_data, scale_factor=1.0):
        """
        Generates visual style for a node based on its layer
        
        Args:
            node_data (dict): Node data
            scale_factor (float): Scaling factor for sizing
            
        Returns:
            dict: {style: string, width: int, height: int}
        """
        layer = node_data['layer']
        
        # Special style for elements without siteid
        if layer == "SEM_SITEID":
            return {
                "style": "shape=mxgraph.basic.ellipse;fillColor=#FF0000;strokeColor=#FFFFFF;",
                "width": 60 * scale_factor,
                "height": 60 * scale_factor
            }
        
        base_layer = layer.split('_', 1)[0]  # Remove regional suffix
        
        # Get layer style or default
        layer_styles = self.config["LAYER_STYLES"].get(
            base_layer, 
            self.config["LAYER_STYLES"].get("default", {})
        )

        # Determine fill color
        fill_color = None
        if node_data.get('color'):
            fill_color = self._normalize_color(node_data['color'])
        elif layer_styles.get('fillColor'):
            fill_color = self._normalize_color(layer_styles['fillColor'])
        else:
            fill_color = self._normalize_color(
                self.config["LAYER_COLORS"].get(
                    base_layer, 
                    self.config["LAYER_COLORS"]["default"]
                )
            )
        
        # Get other properties
        stroke_color = layer_styles.get('strokeColor', 
            self.config["NODE_STYLE"].get('strokeColor', '#ffffff'))
        stroke_color = self._normalize_color(stroke_color)

        # Apply scale factor
        width = layer_styles.get("width", 80) * scale_factor
        height = layer_styles.get("height", 80) * scale_factor

        # Build style string
        style_template = self.config["NODE_STYLE"].copy()
        style_template["fillColor"] = fill_color
        style_template["strokeColor"] = stroke_color

        shape_str = layer_styles.get("shape", "mxgraph.cisco.routers.router")
        
        # Add extra properties
        if isinstance(layer_styles, dict):
            for key, value in layer_styles.items():
                if key not in ["shape", "fillColor", "strokeColor"]:
                    shape_str += f";{key}={value}"
        
        style_template["shape"] = shape_str
        
        # Get and scale font size
        base_font_size = int(self.config["NODE_STYLE"].get("fontSize", 14))
        scaled_font_size = max(1, int(base_font_size * scale_factor))  # Minimum 1px
        
        # Add to style
        style_template["fontSize"] = str(scaled_font_size)
        # ========================================
        
        # Build final style string
        style_str = ";".join([f"{key}={value}" for key, value in style_template.items()])
        
        return {
            "style": style_str,
            "width": width,
            "height": height
        }

    def _get_connection_style(self, connection, scale_factor=1.0):
        """
        Generates visual style for a connection with scale support
        
        Args:
            connection (dict): Connection data
            scale_factor (float): Scaling factor for sizing
            
        Returns:
            str: Style string
        """
        # Determine base layer (removing suffixes)
        base_layer = connection['layer'].replace("_CNX", "").split('_', 1)[0]
        
        # Get base layer style or default
        base_style = self.config["CONNECTION_STYLES"].get(
            base_layer, 
            self.config["CONNECTION_STYLES"]["default"]
        )
        
        # Normalize connection color
        stroke_color = (
            self._normalize_color(connection["strokeColor"]) 
            if connection["strokeColor"] 
            else self._normalize_color(base_style["color"])
        )
        
        # Get base font size (with fallback)
        try:
            base_font_size = int(connection.get('fontSize', '14'))
        except (ValueError, TypeError):
            base_font_size = 14
        
        # Apply scale factor with a minimum of 1px
        scaled_font_size = max(1, int(base_font_size * scale_factor))
        
        # Get base style for connections
        style_template = self.config["CONNECTION_STYLE_BASE"].copy()
        
        # Update with specific properties
        style_template.update({
            "strokeWidth": connection['strokeWidth'] or base_style['strokeWidth'],
            "strokeColor": stroke_color,
            "dashed": connection['dashed'] or '0',
            "fontStyle": connection['fontStyle'] or '1',
            "fontSize": str(scaled_font_size),  # USE SCALED VALUE
            "fontColor": stroke_color
        })
        
        # Build final style string
        return ";".join([f"{key}={value}" for key, value in style_template.items()])

    def generate_drawio(self, output_file, layout_type):
        """
        Generates draw.io file with the specified layout
        """
        # Apply filters before calculating positions
        if self.filter_string:
            self.apply_filters()
            
        logger.info("🖼️ Generating diagram: %s", output_file)
        gen_start = time.perf_counter()
        
        # Map Portuguese names to English keys
        layout_key_map = {
            'circular': 'CIRCULAR_LAYOUT',
            'organico': 'ORGANIC_LAYOUT',
            'geografico': 'GEOGRAPHIC_LAYOUT',
            'hierarquico': 'HIERARCHICAL_LAYOUT'
        }
        
        layout_key = layout_key_map.get(layout_type)
        if not layout_key:
            logger.error("Invalid layout type: %s", layout_type)
            return False
            
        positions = {}
        try:
            # Select layout algorithm
            if layout_type == 'circular':
                positions = self.calculate_circular_positions()
            elif layout_type == 'organico':
                positions = self.calculate_organico_positions()
            elif layout_type == 'geografico':
                positions = self.calculate_geographic_positions()
            elif layout_type == 'hierarquico':
                positions = self.calculate_hierarchical_positions()
            else:
                logger.error("Invalid layout type: %s", layout_type)
                return False
                   
            if not positions:
                logger.error("No positions calculated for %s", layout_type)
                return False
                
            # Get scale factor and lock status for this layout
            layout_config = self.config[layout_key]
            scale_factor = layout_config.get("node_scale_factor", 1)
            locked = layout_config.get("locked", 0)
            
            logger.info("Layout %s | Nodes: %d | Connections: %d | Scale factor: %.1f | Locked: %d", 
                       layout_type, len(positions), len(self.connections), scale_factor, locked)
            
            # Start file content
            content = [
                DRAWIO_HEADER.format(
                    timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    etag=str(uuid.uuid4())
                )
            ]

            # Generate each page defined in config
            for page_def in self.config["PAGE_DEFINITIONS"]:
                page_content = self._generate_page(page_def, positions, layout_type, scale_factor, locked)
                if page_content is not None:  # Add only non-empty pages
                    content.append(page_content)
                
            content.append(DRAWIO_FOOTER)
            
            # Write final file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
            # Log generation time
            gen_time = time.perf_counter() - gen_start
            file_size = os.path.getsize(output_file) / 1024
            logger.info("✅ Diagram generated in %.2fs (%.1fKB)", gen_time, file_size)
            return True
            
        except Exception as e:
            logger.exception("💥 CRITICAL ERROR during generation")
            logger.error("Context: layout=%s, nodes=%d, connections=%d",
                       layout_type, len(positions), len(self.connections))
            return False

    def _generate_page(self, page_def, positions, layout_type, scale_factor=1.0, locked=0):
        """
        Generates XML content for a specific page
        
        Args:
            page_def (dict): Page definition from config
            positions (dict): Node -> position mapping
            layout_type (str): Type of layout used
            scale_factor (float): Scaling factor for node sizing
            locked (int): Layer lock status (0=editable, 1=locked)
            
        Returns:
            str: Page XML content
        """
        diagram_content = DRAWIO_DIAGRAM_TEMPLATE.format(
            page_name=page_def["name"],
            diagram_id=str(uuid.uuid4())
        )
        node_count = 0
        connection_count = 0
        page_content = [diagram_content]
        visible_layers = set(self.layers.keys()) if page_def["visible_layers"] is None else set(page_def["visible_layers"])

        
        # Expand visible layers
        expanded_visible_layers = set()
        for layer in visible_layers:
            expanded_visible_layers.add(layer)
            # Include regional layers
            for existing_layer in self.layers.keys():
                if existing_layer.startswith(layer + '_'):
                    expanded_visible_layers.add(existing_layer)
            # Include connection layers
            cnx_layer_base = f"{layer}_CNX"
            if cnx_layer_base in self.layers:
                expanded_visible_layers.add(cnx_layer_base)
        
        # Add background image for geographic layout
        if layout_type == 'geografico':
            bg_cfg = self.config.get("GEOGRAPHIC_LAYOUT", {}).get("background_image", {})
            if os.path.exists('brasil-map.png'):
                bg_cfg = bg_cfg.copy()
                bg_cfg["url"] = 'brasil-map.png'
                logger.info("Using local image as background")
            elif bg_cfg.get("url", "").startswith("http"):
                logger.info("Using remote image as background")
            else:
                logger.warning("Background image not found")
                bg_cfg = None

            if bg_cfg:
                bg_id = str(uuid.uuid4())
                page_content.extend([
                    f'        <mxCell id="{bg_id}" value="" style="shape=image;image={bg_cfg["url"]};',
                    f'          imageAspect=0;aspect=fixed;verticalLabelPosition=bottom;verticalAlign=top;',
                    f'          opacity={bg_cfg.get("opacity", 30)};" vertex="1" parent="1" visible="0">',
                    f'          <mxGeometry x="{bg_cfg["x"]}" y="{bg_cfg["y"]}" width="{bg_cfg["width"]}" height="{bg_cfg["height"]}" as="geometry"/>',
                    f'        </mxCell>'
                ])

        # Add layer objects in alphabetical order
        sorted_layers = sorted(self.layer_ids.items(), key=lambda x: x[0])
        for layer, lid in sorted_layers:
            # Determine layer visibility
            layer_visible = "1"
            if self.hide_connection_layers:
                layer_visible = "1"
                if layer.endswith("_CNX") and self.hide_connection_layers:
                    layer_visible = "0"
                
            if layer not in expanded_visible_layers:
                continue
                
            page_content.extend([
                f'        <object id="{lid}" label="{layer}">',
                f'          <mxCell style="locked={locked};" parent="0" visible="{layer_visible}"/>',
                f'        </object>'
            ])

        # Precompute nodes to be generated
        generated_nodes = set()
        for node in positions:
            if node in self.nodes and self.nodes[node]['layer'] in expanded_visible_layers:
                generated_nodes.add(node)
        
        # --- START OF MODIFICATION ---
        # Logic to handle multiple connections
        
        # 1. Count how many connections exist between each pair of nodes
        connection_counts = defaultdict(int)
        connection_directions = {}  # Track unique directions

        for conn in self.connections:
            key = (conn['source'], conn['target'])  # DIRECTIONAL tuple
            connection_counts[key] += 1
            connection_directions[key] = (conn['source'], conn['target'])
        # 2. Keep track of the current connection index we are drawing
        connection_indices = defaultdict(int)
        
        # Spacing factor between lines (in pixels)
        spacing_factor = 20
        # --- END OF MODIFICATION ---

        # Add connections only if both nodes exist
        for conn in self.connections:
            if (conn['layer'] not in expanded_visible_layers or
                conn['source'] not in self.node_ids or
                conn['target'] not in self.node_ids or
                conn['source'] not in positions or
                conn['target'] not in positions):
                continue
            connection_count += 1
            # --- START OF MODIFICATION ---
            origem_node = conn['source']
            destino_node = conn['target']
            
            # Get the original connection style
            style = self._get_connection_style(conn, scale_factor)
            
            # Default geometry
            geometry_xml = '<mxGeometry relative="1" as="geometry"/>'

            # Key for this pair of connections
            key = (origem_node, destino_node)  # Use directional tuple
            total_conns = connection_counts[key]
            
            if total_conns > 1:
                # Get the coordinates of the source and target nodes
                x1, y1 = positions[origem_node]
                x2, y2 = positions[destino_node]

                # Calculate the midpoint
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2

                # Calculate the line vector and its length
                dx = x2 - x1
                dy = y2 - y1
                length = math.sqrt(dx**2 + dy**2)
                
                # Get the index of this specific connection
                conn_index = connection_indices[key]

                # Calculate an offset to distribute the lines
                # The formula below centers the group of lines. E.g., for 3 lines (indices 0, 1, 2):
                # offset will be proportional to -1, 0, 1.
                offset_magnitude = spacing_factor * (conn_index - (total_conns - 1) / 2.0)

                # Use actual connection direction (source->target)
                x1_ref, y1_ref = positions[origem_node]
                x2_ref, y2_ref = positions[destino_node]
                dx_ref = x2_ref - x1_ref
                dy_ref = y2_ref - y1_ref
                length_ref = math.sqrt(dx_ref**2 + dy_ref**2) or 1.0

                # Unit perpendicular vector (90° rotation)
                perp_x = -dy_ref / length_ref
                perp_y = dx_ref / length_ref

                # Calculate control point
                point_x = mid_x + perp_x * offset_magnitude
                point_y = mid_y + perp_y * offset_magnitude

                # Force curved style and create new geometry with the control point
                style += ";curved=1"
                geometry_xml = (
                    '          <mxGeometry relative="1" as="geometry">\n'
                    '            <Array as="points">\n'
                    f'              <mxPoint x="{point_x:.2f}" y="{point_y:.2f}"/>\n'
                    '            </Array>\n'
                    '          </mxGeometry>'
                )
                
                # Increment the index for the next connection between this same pair
                connection_indices[key] += 1
            # --- END OF MODIFICATION ---
                
            page_content.extend([
                f'        <mxCell id="{uuid.uuid4()}" value="{conn["connection_text"]}" style="{style}" edge="1"',
                f'          parent="{self.layer_ids[conn["layer"]]}" source="{self.node_ids[conn["source"]]}"',
                f'          target="{self.node_ids[conn["target"]]}">',
                f'          {geometry_xml}',
                '        </mxCell>'
            ])

        # CORRECTION: Apply nodes without names
        for node in generated_nodes:
            data = self.nodes[node]
            alias = data.get('alias', '')  # Get alias if it exists
            style = self._get_node_style(data, scale_factor)
            x, y = positions[node]
            node_count += 1
            
            # Use alias if available, otherwise use original name
            label = ""
            if not self.hide_node_names:
                label = alias if alias else node  # Prioritize alias
            
            page_content.extend([
                f'        <object id="{self.node_ids[node]}" label="{label}">',
                f'          <mxCell style="{style["style"]}" vertex="1" parent="{self.layer_ids[data["layer"]]}">',
                f'            <mxGeometry x="{x - style["width"]/2}" y="{y - style["height"]/2}" ',
                f'width="{style["width"]}" height="{style["height"]}" as="geometry"/>',
                f'          </mxCell>',
                f'        </object>'
            ])

        # Calculate bounding box to position legend
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for node in generated_nodes:
            x, y = positions[node]
            style = self._get_node_style(self.nodes[node], scale_factor)
            width = style["width"]
            height = style["height"]
            
            node_min_x = x - width/2
            node_min_y = y - height/2
            node_max_x = x + width/2
            node_max_y = y + height/2
            
            min_x = min(min_x, node_min_x)
            min_y = min(min_y, node_min_y)
            max_x = max(max_x, node_max_x)
            max_y = max(max_y, node_max_y)
        
        if min_x == float('inf'):
            min_x = min_y = 0
            max_x = max_y = 1000

        # Create LEGEND layer
        legenda_layer_id = str(uuid.uuid4())
        page_content.extend([
            f'        <object id="{legenda_layer_id}" label="LEGEND">',
            f'          <mxCell style="locked={locked};" parent="0" visible="1"/>',
            f'        </object>'
        ])
        
        # Legend configuration and generation
        legend_config = self.config.get("LEGEND_CONFIG", {
            "position": {"x": 50, "y": 30},
            "item_spacing": 40,
            "text_offset": 45,
            "item_size": 30,
            "margin": 50
        })
        
        margin = legend_config.get("margin", 50)
        pos_x = max_x - 300
        pos_y = max_y + margin
        
        base_layers = set()
        for layer in expanded_visible_layers:
            base_layer = layer.split('_', 1)[0]
            base_layers.add(base_layer)

        base_layers = sorted(base_layers)
        
        if base_layers:
            # Legend title with page name
            page_name = page_def["name"].replace('"', '&quot;')
            page_content.extend([
                f'        <mxCell id="legend-title" value="{page_name}" style="text;html=1;strokeColor=none;fillColor=none;'
                f'align=left;verticalAlign=middle;fontStyle=1;fontSize=16;" vertex="1" parent="{legenda_layer_id}">',
                f'          <mxGeometry x="{pos_x}" y="{pos_y}" width="200" height="30" as="geometry"/>',
                f'        </mxCell>'
            ])
            
            pos_y += 30
            
            # Legend items (without applied scale)
            for base_layer in sorted(base_layers):
                layer_style = self.config["LAYER_STYLES"].get(
                    base_layer,
                    self.config["LAYER_STYLES"]["default"]
                )
                
                # Create dummy node to get style
                fake_node_data = {'layer': base_layer, 'color': None, 'type': 'Example'}
                style_dict = self._get_node_style(fake_node_data, scale_factor=1.0)
                
                # Adjust style for legend item
                style_str = style_dict["style"]
                parts = style_str.split(';')
                new_parts = [p for p in parts if not p.startswith('width=') and not p.startswith('height=')]
                new_parts.append(f'width={legend_config["item_size"]}')
                new_parts.append(f'height={legend_config["item_size"]}')
                new_style_str = ';'.join(new_parts)
                
                # Add icon
                item_id = str(uuid.uuid4())
                page_content.extend([
                    f'        <object id="{item_id}" label="">',
                    f'          <mxCell style="{new_style_str}" vertex="1" parent="{legenda_layer_id}">',
                    f'            <mxGeometry x="{pos_x}" y="{pos_y}" width="{legend_config["item_size"]}" height="{legend_config["item_size"]}" as="geometry"/>',
                    f'          </mxCell>',
                    f'        </object>'
                ])
                
                # Add text
                text_id = str(uuid.uuid4())
                layer_name = base_layer.replace("-", " ")
                page_content.extend([
                    f'        <mxCell id="{text_id}" value="{layer_name}" style="text;html=1;strokeColor=none;fillColor=none;'
                    f'align=left;verticalAlign=middle;fontSize=14;" vertex="1" parent="{legenda_layer_id}">',
                    f'          <mxGeometry x="{pos_x + legend_config["text_offset"]}" y="{pos_y + 5}" width="200" height="30" as="geometry"/>',
                    f'        </mxCell>'
                ])
                
                pos_y += legend_config["item_spacing"]
        
        # Close elements
        page_content.append("      </root>")
        page_content.append("    </mxGraphModel>")
        page_content.append("  </diagram>")
        
        # Check if page is empty
        if node_count == 0 and connection_count == 0:
            logger.info(f"Page '{page_def['name']}' is empty and will be omitted.")
            return None               
        return '\n'.join(page_content)

def process_file(connections_file, config, include_orphans=False, layouts_choice="cog", 
                regionalization=False, elements_file='elements.csv', 
                locations_file='locations.csv', hide_node_names=False, 
                hide_connection_layers=False, ignore_optional=False,
                filter_string=None, output_dir=None):
    """
    Processes a complete connection file
    
    Args:
        connections_file (str): Path to the connection file
        config (dict): Loaded configurations
        include_orphans (bool): Include unconnected nodes
        layouts_choice (str): String with selected layouts (e.g., "co")
        regionalization (bool): Activate regionalization
        elements_file (str): Path to elements file
        locations_file (str): Path to localities file
    """
    file_start = time.perf_counter()
    logger.info("⏱️ [START] Processing file: %s", connections_file)
    logger.debug("Parameters: orphans=%s, layouts=%s, regional=%s, hide_names=%s, hide_cnx=%s",
                include_orphans, layouts_choice, regionalization, 
                hide_node_names, hide_connection_layers)
    
    try:
        generator = TopologyGenerator(
            elements_file, 
            connections_file, 
            config, 
            include_orphans, 
            regionalization,
            locations_file,
            hide_node_names,
            hide_connection_layers,
            ignore_optional=ignore_optional,
            filter_string=filter_string
        )
        
        if not generator.valid:
            return False
            
        if not generator.read_elements():
            return False
            
        if not generator.read_connections():
            return False
            
        base_name = os.path.splitext(os.path.basename(connections_file))[0]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Ensure output directory exists
        if output_dir:
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                    logger.info(f"Created output directory: {output_dir}")
                except Exception as e:
                    logger.error(f"Error creating output directory {output_dir}: {e}")
                    return False
        else:
            output_dir = "."
        
        success = True
        
        # Layout mapping dictionary
        layout_map = {
            'c': ('circular', 'Circular'),
            'o': ('organico', 'Organic'),
            'g': ('geografico', 'Geographic'),
            'h': ('hierarquico', 'Hierarchical')
        }
        
        # List of layouts to process
        layouts_to_process = []
        for char in layouts_choice:
            if char in layout_map:
                layout_key, layout_name = layout_map[char]
                # Check geographic availability
                if char == 'g':
                    if not generator.has_geographic_data:
                        logger.warning("Geographic layout requested but no geographic data available. Skipping.")
                        continue
                layouts_to_process.append((layout_key, layout_name))
        
        generated_layouts = []
        # Generate only selected layouts
        for layout_key, layout_name in layouts_to_process:
            output_file = os.path.join(output_dir, f"{base_name}_{timestamp}_{layout_key}.drawio")
            if generator.generate_drawio(output_file, layout_key):
                generated_layouts.append(layout_name)
            else:
                success = False
        
        # Detailed performance log
        file_time = time.perf_counter() - file_start
        logger.info("✅ [SUCCESS] File processed in %.2fs | Layouts: %s | Nodes: %d | Connections: %d",
                  file_time, ', '.join(generated_layouts), 
                  len(generator.nodes), len(generator.connections))
        
        # Register elements without coordinates/siteid
        nodes_review = [n for n, d in generator.nodes.items() if d.get('layer') == "TO_REVIEW"]
        if nodes_review:
            review_log_file = os.path.join(output_dir, f"geographic_review_{base_name}_{timestamp}.log")
            try:
                with open(review_log_file, 'w', encoding='utf-8') as rf:
                    rf.write(f"GEOGRAPHIC REVIEW LOG - File: {connections_file}\n")
                    rf.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    rf.write("="*50 + "\n")
                    rf.write(f"Total elements needing review: {len(nodes_review)}\n")
                    rf.write("These elements are in the 'TO_REVIEW' layer and positioned at the center spiral.\n")
                    rf.write("="*50 + "\n\n")
                    for node in sorted(nodes_review):
                        data = generator.nodes[node]
                        rf.write(f"- {node} (Original Layer: {data.get('layer', 'Unknown')})\n")
                
                logger.info(f"📝 Review log generated: {os.path.basename(review_log_file)}")
            except Exception as e:
                logger.error(f"Error generating review log: {e}")

            nodes_list = ", ".join(nodes_review[:10])
            if len(nodes_review) > 10:
                nodes_list += f", ... (+{len(nodes_review) - 10} more)"
            logger.debug("%d elements moved to review layer: %s", 
                          len(nodes_review), nodes_list)
        
        return success
    except Exception as e:
        logger.exception("💥 [FAILURE] Error during processing")
        logger.error("Context: layouts=%s, regional=%s, elements=%s",
                   layouts_choice, regionalization, elements_file)
        return False

def main():
    global_start = time.perf_counter()
    verificar_dependencias() 
    
    # Configure argument parser
    parser = argparse.ArgumentParser(
        description='Network Topology Generator',
        add_help=False
    )
    
    # Positional arguments
    parser.add_argument(
        'files', 
        nargs='*', 
        help='Connection CSV files'
    )
    
    # Optional arguments
    parser.add_argument(
        '-g',
        metavar='DIRECTORY',
        default=None,
        help='Base directory for input files (connections.csv, elements.csv, locations.csv)'
    )
    parser.add_argument(
        '-y', 
        action='store_true', 
        help='Include unconnected nodes'
    )
    parser.add_argument(
        '-v', '--verbose', 
        action='store_true', 
        help='Verbose mode (show logs on screen)'
    )
    parser.add_argument(
        '-l', 
        action='store_true', 
        help='Generate logs to file'
    )
    parser.add_argument(
        '-t', 
        metavar='LAYOUTS', 
        default='cogh', 
        help='Layouts to generate (c=circular, o=organic, g=geographic, h=hierarchical). Default: cogh'
    )
    parser.add_argument(
        '-r', 
        action='store_true', 
        help='Activate regional layer separation'
    )
    parser.add_argument(
        '-e', 
        metavar='ELEMENTS', 
        default='elements.csv', 
        help='Path to elements file (optional)'
    )
    parser.add_argument(
        '-s', 
        metavar='LOCALITIES', 
        default='locations.csv', 
        help='Path to localities file (optional)'
    )
    parser.add_argument(
        '-h', '--help',
        action='store_true',
        help='Show quick help'
    )
    parser.add_argument(
        '-o', 
        metavar='OPTIONS', 
        default='', 
        help='Options: n (nodes without names), c (hide connection layers)'
    )
    parser.add_argument(
        '-d', 
        action='store_true', 
        help='Disregard optional definitions of elements and connections (use only config.json)'
    )
    parser.add_argument(
     '-c',
     type=str,
     default='config.json',
     help='Path to configuration file (default: config.json)'
    )
    
    parser.add_argument(
        '-w', '--out',
        metavar='OUT_DIR',
        default=None,
        help='Output directory for generated .drawio files'
    )
    
    parser.add_argument(
        '-f',
        metavar='FILTER',
        default=None,
        help='Filter nodes/layers: in/rn/ic/rc "filter1;filter2"'
    )    
    
    # Try to parse arguments
    try:
        args = parser.parse_args()
    except SystemExit:
        print(HELP_TEXT)
        sys.exit(1)
    
    # Handle help requests
    if args.help:
        print(HELP_TEXT)
        sys.exit(0)

    # Register initial information
    logger.info("🚀 Starting TopologyGenerator %s", versionctr)
    logger.info("Start time: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
 
    # Configure logging
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    
    # ================================================
    # DETAILED BASE DIRECTORY VALIDATION
    # ================================================
    base_dir = args.g
    logger.debug(f"Argument -g received: '{base_dir}'")
    
    # Helper function to normalize paths
    def normalize_path(path):
        return os.path.normpath(os.path.abspath(path)) if path else None
    
    def apply_base_dir(filename):
        if base_dir and filename:
            # Normalize and validate path
            normalized_dir = os.path.abspath(os.path.normpath(base_dir))
            if not os.path.exists(normalized_dir):
                logger.error(f"Base directory does not exist: {normalized_dir}")
                return filename
                
            full_path = os.path.join(normalized_dir, os.path.basename(filename))
            logger.debug(f"BaseDir applied: {filename} -> {full_path}")
            return full_path
        return filename

    # ================================================
    # RULES FOR -g (overrides other options)
    # ================================================
    if base_dir:
        # Forces the use of the base directory for elements/localities
        elements_file = os.path.join(base_dir, "elements.csv")
        locations_file = os.path.join(base_dir, "locations.csv")
        logger.info(f"Using fixed paths in base directory (-g active):")
        logger.info(f" - elements: {elements_file}")
        logger.info(f" - localities: {locations_file}")
    else:
        # No -g mode: respects -e and -s options if provided
        elements_file = apply_base_dir(args.e)
        locations_file = apply_base_dir(args.s)
    
    # ================================================
    # SMART FILE SEARCH
    # ================================================
    connections_files = []
    if args.files:
        # Process files explicitly provided by the user
        for f in args.files:
            full_path = apply_base_dir(f)
            if os.path.exists(full_path):
                connections_files.append(full_path)
            else:
                logger.error(f"File not found: {full_path}")
    elif base_dir:
        # -g mode: searches ONLY for "connections*.csv" in the base directory
        logger.info("Searching for connection files in the base directory...")
        search_path = os.path.join(base_dir, "connections*.csv")
        logger.debug(f"Search pattern: {search_path}")
        found_files = glob.glob(search_path, recursive=False)
        
        # Remove duplicates and validate
        seen = set()
        for f in found_files:
            if os.path.isfile(f) and f not in seen:
                seen.add(f)
                connections_files.append(f)
        
        if connections_files:
            logger.info(f"Found {len(connections_files)} connection file(s):")
            for f in connections_files:
                logger.info(f" - {os.path.basename(f)}")
        else:
            logger.warning("No connection files found in the directory")

    # ================================================
    # FINAL PATH VERIFICATION
    # ================================================
    logger.debug("="*50)
    logger.debug("PATH SUMMARY:")
    logger.debug(f"Base directory: {base_dir}")
    logger.debug(f"Elements file: {elements_file} -> Exists: {os.path.exists(elements_file) if elements_file else 'N/A'}")
    logger.debug(f"Localities file: {locations_file} -> Exists: {os.path.exists(locations_file) if locations_file else 'N/A'}")
    logger.debug(f"Connection files: {connections_files}")
    logger.debug("="*50)
    
    # If no files to process, run GUI
    if not connections_files:
        logger.info("No connection files found, starting GUI")
        run_gui()
        return

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    
    # Configure handlers based on options
    if args.verbose:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(stream_handler)
    
    if args.l:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Determine log directory (use output directory if provided)
        log_dir = args.out if args.out else "."
        if args.out and not os.path.exists(args.out):
            try:
                os.makedirs(args.out)
            except Exception as e:
                print(f"Error creating log directory {args.out}: {e}")
                log_dir = "."

        log_file = os.path.join(log_dir, f'topologia_log_{timestamp_str}.txt')
        error_file = os.path.join(log_dir, f'topologia_errors_{timestamp_str}.log')
        
        # Handler for general logs
        file_level = logging.DEBUG if args.verbose else logging.INFO
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(file_level)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        
        # Separate handler for errors
        error_handler = logging.FileHandler(error_file, mode='w', encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(error_handler)

        # New information log
        logger.info("Execution started via CLI")
        logger.info("Options used (different from default):")
        if args.y:
            logger.info("  -y (include orphan nodes)")
        if args.r:
            logger.info("  -r (regionalization)")
        if args.t != "cogh":
            logger.info("  -t %s (layouts)", args.t)
        if args.e != "elements.csv":
            logger.info("  -e %s (elements)", args.e)
        if args.s != "locations.csv":
            logger.info("  -s %s (localities)", args.s)
        if args.out:
            logger.info("  -w %s (output directory)", args.out)
        if args.o:
            logger.info("  -o %s (visualization)", args.o)
    
    # Register system information
    logger.debug("System: %s %s", sys.platform, platform.platform())
    logger.debug("Python: %s", sys.version)
    logger.debug("Dependencies: networkx=%s", nx.__version__)
    
    config = load_config(args.c) if hasattr(args, 'c') else load_config()
    
    # Validate layout choice
    valid_layouts = {'c', 'o', 'g', 'h'}
    layouts_choice = args.t.lower()
    
    if not all(char in valid_layouts for char in layouts_choice):
        logger.error("Option -t contains invalid characters: '%s'. Use only: c, o, g, h", layouts_choice)
        print(f"Error: option -t contains invalid characters: '{layouts_choice}'. Use only: c, o, g, h")
        sys.exit(1)

    # Check file existence
    valid_files = []
    for f in connections_files:
        if os.path.exists(f):
            valid_files.append(f)
        else:
            logger.error(f"File not found: {f}")
    
    if not valid_files:
        logger.error("No valid CSV file specified")
        print("Error: No valid CSV file")
        sys.exit(1)
    
    # Process visualization options
    hide_node_names = 'n' in args.o
    hide_connection_layers = 'c' in args.o
    
    # Process each file with new options
    results = []
    for connections_file in valid_files:
        results.append(process_file(
            connections_file=connections_file, 
            config=config, 
            include_orphans=args.y, 
            layouts_choice=layouts_choice, 
            regionalization=args.r,
            elements_file=elements_file,
            locations_file=locations_file,
            hide_node_names=hide_node_names,
            hide_connection_layers=hide_connection_layers,
            ignore_optional=args.d,
            filter_string=args.f,
            output_dir=args.out
        ))
    
    # Final execution report
    success_count = sum(1 for r in results if r)
    total_files = len(valid_files)
    total_time = time.perf_counter() - global_start
    
    logger.info("✅ PROCESSING COMPLETED")
    logger.info("   Files processed: %d/%d successfully", success_count, total_files)
    logger.info("   Total time: %.2f seconds", total_time)
    log_memory_usage("End of processing")
    
    if success_count < total_files:
        logger.error("⛔ One or more files failed during processing")
        sys.exit(1)
        
    logger.info("✨ All operations completed successfully")

if __name__ == "__main__":
    main()

