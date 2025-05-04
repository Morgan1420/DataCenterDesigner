from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QLineEdit, QGroupBox, QFormLayout, QSpinBox, QListWidget, QListWidgetItem,
    QTabWidget, QWidget, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt
from screens.interior_screen_modules import Subspace

class SubspaceWizard(QDialog):
    """A wizard to help with designing subspaces in the data center"""
    
    def __init__(self, parent_screen):
        super().__init__(parent=parent_screen)
        self.parent_screen = parent_screen
        self.setWindowTitle("Subspace Wizard")
        self.setMinimumSize(800, 600)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        
        # Create tabs for different wizard functions
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create create tab
        self.create_tab = QWidget()
        self.tab_widget.addTab(self.create_tab, "Create Subspace")
        self._setup_create_tab()
        
        # Create optimize tab
        self.optimize_tab = QWidget()
        self.tab_widget.addTab(self.optimize_tab, "Optimize Subspace")
        self._setup_optimize_tab()
        
        # Create templates tab
        self.templates_tab = QWidget()
        self.tab_widget.addTab(self.templates_tab, "Templates")
        self._setup_templates_tab()
        
        # Create close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        self.main_layout.addWidget(self.close_button)
    
    def _setup_create_tab(self):
        """Setup the Create Subspace tab"""
        layout = QVBoxLayout(self.create_tab)
        
        # Form for subspace properties
        properties_group = QGroupBox("Subspace Properties")
        form_layout = QFormLayout()
        properties_group.setLayout(form_layout)
        
        # Name input
        self.name_input = QLineEdit("New Subspace")
        form_layout.addRow("Name:", self.name_input)
        
        # Size inputs
        self.size_x_input = QSpinBox()
        self.size_x_input.setRange(10, 1000)
        self.size_x_input.setValue(100)
        form_layout.addRow("Size X:", self.size_x_input)
        
        self.size_y_input = QSpinBox()
        self.size_y_input.setRange(10, 1000)
        self.size_y_input.setValue(100)
        form_layout.addRow("Size Y:", self.size_y_input)
        
        # Position inputs
        self.position_x_input = QSpinBox()
        self.position_x_input.setRange(0, 5000)
        self.position_x_input.setValue(50)
        form_layout.addRow("Position X:", self.position_x_input)
        
        self.position_y_input = QSpinBox()
        self.position_y_input.setRange(0, 5000)
        self.position_y_input.setValue(50)
        form_layout.addRow("Position Y:", self.position_y_input)
        
        layout.addWidget(properties_group)
        
        # Recommended modules section
        modules_group = QGroupBox("Recommended Modules")
        modules_layout = QVBoxLayout()
        modules_group.setLayout(modules_layout)
        
        self.module_type_combo = QComboBox()
        # Add module categories based on available modules
        module_categories = self._get_module_categories()
        self.module_type_combo.addItems(["All"] + module_categories)
        self.module_type_combo.currentTextChanged.connect(self._filter_recommended_modules)
        modules_layout.addWidget(self.module_type_combo)
        
        # Create the list of recommended modules
        self.recommended_modules_list = QListWidget()
        modules_layout.addWidget(self.recommended_modules_list)
        
        # Populate the recommended modules list
        self._populate_recommended_modules()
        
        layout.addWidget(modules_group)
        
        # Create and add button
        self.create_button = QPushButton("Create Subspace")
        self.create_button.clicked.connect(self._create_subspace)
        layout.addWidget(self.create_button)
    
    def _setup_optimize_tab(self):
        """Setup the Optimize Subspace tab"""
        layout = QVBoxLayout(self.optimize_tab)
        
        # Subspace selection
        selection_group = QGroupBox("Select Subspace to Optimize")
        selection_layout = QVBoxLayout()
        selection_group.setLayout(selection_layout)
        
        self.subspace_combo = QComboBox()
        self._populate_subspace_combo()
        selection_layout.addWidget(self.subspace_combo)
        
        layout.addWidget(selection_group)
        
        # Optimization options
        options_group = QGroupBox("Optimization Options")
        options_layout = QFormLayout()
        options_group.setLayout(options_layout)
        
        self.optimize_space_checkbox = QComboBox()
        self.optimize_space_checkbox.addItems(["Optimize for Space Efficiency", "Optimize for Power Efficiency", "Optimize for Network Connectivity"])
        options_layout.addRow("Optimization Target:", self.optimize_space_checkbox)
        
        layout.addWidget(options_group)
        
        # Optimize button
        self.optimize_button = QPushButton("Optimize Subspace")
        self.optimize_button.clicked.connect(self._optimize_subspace)
        layout.addWidget(self.optimize_button)
        
        # Results area
        results_group = QGroupBox("Optimization Results")
        results_layout = QVBoxLayout()
        results_group.setLayout(results_layout)
        
        self.results_label = QLabel("Run optimization to see results")
        results_layout.addWidget(self.results_label)
        
        layout.addWidget(results_group)
    
    def _setup_templates_tab(self):
        """Setup the Templates tab"""
        layout = QVBoxLayout(self.templates_tab)
        
        # Template selection
        template_group = QGroupBox("Select Template")
        template_layout = QVBoxLayout()
        template_group.setLayout(template_layout)
        
        # Add template types
        self.template_list = QListWidget()
        template_layout.addWidget(self.template_list)
        
        # Add some example templates
        templates = [
            "Server Room (Small)",
            "Server Room (Medium)",
            "Server Room (Large)",
            "Network Hub",
            "Storage Cluster",
            "High-Performance Computing Cluster",
            "Power Distribution Zone",
            "Cooling Zone"
        ]
        
        for template in templates:
            self.template_list.addItem(template)
        
        layout.addWidget(template_group)
        
        # Template preview
        preview_group = QGroupBox("Template Preview")
        preview_layout = QVBoxLayout()
        preview_group.setLayout(preview_layout)
        
        self.preview_label = QLabel("Select a template to see preview")
        preview_layout.addWidget(self.preview_label)
        
        layout.addWidget(preview_group)
        
        # Apply template button
        self.apply_button = QPushButton("Apply Template")
        self.apply_button.clicked.connect(self._apply_template)
        layout.addWidget(self.apply_button)
    
    def _get_module_categories(self):
        """Get categories of available modules"""
        categories = set()
        for module in self.parent_screen.available_modules:
            # Extract category from module ID (e.g., "Data_Rack_100" -> "Data_Rack")
            parts = module.id.split('_')
            if len(parts) >= 2:
                category = "_".join(parts[:-1])
                categories.add(category)
        
        return sorted(list(categories))
    
    def _populate_recommended_modules(self, category=None):
        """Populate the list of recommended modules"""
        self.recommended_modules_list.clear()
        
        for module in self.parent_screen.available_modules:
            if category and category != "All":
                # Filter by category
                parts = module.id.split('_')
                if len(parts) >= 2:
                    module_category = "_".join(parts[:-1])
                    if module_category != category:
                        continue
            
            # Create widget with checkbox for each module
            item = QListWidgetItem()
            widget = QWidget()
            layout = QHBoxLayout(widget)
            
            label = QLabel(module.id)
            layout.addWidget(label)
            
            add_button = QPushButton("Add")
            add_button.clicked.connect(lambda checked=False, m=module: self._add_module_to_list(m))
            layout.addWidget(add_button)
            
            item.setSizeHint(widget.sizeHint())
            self.recommended_modules_list.addItem(item)
            self.recommended_modules_list.setItemWidget(item, widget)
    
    def _filter_recommended_modules(self, category):
        """Filter the recommended modules list by category"""
        self._populate_recommended_modules(category)
    
    def _populate_subspace_combo(self):
        """Populate the subspace selection combo box"""
        self.subspace_combo.clear()
        
        for subspace in self.parent_screen.interior_space.get_subspaces():
            name = getattr(subspace, 'name', f"Subspace ({subspace.x}, {subspace.y})")
            self.subspace_combo.addItem(name, subspace)
    
    def _create_subspace(self):
        """Create a new subspace with the specified properties"""
        name = self.name_input.text()
        size_x = self.size_x_input.value()
        size_y = self.size_y_input.value()
        position_x = self.position_x_input.value()
        position_y = self.position_y_input.value()
        
        # Create the subspace
        subspace = Subspace(position_x, position_y)
        subspace.resize(size_x, size_y)
        subspace.name = name
        
        # Add the subspace to the interior space
        self.parent_screen.interior_space.add_subspace(subspace)
        
        # Update the interior screen
        self.parent_screen._draw_space()
        self.parent_screen._add_subspace_editor(subspace)
        
        # Show success message
        QMessageBox.information(self, "Success", f"Subspace '{name}' created successfully!")
        
        # Update the subspace combo box in the optimize tab
        self._populate_subspace_combo()
    
    def _add_module_to_list(self, module):
        """Add a module to the selected subspace"""
        # Get the currently selected subspace in the optimize tab
        index = self.subspace_combo.currentIndex()
        if index == -1:
            QMessageBox.warning(self, "Error", "Please select a subspace first!")
            return
        
        subspace = self.subspace_combo.currentData()
        if not subspace:
            QMessageBox.warning(self, "Error", "No subspace selected!")
            return
        
        # Add the module to the subspace
        self.parent_screen._add_module_to_subspace(module, subspace)
        
        # Show success message
        QMessageBox.information(self, "Success", f"Module '{module.id}' added to subspace!")
    
    def _optimize_subspace(self):
        """Optimize the selected subspace"""
        # Get the currently selected subspace
        index = self.subspace_combo.currentIndex()
        if index == -1:
            QMessageBox.warning(self, "Error", "Please select a subspace first!")
            return
        
        subspace = self.subspace_combo.currentData()
        if not subspace:
            QMessageBox.warning(self, "Error", "No subspace selected!")
            return
        
        # Get the optimization target
        target = self.optimize_space_checkbox.currentText()
        
        # Implement a simple optimization algorithm (just a placeholder)
        # In a real implementation, this would do more sophisticated optimization
        if target == "Optimize for Space Efficiency":
            self._optimize_for_space(subspace)
        elif target == "Optimize for Power Efficiency":
            self._optimize_for_power(subspace)
        elif target == "Optimize for Network Connectivity":
            self._optimize_for_network(subspace)
        
        # Update the results label
        self.results_label.setText(f"Optimization for '{target}' completed!")
        
        # Refresh the subspace view
        subspace_coords = (subspace.x, subspace.y)
        if subspace_coords in self.parent_screen.subspace_scenes:
            subspace_modules_list = self.parent_screen.subspace_module_lists.get(subspace_coords)
            subspace_scene = self.parent_screen.subspace_scenes.get(subspace_coords)
            self.parent_screen._update_subspace_editor(subspace, subspace_modules_list, subspace_scene)
    
    def _optimize_for_space(self, subspace):
        """Optimize the subspace for space efficiency"""
        # Simple grid layout algorithm for modules
        modules = subspace.get_modules()
        if not modules:
            return
        
        # Sort modules by size (largest first)
        modules.sort(key=lambda m: m.size_x * m.size_y, reverse=True)
        
        # Simple grid placement
        x, y = 10, 10  # Start with some padding
        max_height_in_row = 0
        max_width = subspace.size_x - 20  # Allow some padding
        
        for module in modules:
            # If we'd exceed the width, move to next row
            if x + module.size_x > max_width:
                x = 10
                y += max_height_in_row + 10  # Move down by the tallest module in the row + padding
                max_height_in_row = 0
            
            # Set the module position
            module.x = x
            module.y = y
            
            # Update position for next module
            x += module.size_x + 10  # Add some padding
            max_height_in_row = max(max_height_in_row, module.size_y)
    
    def _optimize_for_power(self, subspace):
        """Optimize the subspace for power efficiency"""
        # Placeholder for power optimization
        # In a real implementation, this would analyze power connections
        # and optimize module placement based on power requirements
        pass
    
    def _optimize_for_network(self, subspace):
        """Optimize the subspace for network connectivity"""
        # Placeholder for network optimization
        # In a real implementation, this would analyze network connections
        # and optimize module placement based on connectivity requirements
        pass
    
    def _apply_template(self):
        """Apply the selected template to create a new subspace"""
        # Get the selected template
        selected_items = self.template_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a template first!")
            return
        
        template_name = selected_items[0].text()
        
        # Create a new subspace based on the template
        if "Server Room" in template_name:
            self._create_server_room_template(template_name)
        elif "Network Hub" in template_name:
            self._create_network_hub_template()
        elif "Storage Cluster" in template_name:
            self._create_storage_cluster_template()
        elif "High-Performance Computing Cluster" in template_name:
            self._create_hpc_cluster_template()
        elif "Power Distribution Zone" in template_name:
            self._create_power_distribution_template()
        elif "Cooling Zone" in template_name:
            self._create_cooling_zone_template()
    
    def _create_server_room_template(self, template_name):
        """Create a server room template based on the specified size"""
        # Determine the size based on the template name
        if "Small" in template_name:
            size_x, size_y = 150, 150
            server_count = 3
        elif "Medium" in template_name:
            size_x, size_y = 250, 250
            server_count = 6
        else:  # Large
            size_x, size_y = 350, 350
            server_count = 10
        
        # Create the subspace
        subspace = Subspace(50, 50)
        subspace.resize(size_x, size_y)
        subspace.name = template_name
        
        # Add the subspace to the interior space
        self.parent_screen.interior_space.add_subspace(subspace)
        
        # Find server rack modules
        server_modules = []
        for module in self.parent_screen.available_modules:
            if "Server_Rack" in module.id:
                server_modules.append(module)
        
        # Add server rack modules
        if server_modules:
            server_module = server_modules[0]  # Use the first server rack type
            
            # Add server racks in a grid layout
            grid_cols = min(4, server_count)
            for i in range(server_count):
                col = i % grid_cols
                row = i // grid_cols
                
                # Add the module
                self.parent_screen._add_module_to_subspace(server_module, subspace)
                
                # Position the module (this is simplified - the actual _add_module_to_subspace handles positioning)
                last_module = subspace.get_modules()[-1]
                last_module.x = 20 + col * (server_module.size_x + 10)
                last_module.y = 20 + row * (server_module.size_y + 10)
        
        # Find network rack module
        network_modules = []
        for module in self.parent_screen.available_modules:
            if "Network_Rack" in module.id:
                network_modules.append(module)
        
        # Add one network rack
        if network_modules:
            network_module = network_modules[0]
            self.parent_screen._add_module_to_subspace(network_module, subspace)
            
            # Position at the end of the row
            last_module = subspace.get_modules()[-1]
            last_module.x = 20
            last_module.y = size_y - network_module.size_y - 20
        
        # Update the interior screen
        self.parent_screen._draw_space()
        self.parent_screen._add_subspace_editor(subspace)
        
        # Show success message
        QMessageBox.information(self, "Success", f"Template '{template_name}' applied successfully!")
        
        # Update the subspace combo box in the optimize tab
        self._populate_subspace_combo()
    
    def _create_network_hub_template(self):
        """Create a network hub template"""
        # Similar implementation to the server room template
        # but with network equipment focus
        pass
    
    def _create_storage_cluster_template(self):
        """Create a storage cluster template"""
        # Implementation for storage cluster template
        pass
    
    def _create_hpc_cluster_template(self):
        """Create a high-performance computing cluster template"""
        # Implementation for HPC cluster template
        pass
    
    def _create_power_distribution_template(self):
        """Create a power distribution zone template"""
        # Implementation for power distribution template
        pass
    
    def _create_cooling_zone_template(self):
        """Create a cooling zone template"""
        # Implementation for cooling zone template
        pass

