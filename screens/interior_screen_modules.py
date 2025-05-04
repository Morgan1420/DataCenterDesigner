from modules import Module
from PySide6.QtWidgets import QGraphicsLineItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QColor

PADDING = 10  # Define padding between modules


class Subspace:
    """Represents a subspace with x and y dimensions."""
    def __init__(self, size_x: float, size_y: float):
        self.size_x = size_x
        self.size_y = size_y
        self.x = 0.0
        self.y = 0.0
        self.inputs: dict[str, float] = {}  # For reference the values can be: {"Water_Connection": 0.0, "Fresh_Water": 0.0, "Distlled_Water": 0.0, "Chilled_Water": 0.0, "Grid_Connection": 0.0, "Usable_Power": 0.0}  
        self.outputs: dict[str, float] = {}  # {"Water_Connection": 0.0, "Fresh_Water": 0.0, "Distlled_Water": 0.0, "Chilled_Water": 0.0, "Grid_Connection": 0.0, "Usable_Power": 0.0}  
        self.modules: list[Module] = []
        # Tracking for grid placement
        self._current_placement_x = PADDING
        self._current_placement_y = PADDING
        self._max_y_in_row = PADDING
        # Track boundary connections
        self.boundary_connections = []
        
    def add_input(self, input: str, amount: float):
        """Adds an input to the subspace."""
        if input in self.inputs:
            self.inputs[input] += amount
        else:
            self.inputs[input] = amount
    
    def add_output(self, output: str, amount: float):
        """Adds an output to the subspace."""
        if output in self.outputs:
            self.outputs[output] += amount
        else:
            self.outputs[output] = amount
    
    def remove_input(self, input: str, value: float = 0.0):
        """Removes an input from the subspace."""
        if input in self.inputs:
            self.inputs[input] -= value
            if self.inputs[input] <= 0:
                del self.inputs[input]
    
    def remove_output(self, output: str, value: float = 0.0):
        """Removes an output from the subspace."""
        if output in self.outputs:
            self.outputs[output] -= value
            if self.outputs[output] <= 0:
                del self.outputs[output]
    
    def remove_all_inputs(self):
        """Removes all inputs from the subspace."""
        self.inputs.clear()
        
    def remove_all_outputs(self):
        """Removes all outputs from the subspace."""
        self.outputs.clear()
        
    def update_boundary_connection(self, data_type: str, is_input: bool, amount: float, add: bool = True):
        """Updates inputs/outputs based on boundary connections.
        
        Args:
            data_type: The type of data being connected
            is_input: True if connecting to an input boundary circle, False for output
            amount: The amount of data flowing through the connection
            add: True to add a connection, False to remove a connection
        """
        if add:
            # Adding a connection
            if is_input:
                # Connection to an input boundary adds to subspace inputs
                self.add_input(data_type, amount)
            else:
                # Connection to an output boundary adds to subspace outputs
                self.add_output(data_type, amount)
        else:
            # Removing a connection
            if is_input:
                # Connection to an input boundary removes from subspace inputs
                if data_type in self.inputs:
                    self.inputs[data_type] -= amount
                    if self.inputs[data_type] <= 0:
                        del self.inputs[data_type]
            else:
                # Connection to an output boundary removes from subspace outputs
                if data_type in self.outputs:
                    self.outputs[data_type] -= amount
                    if self.outputs[data_type] <= 0:
                        del self.outputs[data_type]
            
    def get_inputs(self) -> dict[str, float]:
        """Returns the dictionary of inputs."""
        return self.inputs  
    
    def get_outputs(self) -> dict[str, float]:
        """Returns the dictionary of outputs."""
        return self.outputs
    
    def resize(self, new_x: float, new_y: float):
        """Resizes the subspace to new dimensions."""
        self.size_x = new_x
        self.size_y = new_y
    
    def get_dimensions(self) -> tuple[float, float]:
        """Returns the dimensions of the subspace."""
        return self.size_x, self.size_y
    
    def set_position(self, x: float, y: float):
        """Sets the position of the subspace."""
        self.x = x
        self.y = y
    
    def add_module(self, module: Module):
        """Adds a module to the subspace, calculates its position, and resizes the subspace."""

        # --- Simple Grid Placement Logic ---
        # Use a reasonable default size if module size is 0
        module_draw_width = module.size_x if module.size_x > 0 else 20
        module_draw_height = module.size_y if module.size_y > 0 else 20

        if self._current_placement_x + module_draw_width + PADDING > self.size_x:
            # Move to the next row
            self._current_placement_y = self._max_y_in_row + PADDING
            self._current_placement_x = PADDING

        # Set module position
        module_x = self._current_placement_x
        module_y = self._current_placement_y
        module.set_position(module_x, module_y)

        # Update placement trackers for the next module
        self._current_placement_x += module_draw_width + PADDING
        self._max_y_in_row = max(self._max_y_in_row, module_y + module_draw_height)
        # --- End Placement Logic ---

        self.modules.append(module)

        # --- Dynamic Resizing ---
        # Ensure subspace is large enough to contain the new module including padding
        required_width = self._current_placement_x  # Width needed is the current x placement
        required_height = self._max_y_in_row + PADDING  # Height needed is the max y reached + padding

        # Expand dimensions as needed
        self.size_x = max(self.size_x, required_width)
        self.size_y = max(self.size_y, required_height)
        # --- End Resizing ---

        # NOTE: Removed automatic addition of module inputs and outputs to the subspace
        # Subspace inputs/outputs will be determined by boundary connections instead

    def get_modules(self) -> list[Module]:
        """Returns the list of modules."""
        return self.modules
    
    def remove_module(self, module: Module):
        """Removes a module from the subspace and resizes the subspace if needed."""
        if module in self.modules:
            # Remove the module from our list
            self.modules.remove(module)
            
            # NOTE: Removed automatic removal of module inputs/outputs from the subspace
            # Subspace inputs/outputs are now determined by boundary connections instead
            
            # Recalculate the bounding box based on the remaining modules
            if self.modules:
                # Find the maximum x and y coordinates needed by remaining modules
                max_x = PADDING  # Minimum padding
                max_y = PADDING  # Minimum padding
                
                for mod in self.modules:
                    # Calculate the right and bottom edges of each module
                    mod_right = mod.x + mod.size_x
                    mod_bottom = mod.y + mod.size_y
                    
                    # Update max coordinates
                    max_x = max(max_x, mod_right + PADDING)
                    max_y = max(max_y, mod_bottom + PADDING)
                
                # Resize the subspace to fit the remaining modules (with padding)
                self.size_x = max(max_x, PADDING * 2)  # Ensure minimum size
                self.size_y = max(max_y, PADDING * 2)  # Ensure minimum size
            else:
                # If no modules remain, reset to a minimum size
                self.size_x = PADDING * 2
                self.size_y = PADDING * 2
                
            # Reset placement tracking variables for consistent future placements
            self._current_placement_x = PADDING
            self._current_placement_y = PADDING
            self._max_y_in_row = PADDING
            
    def update_size_for_module_position(self, module: Module):
        """Update the subspace size if needed when a module is moved."""
        if module in self.modules:
            # Calculate required size based on module position
            required_width = module.x + module.size_x + PADDING
            required_height = module.y + module.size_y + PADDING
            
            # Expand dimensions if needed
            if required_width > self.size_x or required_height > self.size_y:
                self.size_x = max(self.size_x, required_width)
                self.size_y = max(self.size_y, required_height)
                return True  # Size was changed
        
        return False  # No change needed

    def recalculate_size(self):
        """Recalculate the optimal size of the subspace based on the current module positions."""
        if not self.modules:
            # If no modules, reset to minimum size
            self.size_x = PADDING * 2
            self.size_y = PADDING * 2
            return
            
        # Find the maximum extents of all modules (with padding)
        max_x = PADDING
        max_y = PADDING
        
        for module in self.modules:
            # Calculate the right and bottom edges of the module
            right_edge = module.x + module.size_x
            bottom_edge = module.y + module.size_y
            
            # Update maximum coordinates
            max_x = max(max_x, right_edge + PADDING)
            max_y = max(max_y, bottom_edge + PADDING)
        
        # Update subspace dimensions
        self.size_x = max_x
        self.size_y = max_y

class BoundaryIOBox:
    """Represents an input/output box at the boundary of a subspace."""
    def __init__(self, is_input: bool, data_type: str, value: float = 0.0):
        self.is_input = is_input  # True for input, False for output
        self.data_type = data_type
        self.value = value
        self.connections = []  # List of connections to/from this box
        self.x = 0
        self.y = 0
        self.size = 10  # Default size

    def set_position(self, x: float, y: float):
        """Sets the position of the boundary IO box."""
        self.x = x
        self.y = y

    def set_size(self, size: float):
        """Sets the size of the boundary IO box."""
        self.size = size

    def add_connection(self, connection):
        """Adds a connection to this boundary IO box."""
        self.connections.append(connection)

    def remove_connection(self, connection):
        """Removes a connection from this boundary IO box."""
        if connection in self.connections:
            self.connections.remove(connection)
    
    def get_connections(self):
        """Returns the list of connections to/from this boundary IO box."""
        return self.connections

    def update_value(self, value: float):
        """Updates the value of this boundary IO box."""
        self.value = value

class InteriorSpace:
    """Represents an interior space with x and y dimensions and a list of subspaces."""
    def __init__(self, size_x: float, size_y: float):
        self.size_x = size_x
        self.size_y = size_y
        self.subspaces: list[Subspace] = []
        self.inputs: dict[str, float] = {}
        self.outputs: dict[str, float] = {}
        # Interior space specific attributes
        self.cooling_capacity = 0.0  # In kW
        self.power_capacity = 0.0  # In kW
        self.network_capacity = 0.0  # In Gbps

    def add_subspace(self, subspace: Subspace):
        """Adds a subspace to the interior space."""
        self.subspaces.append(subspace)

    def remove_subspace(self, subspace: Subspace):
        """Removes a subspace from the interior space."""
        if subspace in self.subspaces:
            self.subspaces.remove(subspace)
            
    def get_subspaces(self) -> list[Subspace]:
        """Returns the list of subspaces."""
        return self.subspaces
    
    def add_input(self, input: str, amount: float):
        """Adds an input to the interior space."""
        if input in self.inputs:
            self.inputs[input] += amount
        else:
            self.inputs[input] = amount
    
    def add_output(self, output: str, amount: float):
        """Adds an output to the interior space."""
        if output in self.outputs:
            self.outputs[output] += amount
        else:
            self.outputs[output] = amount
    
    def remove_input(self, input: str):
        """Removes an input from the interior space."""
        if input in self.inputs:
            del self.inputs[input]
    
    def get_size_x(self) -> float:
        """Returns the x dimension of the interior space."""
        return self.size_x
    
    def get_size_y(self) -> float:
        """Returns the y dimension of the interior space."""
        return self.size_y
    
    def resize(self, new_x: float, new_y: float):
        """Resizes the interior space to new dimensions."""
        self.size_x = new_x
        self.size_y = new_y
    
    def update_cooling_capacity(self, capacity: float):
        """Updates the cooling capacity of the interior space."""
        self.cooling_capacity = capacity
        
    def update_power_capacity(self, capacity: float):
        """Updates the power capacity of the interior space."""
        self.power_capacity = capacity
        
    def update_network_capacity(self, capacity: float):
        """Updates the network capacity of the interior space."""
        self.network_capacity = capacity
        
    def get_cooling_capacity(self) -> float:
        """Returns the cooling capacity of the interior space."""
        return self.cooling_capacity
        
    def get_power_capacity(self) -> float:
        """Returns the power capacity of the interior space."""
        return self.power_capacity
        
    def get_network_capacity(self) -> float:
        """Returns the network capacity of the interior space."""
        return self.network_capacity
    
    def __repr__(self):
        return f"InteriorSpace(size_x={self.size_x}, size_y={self.size_y}, subspaces={self.subspaces})"

