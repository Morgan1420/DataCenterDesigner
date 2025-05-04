from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QLineEdit, QGroupBox, QFormLayout, QSpinBox, QListWidget, QListWidgetItem,
    QTabWidget, QWidget, QMessageBox, QScrollArea, QDoubleSpinBox, QFrame
)
from PySide6.QtCore import Qt
from screens.exterior_screen_modules import Subspace
from modules import load_exterior_modules, Module
import os
import math
import random

class ConditionWidget(QWidget):
    """Widget representing a single condition with 4 elements (3 dropdowns, 1 number input, and a delete button)"""
    
    def __init__(self, parent=None, delete_callback=None):
        super().__init__(parent)
        self.delete_callback = delete_callback
        
        # Create horizontal layout for the condition
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # First dropdown - Condition type
        self.condition_type = QComboBox()
        self.condition_type.addItems(["Input", "Output", "Size", "Module"])
        self.condition_type.currentIndexChanged.connect(self.update_property_options)
        self.layout.addWidget(self.condition_type)
        
        # Second dropdown - Property name
        self.property_name = QComboBox()
        self.layout.addWidget(self.property_name)
        
        # Third dropdown - Condition operator
        self.condition_operator = QComboBox()
        self.condition_operator.addItems([">", "<", "=", ">=", "<="])
        self.layout.addWidget(self.condition_operator)
        
        # Number input - Value
        self.value = QDoubleSpinBox()
        self.value.setMinimum(0)
        self.value.setMaximum(10000)
        self.value.setValue(100)
        self.layout.addWidget(self.value)
        
        # Delete button
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_self)
        self.layout.addWidget(self.delete_button)
        
        # Initialize second dropdown based on default selection in first dropdown
        self.update_property_options(0)
    
    def update_property_options(self, index):
        """Update options in the second dropdown based on selection in the first dropdown"""
        self.property_name.clear()
        
        if self.condition_type.currentText() == "Input" or self.condition_type.currentText() == "Output":
            # For Input or Output, show resource types
            self.property_name.addItems([
                "Grid_Connection", "Price", "Usable_Power", "Distilled_Water", 
                "Chilled_Water", "Water_Connection", "Fresh_Water"
            ])
        elif self.condition_type.currentText() == "Size":
            # For Size, show X or Y options
            self.property_name.addItems(["X", "Y"])
        elif self.condition_type.currentText() == "Module":
            # For Module, show available exterior modules
            module_names = self.get_exterior_module_names()
            self.property_name.addItems(module_names)
    
    def get_exterior_module_names(self):
        """Get the names of all available exterior modules from the CSV files"""
        module_names = []
        modules = load_exterior_modules("CSV/ExteriorModules/")
        
        for module in modules:
            module_names.append(module.id)
        
        return module_names
    
    def delete_self(self):
        """Delete this condition widget"""
        if self.delete_callback:
            self.delete_callback(self)
    
    def get_condition(self):
        """Return a dictionary representing the condition"""
        return {
            "type": self.condition_type.currentText(),
            "property": self.property_name.currentText(),
            "operator": self.condition_operator.currentText(),
            "value": self.value.value()
        }


class SubspaceWizard(QDialog):
    """A wizard to help with designing subspaces in the data center based on conditions"""
    
    def __init__(self, parent_screen, available_modules):
        super().__init__(parent=parent_screen)
        self.parent_screen = parent_screen
        self.available_modules = available_modules
        self.setWindowTitle("Subspace Wizard")
        self.setMinimumSize(800, 600)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        
        # Add a title label
        self.title_label = QLabel("Subspace Generator Wizard")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.title_label)
        
        # Add instructions
        self.instructions = QLabel("Define conditions for your subspace by adding rules below.")
        self.instructions.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.instructions)
        
        # Create a scroll area for all conditions
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(300)
        
        # Create container widget for the scroll area
        self.scroll_container = QWidget()
        self.conditions_layout = QVBoxLayout(self.scroll_container)
        
        # Add the container to the scroll area
        self.scroll_area.setWidget(self.scroll_container)
        self.main_layout.addWidget(self.scroll_area)
        
        # Add condition button
        self.add_condition_button = QPushButton("Add Condition")
        self.add_condition_button.clicked.connect(self.add_condition)
        self.main_layout.addWidget(self.add_condition_button)
        
        # Add a separator
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        self.main_layout.addWidget(self.separator)
        
        # Generate button
        self.generate_button = QPushButton("Generate Subspace")
        self.generate_button.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white; padding: 8px;")
        self.generate_button.clicked.connect(self.generate_subspace)
        self.main_layout.addWidget(self.generate_button)
        
        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        self.main_layout.addWidget(self.close_button)
        
        # Add an initial condition
        self.add_condition()
        
        self.modulesAdded = []
    
    def add_condition(self):
        """Add a new condition to the scroll area"""
        condition = ConditionWidget(delete_callback=self.delete_condition)
        self.conditions_layout.addWidget(condition)
    
    def delete_condition(self, condition_widget):
        """Delete a specific condition widget"""
        if condition_widget:
            condition_widget.setParent(None)
            condition_widget.deleteLater()
    
    def generate_subspace(self):
        """Generate a subspace based on the defined conditions"""
        try:
            # Collect all conditions from the UI
            conditions = []
            for i in range(self.conditions_layout.count()):
                item = self.conditions_layout.itemAt(i)
                if item and item.widget():
                    condition_widget = item.widget()
                    if hasattr(condition_widget, 'get_condition'):
                        conditions.append(condition_widget.get_condition())
            
            if not conditions:
                QMessageBox.warning(
                    self,
                    "No Conditions",
                    "Please add at least one condition to generate a subspace."
                )
                return
            
            # Load all available modules
            all_modules = self.available_modules
            
            # Filter modules based on conditions
            depth = 3
            self.filter_modules_by_conditions(all_modules, conditions, depth)
            
            if not self.modulesAdded:
                QMessageBox.warning(
                    self,
                    "No Matching Modules",
                    "No modules found that match all conditions. Try adjusting your criteria."
                )
                return
            # print("Modules added:", self.modulesAdded)
            self.create_subspace_with_modules(self.modulesAdded)
            self.modulesAdded = []
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate subspace: {str(e)}"
            )
    
    def filter_modules_by_conditions(self, modules, conditions, depth):
        """Filter modules based on the specified conditions"""
        totalConditions = len(conditions)

        # Initialize the dictionary to store modules and their condition match count
        matching_modules = {}

        # Iterate through modules and count how many conditions each one meets
        for module in modules:
            # Check if the module meets all conditions
            for condition in conditions:
                condition_type = condition["type"]
                property_name = condition["property"]
                operator = condition["operator"]
                value = condition["value"]
                condition_weight = 0 # Default weight for the condition

                try: # Use try-except to handle potential conversion errors gracefully
                    if condition_type == "Input":
                    # Check if module has the specified input property
                        if property_name in module.inputs:
                            # Convert module input value to float for comparison
                            module_value = float(module.inputs[property_name])
                            condition_weight = min(module_value, value)/max(module_value, value) 
                            # Compare using the specified operator
                            if self.compare_values(module_value, value, operator):
                                condition_weight = 1 # Set weight to 1 if condition is satisfied
                        elif self.compare_values(0, value, operator):
                            # Per si tenim < que, doncs que ho tingui en compte per les entrades com que no té res
                            condition_weight = 1
                    elif condition_type == "Output":
                    # Check if module has the specified output property
                        if property_name in module.outputs:
                            # Convert module output value to float for comparison
                            module_value = float(module.outputs[property_name])
                            condition_weight = min(module_value, value)/max(module_value, value) 
                            # Compare using the specified operator
                            if self.compare_values(module_value, value, operator):
                                condition_weight = 1

                    elif condition_type == "Size":
                    # Check module size (X or Y dimension)
                        module_value = None
                        if property_name == "X":
                            module_value = module.size_x
                        elif property_name == "Y":
                            module_value = module.size_y

                        # If a valid dimension was found, compare it
                        if module_value is not None:
                            if self.compare_values(float(module_value), value, operator):
                                condition_weight = 1

                    elif condition_type == "Module":
                    # Check if the module's ID matches the specified property name
                    # Operator and value are ignored for this type based on original logic
                        if module.id == property_name:
                            condition_weight = 1

                except (ValueError, TypeError):
                 # If conversion to float fails (e.g., non-numeric value), treat condition as not met
                 pass

                # Store the module as the key and the count of met conditions as the value
                matching_modules[module] = condition_weight
                
        # Look for most suitable module
        best_module = max(matching_modules, key=matching_modules.get, default=None)
        
        print("Best module found:", best_module)
        
        if best_module is not None and matching_modules[best_module] == totalConditions:
            self.modulesAdded.append(best_module)
            # If the best module meets all conditions, create a subspace with it
            return 0
        else:
            # If the best module doesn't meet all conditions, inform the user and ask to proceed.
            unmet_conditions_desc = []
            extra_inputs_needed_desc = []

            # Check original conditions against the best module to find unmet ones
            for condition in conditions:
                condition_type = condition["type"]
                property_name = condition["property"]
                operator = condition["operator"]
                value = condition["value"]
                condition_satisfied = False
                module_value_str = "N/A" # Default description for module's value

                try:
                    if condition_type == "Input":
                        if property_name in best_module.inputs:
                            module_value = float(best_module.inputs[property_name])
                            condition["value"] = value - module_value
                            if value <= module_value:
                                condition_satisfied = True
                        else:
                             module_value_str = "Not Provided" # Module doesn't have this input property
                    elif condition_type == "Output":
                         if property_name in best_module.outputs:
                            module_value = float(best_module.inputs[property_name])
                            condition["value"] = value - module_value
                            if value <= module_value:
                                condition_satisfied = True
                         else:
                             module_value_str = "Not Provided" # Module doesn't have this output property
                    elif condition_type == "Size":
                        module_dim_value = None
                        if property_name == "X":
                            module_dim_value = best_module.size_x
                            module_value_str = str(module_dim_value)
                        elif property_name == "Y":
                            module_dim_value = best_module.size_y
                            module_value_str = str(module_dim_value)
                        else:
                             module_value_str = "N/A" # Should not happen with current UI

                        if module_dim_value is not None:
                             # Compare the dimension value
                             if self.compare_values(float(module_dim_value), value, operator):
                                condition_satisfied = True
                    elif condition_type == "Module":
                         # For module type condition, check if the module ID matches the property name
                         module_value_str = best_module.id
                         if best_module.id == property_name:
                            # Operator and value are ignored for this type based on original logic
                            condition_satisfied = True
                         else:
                             # Explicitly state the module ID doesn't match if this was the condition
                             module_value_str = f"Is '{best_module.id}'"

                except (ValueError, TypeError) as e:
                    # Handle cases where module value isn't numeric when expected for comparison
                    module_value_str = f"Error ({e})" # Report error in description
                    pass # Condition remains unsatisfied

                # If the condition was not satisfied by the best module, record it
                if not condition_satisfied:
                    condition_desc = f"{condition_type} '{property_name}' {operator} {value}"
                    unmet_conditions_desc.append(
                        f"- Required: {condition_desc} (Module: {module_value_str})"
                    )

            # Check module's inputs to see if any were not part of the original conditions
            # These represent additional requirements the module brings.
            original_input_conditions_props = {
                c["property"] for c in conditions if c["type"] == "Input"
            }
            for input_prop, input_val_str in best_module.inputs.items():
                 if input_prop not in original_input_conditions_props:
                     try:
                         # Attempt to convert to float for a clearer requirement description
                         input_val = float(input_val_str)
                         # Assume the module needs at least this value if not specified otherwise
                         extra_inputs_needed_desc.append(
                             f"- Input '{input_prop}': Requires >= {input_val}"
                         )
                     except (ValueError, TypeError):
                         # Handle non-numeric input requirements
                         extra_inputs_needed_desc.append(
                             f"- Input '{input_prop}': Requires '{input_val_str}'"
                         )

            # Add the best module to the list of added modules
            self.modulesAdded.append(best_module)
            if(depth > 0):
                self.filter_modules_by_conditions(modules, conditions, depth - 1)
            else:
                # Arribar aquí vol dir que no hem pogut solucionar-ho tot
                self.modulesAdded = [] 
            return 0
        
    
    def compare_values(self, module_value, condition_value, operator):
        """Compare module value with condition value using the specified operator"""
        if operator == ">":
            return module_value > condition_value
        elif operator == "<":
            return module_value < condition_value
        elif operator == "=":
            return math.isclose(module_value, condition_value, rel_tol=1e-5)
        elif operator == ">=":
            return module_value >= condition_value
        elif operator == "<=":
            return module_value <= condition_value
        return False
    
    def create_subspace_with_modules(self, modules):
        """Create a subspace containing the specified module"""
        
        # Create a new subspace
        new_subspace = Subspace(50, 50)
        
        for module in modules:        
            # Add module to the subspace
            new_subspace.add_module(module)
        
        # Add the subspace to the exterior screen
        self.parent_screen.add_subspace(new_subspace)
        
        # Close the wizard
        self.accept()
        
        # Show confirmation message
        QMessageBox.information(
            self.parent_screen,
            "Subspace Generated",
            f"Successfully created a subspace containing a {module.id} module."
        )

