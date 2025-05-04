from modules import Module
from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsView, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem, QInputDialog, QMessageBox
from PySide6.QtCore import Qt, QPointF, QEvent
from PySide6.QtGui import QPen, QColor, QPainter
from PySide6.QtWidgets import QFrame

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


class ZoomableGraphicsView(QGraphicsView):
    """A custom QGraphicsView that supports zooming and panning."""
    
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setBackgroundBrush(QColor(248, 248, 248))
        self.setFrameShape(QFrame.NoFrame)
        
        # Initialize the base scale
        self._base_scale = 1.0
        
    def wheelEvent(self, event):
        """Override the wheel event for custom zoom functionality."""
        # Calculate zoom factor
        zoom_factor = 1.2
        
        # Determine direction
        if event.angleDelta().y() > 0:
            # Zoom in
            self.scale(zoom_factor, zoom_factor)
        else:
            # Zoom out
            self.scale(1.0 / zoom_factor, 1.0 / zoom_factor)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MiddleButton:
            # Enable panning with middle mouse button
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            # Create a fake left mouse button event to initiate drag
            fake_event = QMouseEvent(
                QEvent.MouseButtonPress,
                event.pos(),
                Qt.LeftButton,
                Qt.LeftButton,
                Qt.NoModifier
            )
            super().mousePressEvent(fake_event)
        else:
            super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.MiddleButton:
            # Create a fake left mouse button event to finish drag
            fake_event = QMouseEvent(
                QEvent.MouseButtonRelease,
                event.pos(),
                Qt.LeftButton,
                Qt.LeftButton,
                Qt.NoModifier
            )
            super().mouseReleaseEvent(fake_event)
            # Reset drag mode
            self.setDragMode(QGraphicsView.NoDrag)
        else:
            super().mouseReleaseEvent(event)
    
    def resetZoom(self):
        """Reset view to original scale and position."""
        self.resetTransform()
        self.centerOn(0, 0)


class DraggableModuleItem(QGraphicsRectItem):
    """A draggable module item for the graphics scene."""
    
    def __init__(self, x, y, width, height, module, subspace, parent_screen):
        super().__init__(x, y, width, height)
        self.module = module
        self.subspace = subspace
        self.parent_screen = parent_screen
        
        # Set flags for interaction
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        
        # Visual properties
        self.normal_color = QColor(150, 200, 230)
        self.selected_color = QColor(220, 230, 150)
        self.setBrush(self.normal_color)
        self.setPen(QPen(Qt.black, 1))
        
        # Add a label
        self.label = QGraphicsTextItem(module.id, self)
        self.label.setPos(5, 5)
        
        # Add connection points
        self._create_connection_points()
    
    def _create_connection_points(self):
        """Create visual connection points for inputs and outputs."""
        self.input_points = []
        self.output_points = []
        
        # Add inputs on left side
        y_pos = 20
        for input_type, capacity in self.module.inputs.items():
            input_point = ConnectionPoint(
                self, -5, y_pos, input_type, capacity, False, self.parent_screen
            )
            self.input_points.append(input_point)
            y_pos += 20
        
        # Add outputs on right side
        y_pos = 20
        for output_type, capacity in self.module.outputs.items():
            output_point = ConnectionPoint(
                self, self.module.size_x + 5, y_pos, output_type, capacity, True, self.parent_screen
            )
            self.output_points.append(output_point)
            y_pos += 20
    
    def paint(self, painter, option, widget=None):
        """Override paint to add custom appearance."""
        # Use different color when selected
        if self.isSelected():
            self.setBrush(self.selected_color)
        else:
            self.setBrush(self.normal_color)
        
        # Draw the basic rectangle
        super().paint(painter, option, widget)
        
        # Add additional visuals
        painter.setPen(QPen(Qt.black, 1))
        
        # Draw header area
        header_rect = QRectF(self.rect().x(), self.rect().y(), self.rect().width(), 20)
        painter.fillRect(header_rect, QColor(100, 150, 180))
        
        # Draw labels for inputs and outputs
        painter.setPen(QPen(Qt.darkGray, 1))
        for i, point in enumerate(self.input_points):
            painter.drawText(QPointF(5, 25 + i * 20), f"{point.connection_type}")
        
        for i, point in enumerate(self.output_points):
            painter.drawText(
                QPointF(self.rect().width() - 40, 25 + i * 20),
                f"{point.connection_type}"
            )
    
    def itemChange(self, change, value):
        """Handle changes to the item's state."""
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Update the module position when dragged
            new_pos = value
            
            # Keep the module within the subspace boundaries
            x = max(0, min(new_pos.x(), self.subspace.size_x - self.module.size_x))
            y = max(0, min(new_pos.y(), self.subspace.size_y - self.module.size_y))
            
            # Update the module's stored position
            self.module.x = x
            self.module.y = y
            
            return QPointF(x, y)
        
        elif change == QGraphicsItem.ItemSelectedChange:
            # Handle selection changes
            pass
        
        return super().itemChange(change, value)
    
    def hoverEnterEvent(self, event):
        """Handle mouse hover enter events."""
        self.setCursor(Qt.SizeAllCursor)
        self.setOpacity(0.8)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle mouse hover leave events."""
        self.setCursor(Qt.ArrowCursor)
        self.setOpacity(1.0)
        super().hoverLeaveEvent(event)


class ConnectionPoint(QGraphicsEllipseItem):
    """A connection point for module inputs/outputs."""
    
    def __init__(self, parent_item, x, y, connection_type, capacity, is_output, parent_screen):
        # Draw a small circle for the connection point
        radius = 5
        super().__init__(x - radius, y - radius, radius * 2, radius * 2, parent_item)
        
        self.parent_item = parent_item
        self.connection_type = connection_type
        self.capacity = capacity
        self.is_output = is_output
        self.parent_screen = parent_screen
        
        # Visual properties
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        # Color based on connection type
        color_map = {
            "power": QColor(255, 100, 100),
            "data": QColor(100, 100, 255),
            "water": QColor(100, 255, 100),
            "cooling": QColor(150, 200, 255)
        }
        
        base_color = color_map.get(connection_type.lower().split('_')[0], QColor(200, 200, 200))
        self.setBrush(base_color)
        self.setPen(QPen(Qt.black, 1))
        
        # Add a tooltip
        used = 0  # Calculate actual usage from connections
        self.setToolTip(f"{'Output' if is_output else 'Input'}: {connection_type}\n"
                        f"Capacity: {capacity}\n"
                        f"Used: {used}/{capacity}")
    
    def hoverEnterEvent(self, event):
        """Handle mouse hover enter events."""
        self.setCursor(Qt.PointingHandCursor)
        self.setBrush(self.brush().color().lighter())
        
        # Update tooltip with current usage
        if self.is_output:
            used = self.parent_screen.get_current_output_usage(
                self.parent_item.module, self.connection_type
            )
        else:
            used = self.parent_screen.get_current_input_usage(
                self.parent_item.module, self.connection_type
            )
        
        self.setToolTip(f"{'Output' if self.is_output else 'Input'}: {self.connection_type}\n"
                        f"Capacity: {self.capacity}\n"
                        f"Used: {used}/{self.capacity}")
        
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle mouse hover leave events."""
        self.setCursor(Qt.ArrowCursor)
        self.setBrush(self.brush().color().darker())
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press events to start connection."""
        if event.button() == Qt.LeftButton:
            # Start connection drawing
            self.parent_screen.connection_start_item = self.parent_item.module
            self.parent_screen.connection_start_type = self.connection_type
            self.parent_screen.connection_is_output = self.is_output
            
            # Create temporary line for visual feedback
            if self.scene():
                start_point = self.scenePos() + QPointF(5, 5)  # Center of the connection point
                self.parent_screen.temp_connection_line = QGraphicsLineItem(
                    start_point.x(), start_point.y(), start_point.x(), start_point.y()
                )
                self.parent_screen.temp_connection_line.setPen(QPen(Qt.red, 2, Qt.DashLine))
                self.scene().addItem(self.parent_screen.temp_connection_line)
        
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events to complete connection."""
        if event.button() == Qt.LeftButton and self.parent_screen.connection_start_item:
            # Check if we can make a valid connection
            if (self.parent_screen.connection_is_output != self.is_output and
                self.parent_screen.connection_start_type == self.connection_type):
                
                # Determine source and target
                if self.parent_screen.connection_is_output:
                    source_module = self.parent_screen.connection_start_item
                    source_type = self.parent_screen.connection_start_type
                    target_module = self.parent_item.module
                    target_type = self.connection_type
                else:
                    source_module = self.parent_item.module
                    source_type = self.connection_type
                    target_module = self.parent_screen.connection_start_item
                    target_type = self.parent_screen.connection_start_type
                
                # Check current usage
                source_used = self.parent_screen.get_current_output_usage(source_module, source_type)
                target_used = self.parent_screen.get_current_input_usage(target_module, target_type)
                
                source_capacity = source_module.outputs[source_type]
                target_capacity = target_module.inputs[target_type]
                
                available_capacity = min(
                    source_capacity - source_used,
                    target_capacity - target_used
                )
                
                if available_capacity > 0:
                    # Ask user for the amount to connect
                    amount, ok = QInputDialog.getInt(
                        None, "Connection Amount",
                        f"Enter amount to connect (max {available_capacity}):",
                        1, 1, available_capacity
                    )
                    
                    if ok:
                        # Create the connection
                        connection = ModuleConnection(
                            source_module, source_type,
                            target_module, target_type,
                            amount
                        )
                        
                        # Create a permanent line for the connection
                        self.parent_screen.add_module_connection(
                            connection, self.parent_screen.temp_connection_line
                        )
                        
                        # Update the connection line appearance
                        self.parent_screen.temp_connection_line.setPen(QPen(Qt.black, 2))
                        
                        # Set temporary line to None since it's now a permanent connection
                        self.parent_screen.temp_connection_line = None
                else:
                    # No capacity available
                    QMessageBox.warning(
                        None, "Connection Error",
                        "Cannot create connection due to insufficient capacity."
                    )
            else:
                # Invalid connection (same type or wrong direction)
                scene = self.scene()
                if scene and self.parent_screen.temp_connection_line:
                    scene.removeItem(self.parent_screen.temp_connection_line)
                    self.parent_screen.temp_connection_line = None
            
            # Reset connection tracking
            self.parent_screen.connection_start_item = None
            self.parent_screen.connection_start_type = None
            self.parent_screen.connection_is_output = False
        
        super().mouseReleaseEvent(event)


class ModuleConnection:
    """Represents a connection between two modules."""
    
    def __init__(self, source_module, source_type, target_module, target_type, amount):
        self.source_module = source_module
        self.source_type = source_type
        self.target_module = target_module
        self.target_type = target_type
        self.amount = amount

