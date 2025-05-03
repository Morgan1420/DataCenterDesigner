from modules import Module

PADDING = 5  # Define padding between modules

class Subspace:
    """Represents a subspace with x and y dimensions."""
    def __init__(self, size_x: float, size_y: float):
        self.size_x = size_x
        self.size_y = size_y
        self.x = 0.0
        self.y = 0.0
        self.inputs: dict[str, float] = {}
        self.outputs: dict[str, float] = {}
        self.modules: list[Module] = []
        # Tracking for grid placement
        self._current_placement_x = PADDING
        self._current_placement_y = PADDING
        self._max_y_in_row = PADDING
        
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
    
    def remove_input(self, input: str):
        """Removes an input from the subspace."""
        if input in self.inputs:
            del self.inputs[input]
    
    def remove_output(self, output: str):
        """Removes an output from the subspace."""
        if output in self.outputs:
            del self.outputs[output]
            
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

        # Add module inputs and outputs to the subspace
        for unit, amount in module.inputs.items():
            self.inputs[unit] = self.inputs.get(unit, 0) + amount

        for unit, amount in module.outputs.items():
            self.outputs[unit] = self.outputs.get(unit, 0) + amount

    def get_modules(self) -> list[Module]:
        """Returns the list of modules."""
        return self.modules
    
    def remove_module(self, module: Module):
        """Removes a module from the subspace and resizes the subspace if needed."""
        if module in self.modules:
            # Remove the module from our list
            self.modules.remove(module)
            
            # Update inputs/outputs
            for unit, amount in module.inputs.items():
                if unit in self.inputs:
                    self.inputs[unit] -= amount
                    if self.inputs[unit] <= 0:
                        del self.inputs[unit]
            for unit, amount in module.outputs.items():
                if unit in self.outputs:
                    self.outputs[unit] -= amount
                    if self.outputs[unit] <= 0:
                        del self.outputs[unit]
            
            # Recalculate the bounding box based on the remaining modules
            if self.modules:
                # Find the maximum x and y coordinates needed by remaining modules
                max_x = PADDING  # Minimum padding
                max_y = PADDING  # Minimum padding
                
                for mod in self.modules:
                    # Calculate the right and bottom edges of each module
                    mod_right = mod.x + (mod.size_x if mod.size_x > 0 else 20)
                    mod_bottom = mod.y + (mod.size_y if mod.size_y > 0 else 20)
                    
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
            self._max_height_current_row = 0
            self._max_width_current_column = 0
            
class ExteriorSpace:
    """Represents an exterior space with x and y dimensions and a list of subspaces."""
    def __init__(self, size_x: float, size_y: float):
        self.size_x = size_x
        self.size_y = size_y
        self.subspaces: list[Subspace] = []
        self.inputs: dict[str, float] = {}
        self.outputs: dict[str, float] = {}

    def add_subspace(self, subspace: Subspace):
        """Adds a subspace to the exterior space."""
        self.subspaces.append(subspace)

    def remove_subspace(self, subspace: Subspace):
        """Removes a subspace from the exterior space."""
        if subspace in self.subspaces:
            self.subspaces.remove(subspace)
            
    def get_subspaces(self) -> list[Subspace]:
        """Returns the list of subspaces."""
        return self.subspaces
    
    def add_input(self, input: str, amount: float):
        """Adds an input to the exterior space."""
        if input in self.inputs:
            self.inputs[input] += amount
        else:
            self.inputs[input] = amount
    
    def add_output(self, output: str, amount: float):
        """Adds an output to the exterior space."""
        if output in self.outputs:
            self.outputs[output] += amount
        else:
            self.outputs[output] = amount
    
    def remove_input(self, input: str):
        """Removes an input from the exterior space."""
        if input in self.inputs:
            del self.inputs[input]
    
    def get_size_x(self) -> float:
        """Returns the x dimension of the exterior space."""
        return self.size_x
    
    def get_size_y(self) -> float:
        """Returns the y dimension of the exterior space."""
        return self.size_y
    
    def resize(self, new_x: float, new_y: float):
        """Resizes the exterior space to new dimensions."""
        self.size_x = new_x
        self.size_y = new_y
    
    def __repr__(self):
        return f"ExteriorSpace(size_x={self.size_x}, size_y={self.size_y}, subspaces={self.subspaces})"

class InteriorSpace:
    def __init__(self, size_x: float, size_y: float):
        self.size_x = size_x
        self.size_y = size_y
        self.subspaces: list[Subspace] = []
        self.inputs: dict[str, float] = {}
        self.outputs: dict[str, float] = {}
    def add_subspace(self, subspace: Subspace):
        self.subspaces.append(subspace)
    def remove_subspace(self, subspace: Subspace):
        if subspace in self.subspaces:
            self.subspaces.remove(subspace)
    def get_subspaces(self) -> list[Subspace]:
        return self.subspaces
    def add_input(self, input: str, amount: float):
        if input in self.inputs:
            self.inputs[input] += amount
        else:
            self.inputs[input] = amount
    def add_output(self, output: str, amount: float):
        if output in self.outputs:
            self.outputs[output] += amount
        else:
            self.outputs[output] = amount
    def remove_input(self, input: str):
        if input in self.inputs:
            del self.inputs[input]
    def get_size_x(self) -> float:
        return self.size_x
    def get_size_y(self) -> float:
        return self.size_y
    def resize(self, new_x: float, new_y: float):
        self.size_x = new_x
        self.size_y = new_y
    def __repr__(self):
        return f"InteriorSpace(size_x={self.size_x}, size_y={self.size_y}, subspaces={self.subspaces})"
