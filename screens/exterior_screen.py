from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox, QGraphicsView, QGraphicsScene, 
    QGraphicsRectItem, QGroupBox, QScrollArea, QSplitter, QListWidgetItem, QGraphicsItem, QGraphicsEllipseItem,
    QGraphicsPolygonItem, QMenu, QTreeView, QGraphicsLineItem, QLineEdit
)
from PySide6.QtCore import Qt, QSize, QRectF, QPointF
from PySide6.QtGui import QColor, QPen, QBrush, QCursor, QPainter, QPolygonF, QStandardItemModel
from screens.exterior_screen_modules import ExteriorSpace, Subspace
from modules import Module

# Constants
PADDING = 10  # Padding between modules (should match padding in exterior_screen_modules.py)

# Color mapping for different types of inputs/outputs
# Ensure consistent colors across the application
class DataTypeColors:
    @staticmethod
    def get_color_for_data_type(data_type: str) -> QColor:
        """Get a consistent color for a given data type."""
        # Color mapping for common data types
        color_map = {
            # Power-related
            "Usable_Power": QColor(255, 140, 0),  # Orange
            "Grid_Connection": QColor(255, 215, 0),  # Gold
            "Power": QColor(255, 140, 0),  # Orange
            
            # Water-related
            "Water": QColor(0, 191, 255),  # Deep Sky Blue
            "Cooling_Water": QColor(135, 206, 250),  # Light Sky Blue
            "Treated_Water": QColor(70, 130, 180),  # Steel Blue
            
            # Space-related
            "Space_X": QColor(169, 169, 169),  # Dark Gray
            "Space_Y": QColor(169, 169, 169),  # Dark Gray
            
            # Network-related
            "Network": QColor(50, 205, 50),  # Lime Green
            "Data": QColor(34, 139, 34),  # Forest Green
            
            # Price/economic
            "Price": QColor(138, 43, 226),  # Blue Violet
            "Cost": QColor(138, 43, 226),  # Blue Violet
            
            # Performance metrics
            "Performance": QColor(255, 20, 147),  # Deep Pink
            "Cooling": QColor(30, 144, 255),  # Dodger Blue
        }
        
        # If we have an exact match
        if data_type in color_map:
            return color_map[data_type]
        
        # If we have a partial match (e.g., "Cooling_Something" should match "Cooling")
        for key, color in color_map.items():
            if key in data_type or data_type in key:
                return color
        
        # Default color for unknown types - purple
        return QColor(128, 0, 128)  # Purple


class ModuleConnection:
    """Represents a connection between two module IO indicators."""
    def __init__(self, source_module, source_type, target_module, target_type):
        self.source_module = source_module  # Source module (None for boundary input)
        self.source_type = source_type      # Data type for source
        self.target_module = target_module  # Target module (None for boundary output)
        self.target_type = target_type      # Data type for target
        self.amount = 0                     # Amount of resource flowing through connection
        
    def set_amount(self, amount):
        """Set the amount of resource flowing through this connection."""
        self.amount = amount
        
    def is_boundary_connection(self):
        """Check if this is a connection to a boundary box."""
        return self.source_module is None or self.target_module is None


class ModuleConnectionLine(QGraphicsLineItem):
    """Visual representation of a connection between modules."""
    def __init__(self, connection, start_point, end_point):
        super().__init__(start_point.x(), start_point.y(), end_point.x(), end_point.y())
        self.connection = connection
        self.start_point = start_point
        self.end_point = end_point
        
        # Set line appearance to black
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        self.setPen(pen)
        
        # Store the connection amount
        self.amount = connection.amount
        
        # Set tooltip showing connection details
        self.setToolTip(f"Connection: {connection.source_type} = {connection.amount}")
        
        # Make the connection line selectable
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        
        # Set high z-value to ensure lines appear on top of other elements
        self.setZValue(10)
        
    def update_position(self, start_point=None, end_point=None):
        """Update the position of the connection line."""
        if start_point:
            self.start_point = start_point
        if end_point:
            self.end_point = end_point
            
        # Update the line
        self.setLine(self.start_point.x(), self.start_point.y(), 
                     self.end_point.x(), self.end_point.y())


class ModuleIOIndicator:
    """Base class for module input/output indicators."""
    @staticmethod
    def create_input_indicator(parent_item, input_type, value, x, y, size):
        """Create a circle indicator for an input with absolute coordinates.
        
        Args:
            parent_item: The parent module item
            input_type: The type of input
            value: The input value
            x: The absolute x position
            y: The absolute y position
            size: The size of the indicator
        """
        # Create a circle for the input - positioned at absolute coordinates
        circle = QGraphicsEllipseItem(
            x,  # Absolute x position
            y,  # Absolute y position 
            size * 1.5,  # Width
            size * 1.5,  # Height
            parent=parent_item  # This ensures the circle moves with the module
        )
        
        # Use consistent color based on input type
        color = DataTypeColors.get_color_for_data_type(input_type)
        circle.setBrush(color)
        circle.setPen(QPen(Qt.black, 0.5))
        
        # Add a tooltip with the input type but filter out price-related information
        if "Price" in input_type or "Cost" in input_type or "price" in input_type or "cost" in input_type:
            circle.setToolTip(f"Input: {input_type}")
        else:
            circle.setToolTip(f"Input: {input_type} = {value}")
        
        return circle
    
    @staticmethod
    def create_output_indicator(parent_item, output_type, value, x, y, size):
        """Create a triangle indicator for an output with absolute coordinates.
        
        Args:
            parent_item: The parent module item
            output_type: The type of output
            value: The output value
            x: The absolute x position
            y: The absolute y position
            size: The size of the indicator
        """
        # Create a triangle pointing right - positioned at absolute coordinates
        triangle_size = size * 1.5
        
        triangle = QPolygonF()
        
        # Position the triangle at absolute coordinates
        triangle.append(QPointF(x + triangle_size, y + triangle_size/2))  # Point (right)
        triangle.append(QPointF(x, y))  # Top left
        triangle.append(QPointF(x, y + triangle_size))  # Bottom left
        
        triangle_item = QGraphicsPolygonItem(triangle, parent=parent_item)
        
        # Use consistent color based on output type
        color = DataTypeColors.get_color_for_data_type(output_type)
        triangle_item.setBrush(color)
        triangle_item.setPen(QPen(Qt.black, 0.5))
        
        # Add a tooltip with the output type but filter out price-related information
        if "Price" in output_type or "Cost" in output_type or "price" in output_type or "cost" in output_type:
            triangle_item.setToolTip(f"Output: {output_type}")
        else:
            triangle_item.setToolTip(f"Output: {output_type} = {value}")
        
        return triangle_item


class DraggableModuleItem(QGraphicsRectItem):
    def __init__(self, x, y, width, height, module, subspace, parent_screen):
        super().__init__(x, y, width, height)
        self.module = module
        self.subspace = subspace
        self.parent_screen = parent_screen
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.ItemIsSelectable)  # Make the item selectable
        self.setBrush(QColor(255, 0, 0))
        self.setPen(QColor(0, 0, 0))
        self.setAcceptHoverEvents(True)
        self.setZValue(1)  # Ensure modules appear above the subspace background
        self.start_pos = QPointF(x, y)
        self.is_moving = False  # Flag to track if we're in move mode
        
        # Connection drawing variables
        self.temp_connection_line = None  # Temporary line shown while dragging
        self.connection_start_item = None  # The IO indicator that started the connection
        self.connection_start_type = None  # The data type of the IO indicator
        self.connection_is_output = False  # Whether the connection starts from an output
        
        # Immediately add IO indicators as children
        self.input_indicators = []
        self.output_indicators = []
        self._create_io_indicators()

    def _create_io_indicators(self):
        """Create visual indicators for inputs (circles) and outputs (triangles)."""
        # Size of indicators
        indicator_size = min(self.module.size_x, self.module.size_y) * 0.18
        indicator_size = max(indicator_size, 5)  # Minimum size
        indicator_size = min(indicator_size, 12)  # Maximum size
        
        # Filter out Space_X and Space_Y from inputs
        valid_inputs = [input_type for input_type in self.module.inputs_no_price.keys() 
                       if input_type not in ['Space_X', 'Space_Y']]
        input_count = len(valid_inputs)
        
        # Add input indicators (circles) on the left side
        if input_count > 0:
            # Calculate spacing to distribute indicators evenly along the height
            input_spacing = self.module.size_y / (input_count + 1)
            
            for i, input_type in enumerate(valid_inputs):
                value = self.module.inputs_no_price[input_type]
                
                # Calculate absolute position for the input indicator
                
                # Start with the module's global position
                module_x = self.x()
                module_y = self.y()
                
                # Calculate the specific position for this indicator
                x_pos = module_x + self.module.x + indicator_size * 1.1
                y_pos = module_y + self.module.y + (i + 1) * input_spacing - (indicator_size * 1.5) / 2
                
                # Create and add the indicator with global coordinates
                indicator = ModuleIOIndicator.create_input_indicator(
                    self, input_type, value, x_pos, y_pos, indicator_size
                )
                # Make the indicator interactive for connections
                indicator.setFlag(QGraphicsItem.ItemIsSelectable)
                indicator.setAcceptHoverEvents(True)
                indicator.data_type = input_type  # Store data type for connection validation
                indicator.value = value  # Store value for connection validation
                indicator.is_input = True  # Mark as input for connection logic
                indicator.parent_module = self.module  # Store parent module reference
                
                # Store a reference to the original mousePressEvent
                original_press_event = indicator.mousePressEvent
                original_release_event = indicator.mouseReleaseEvent
                original_move_event = indicator.mouseMoveEvent
                
                # Define custom event handlers as instance methods for this specific indicator
                def create_press_handler(ind):
                    def handler(event):
                        self.io_indicator_mouse_press(event, ind)
                    return handler
                
                def create_release_handler(ind):
                    def handler(event):
                        self.io_indicator_mouse_release(event, ind)
                    return handler
                
                def create_move_handler(ind):
                    def handler(event):
                        self.io_indicator_mouse_move(event, ind)
                    return handler
                
                # Set up event handlers specific to this indicator
                indicator.mousePressEvent = create_press_handler(indicator)
                indicator.mouseReleaseEvent = create_release_handler(indicator)
                indicator.mouseMoveEvent = create_move_handler(indicator)
                
                self.input_indicators.append(indicator)
                
                # Add the indicator to the subspace
                self.subspace.add_input(input_type, value)
                
        # Add output indicators (triangles) on the right side
        output_count = len(self.module.outputs)
        if output_count > 0:
            # Calculate spacing to distribute indicators evenly along the height
            output_spacing = self.module.size_y / (output_count + 1)
            
            for i, output_type in enumerate(self.module.outputs.keys()):
                value = self.module.outputs[output_type]
                
                # Calculate absolute position for the output indicator
                # Start with the module's global position
                module_x = self.x()
                module_y = self.y()
                
                # Calculate the specific position for this indicator
                x_pos = module_x + self.module.x + self.module.size_x - indicator_size*2
                y_pos = module_y + self.module.y + (i + 1) * output_spacing - (indicator_size * 1.5) / 2
                
                # Create and add the indicator with global coordinates
                indicator = ModuleIOIndicator.create_output_indicator(
                    self, output_type, value, x_pos, y_pos, indicator_size
                )
                # Make the indicator interactive for connections
                indicator.setFlag(QGraphicsItem.ItemIsSelectable)
                indicator.setAcceptHoverEvents(True)
                indicator.data_type = output_type  # Store data type for connection validation
                indicator.value = value  # Store value for connection validation
                indicator.is_input = False  # Mark as output for connection logic
                indicator.parent_module = self.module  # Store parent module reference
                
                # Define custom event handlers for this specific indicator
                def create_press_handler(ind):
                    def handler(event):
                        self.io_indicator_mouse_press(event, ind)
                    return handler
                
                def create_release_handler(ind):
                    def handler(event):
                        self.io_indicator_mouse_release(event, ind)
                    return handler
                
                def create_move_handler(ind):
                    def handler(event):
                        self.io_indicator_mouse_move(event, ind)
                    return handler
                
                # Set up event handlers specific to this indicator
                indicator.mousePressEvent = create_press_handler(indicator)
                indicator.mouseReleaseEvent = create_release_handler(indicator)
                indicator.mouseMoveEvent = create_move_handler(indicator)
                
                self.output_indicators.append(indicator)
                
                # Add the indicator to the subspace
                self.subspace.add_output(output_type, value)
            
                
    def io_indicator_mouse_press(self, event, item):
        """Handle mouse press on an IO indicator to start creating a connection."""
        if event.button() == Qt.LeftButton:
            # Start drawing a connection from this indicator
            if self.temp_connection_line is None:  # Only start if not already drawing
                # Store the starting item information
                self.connection_start_item = item
                self.connection_start_type = item.data_type
                self.connection_is_output = not item.is_input  # Output indicators start connections
                
                # Create a temporary line to visualize the connection during dragging
                start_point = item.sceneBoundingRect().center()
                self.temp_connection_line = QGraphicsLineItem(
                    start_point.x(), start_point.y(), 
                    start_point.x(), start_point.y()
                )
                
                # Set line appearance based on data type
                color = DataTypeColors.get_color_for_data_type(item.data_type)
                pen = QPen(color, 2, Qt.DashLine)
                self.temp_connection_line.setPen(pen)
                self.temp_connection_line.setZValue(0.5)  # Above background, below modules
                
                # Add the temporary line to the scene
                self.scene().addItem(self.temp_connection_line)
            
            event.accept()
        else:
            # Pass the event to the parent for other buttons
            super(DraggableModuleItem, self).mousePressEvent(event)
    
    def io_indicator_mouse_move(self, event, item):
        """Handle mouse move on an IO indicator to update the temporary connection line."""
        if self.temp_connection_line is not None:
            # Update the end point of the temporary line to follow the mouse
            start_point = self.connection_start_item.sceneBoundingRect().center()
            end_point = self.mapToScene(event.pos())
            
            self.temp_connection_line.setLine(
                start_point.x(), start_point.y(),
                end_point.x(), end_point.y()
            )
            
            event.accept()
        else:
            # Pass the event to the parent
            super(DraggableModuleItem, self).mouseMoveEvent(event)
    
    def io_indicator_mouse_release(self, event, item):
        """Handle mouse release on an IO indicator to complete the connection."""
        if event.button() == Qt.LeftButton and self.temp_connection_line is not None:
            # Check if the release happened over a valid target IO indicator
            release_pos = self.mapToScene(event.pos())
            target_item = self.find_io_indicator_at_position(release_pos)
            
            if target_item and self.is_valid_connection(self.connection_start_item, target_item):
                # Valid connection target found, create the permanent connection
                self.create_module_connection(self.connection_start_item, target_item)
            else:
                # Check if the release happened over a boundary IO box
                boundary_box = self.find_boundary_box_at_position(release_pos)
                if boundary_box and self.is_valid_boundary_connection(self.connection_start_item, boundary_box):
                    # Valid boundary box found, create the connection to the boundary
                    self.create_boundary_connection(self.connection_start_item, boundary_box)
                else:
                    # No valid target, remove the temporary line
                    self.scene().removeItem(self.temp_connection_line)
                    self.temp_connection_line = None
            
            # Clean up temporary drawing state
            self.scene().removeItem(self.temp_connection_line)
            self.temp_connection_line = None
            self.connection_start_item = None
            self.connection_start_type = None
            
            event.accept()
        else:
            # Pass the event to the parent for other buttons
            super(DraggableModuleItem, self).mouseReleaseEvent(event)
            
    def find_io_indicator_at_position(self, pos):
        """Find an IO indicator at the given position."""
        for item in self.scene().items(pos):
            # Check if the item is an IO indicator (circle or triangle)
            if hasattr(item, 'data_type') and hasattr(item, 'is_input'):
                # Don't connect to the starting item
                if item != self.connection_start_item:
                    return item
        return None
    
    def find_boundary_box_at_position(self, pos):
        """Find a boundary IO box at the given position."""
        for item in self.scene().items(pos):
            # Check if the item is a boundary IO box
            if isinstance(item, QGraphicsRectItem) and hasattr(item, 'is_boundary_box'):
                return item
        return None
    
    def is_valid_connection(self, source_item, target_item):
        
        
        """Check if the connection between the two IO indicators is valid."""
        
        # Rule 1: The connections must be between same types of data
        if source_item.data_type != target_item.data_type:
            return False
        
        # Rule 2: One must be an input and one must be an output
        if source_item.is_input == target_item.is_input:
            return False
        
        """
        # This code is not wrong, but for now we don't need it
        # Rule 3: A connection can be 1 to many as long as the output is less than the input
        # Determine which is the output and which is the input
        output_item = source_item if not source_item.is_input else target_item
        input_item = target_item if source_item == output_item else source_item
        
        # Get the current total outgoing value from the output
        output_module = output_item.parent_module
        output_type = output_item.data_type
        output_value = output_module.outputs.get(output_type, 0)
        
        # Get the current total incoming value to the input
        input_module = input_item.parent_module
        input_type = input_item.data_type
        input_value = input_module.inputs.get(input_type, 0)
        
        # Check existing connections to see how much is already used
        existing_output_usage = self.parent_screen.get_current_output_usage(output_module, output_type)
        existing_input_usage = self.parent_screen.get_current_input_usage(input_module, input_type)
        
        # Calculate remaining capacity
        remaining_output = output_value - existing_output_usage
        remaining_input = input_value - existing_input_usage
        
        # Output capacity must be positive and cannot exceed input capacity
        
        return remaining_output > 0 and remaining_output <= remaining_input
        """
        
        return True  # Allow all connections for now
    
    def is_valid_boundary_connection(self, module_item, boundary_box):
        """Check if the connection between an IO indicator and a boundary box is valid."""
        # Rule 1: The connections can be between different types of data now
        # No need to check if module_item.data_type == boundary_box.data_type
        
        # Rule 2: The IO indicator and boundary box must have opposite directions
        # (input connects to output, output connects to input)
        if module_item.is_input == boundary_box.is_input:
            return False
        
        # All other connections are now allowed
        return True
    
    def create_module_connection(self, source_item, target_item):
        """Create a permanent connection between two IO indicators."""
        # Determine the source and target modules and types
        if source_item.is_input:
            # Input to output connection (target is output)
            source_module = source_item.parent_module
            source_type = source_item.data_type
            target_module = target_item.parent_module
            target_type = target_item.data_type
        else:
            # Output to input connection (source is output)
            source_module = source_item.parent_module
            source_type = source_item.data_type
            target_module = target_item.parent_module
            target_type = target_item.data_type
        
        # Create a ModuleConnection object
        connection = ModuleConnection(source_module, source_type, target_module, target_type)
         
        # Calculate the amount to transfer (minimum of available output and input)
        output_item = source_item if not source_item.is_input else target_item
        output_module = output_item.parent_module
        output_type = output_item.data_type
        output_value = output_module.outputs.get(output_type, 0)
        
        input_item = target_item if source_item == output_item else source_item
        input_module = input_item.parent_module
        input_type = input_item.data_type
        input_value = input_module.inputs.get(input_type, 0)
        
        # Account for existing connections
        existing_output_usage = self.parent_screen.get_current_output_usage(output_module, output_type)
        existing_input_usage = self.parent_screen.get_current_input_usage(input_module, input_type)
        
        # Calculate remaining capacity
        remaining_output = output_value - existing_output_usage
        remaining_input = input_value - existing_input_usage
        
        # Set the amount for the connection (minimum of available capacities)
        connection_amount = min(remaining_output, remaining_input)
        connection.set_amount(connection_amount)
        
        # Create a visual representation of the connection
        start_point = source_item.sceneBoundingRect().center()
        end_point = target_item.sceneBoundingRect().center()
        connection_line = ModuleConnectionLine(connection, start_point, end_point)
        
        # Add the connection line to the scene
        self.scene().addItem(connection_line)
        
        # Add the connection to the parent screen's tracking
        self.parent_screen.add_module_connection(connection, connection_line)
        
        # Remove the data type from the subspace
        data_type = source_item.data_type
        value = min(source_item.value, target_item.value)
        self.subspace.remove_input(data_type, value)
        self.subspace.remove_output(data_type, value)   
        
        print(f"\n\nsubspace inputs: {self.subspace.get_inputs()}") 
        print(f"\nsubspace outputs: {self.subspace.get_outputs()}\n\n") 
    
    def create_boundary_connection(self, module_item, boundary_box):
        """Create a permanent connection between an IO indicator and a boundary box."""
        # Determine the module and boundary box details
        module = module_item.parent_module
        data_type = module_item.data_type
        
        # Create a BoundaryConnection object (special case of ModuleConnection)
        # For boundary connections, one of the modules will be None
        if module_item.is_input:
            # Module input connects to boundary output
            connection = ModuleConnection(module, data_type, None, data_type)
        else:
            # Module output connects to boundary input
            connection = ModuleConnection(None, data_type, module, data_type)
        
        # Set the amount based on the available capacity
        if module_item.is_input:
            connection_amount = module_item.value
        else:
            connection_amount = module_item.value
        
        # Adjust for existing connections
        if module_item.is_input:
            existing_usage = self.parent_screen.get_current_input_usage(module, data_type)
        else:
            existing_usage = self.parent_screen.get_current_output_usage(module, data_type)
        
        # Calculate the amount to transfer
        remaining = connection_amount - existing_usage
        connection.set_amount(remaining)
        
        # Create a visual representation of the connection
        start_point = module_item.sceneBoundingRect().center()
        end_point = boundary_box.sceneBoundingRect().center()
        connection_line = ModuleConnectionLine(connection, start_point, end_point)
        
        # Add the connection line to the scene
        self.scene().addItem(connection_line)
        
        # Add the connection to the parent screen's tracking
        self.parent_screen.add_boundary_connection(connection, connection_line, boundary_box)
        
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Update IO indicators whenever the module position changes
            # This is needed because we're using global coordinates
            
            # First handle grid snapping
            grid_size = PADDING
            new_pos = value
            new_pos.setX(round(new_pos.x() / grid_size) * grid_size)
            new_pos.setY(round(new_pos.y() / grid_size) * grid_size)
            
            return new_pos
        elif change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            # After the module has been moved, update the module's position in the data model
            self.module.x = self.x()
            self.module.y = self.y()
            
            # Clear all connections and reset IOs when a module is moved
            self.parent_screen._clear_all_connections()
            
            # Clear the subspace's inputs and outputs to set them up again
            self.subspace.remove_all_inputs()
            self.subspace.remove_all_outputs()
            
            # Add all inputs/outputs to the subspace
            for m in self.subspace.get_modules():
                for i in m.inputs:
                    self.subspace.add_input(i, m.inputs[i])
                for o in m.outputs:
                    self.subspace.add_output(o, m.outputs[o])
                    
            # Recalculate unconnected IO for the subspace
            self.subspace.calculate_unconnected_io(self.parent_screen.module_connections)
            self.parent_screen._redraw_subspace_io_indicators(self.subspace)
            
        return super().itemChange(change, value)

    def hoverEnterEvent(self, event):
        if self.is_moving:
            self.setCursor(QCursor(Qt.OpenHandCursor))
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))
        self.setOpacity(0.8)  # Slightly transparent when hovered
        # Set tooltip to display module ID when hovering
        self.setToolTip(f"Module ID: {self.module.id}")
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setCursor(QCursor(Qt.ArrowCursor))
        self.setOpacity(1.0)  # Full opacity when not hovered
        self.setBrush(QColor(255, 0, 0))  # Reset to original color
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_moving:
                # If we're in move mode, handle module positioning
                self.setCursor(QCursor(Qt.ClosedHandCursor))
                self.start_pos = self.pos()
                super().mousePressEvent(event)
            else:
                # If not in move mode, just select the item
                self.setSelected(True)
                event.accept()
        elif event.button() == Qt.RightButton:
            # Create context menu for right-click
            self.show_context_menu(event)
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_moving:
            self.setCursor(QCursor(Qt.OpenHandCursor))
            # End the move operation
            self.is_moving = False
        super().mouseReleaseEvent(event)
            
    def show_context_menu(self, event):
        menu = QMenu()
        
        # Add Move action
        move_action = menu.addAction("Move")
        move_action.triggered.connect(self.start_move)
        
        # Add Delete action
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self.delete_module)
        
        # Show the menu at the cursor position
        menu.exec_(event.screenPos().toPoint())
    
    def start_move(self):
        """Enter moving mode - will allow dragging the module until next click"""
        self.is_moving = True
        self.setCursor(QCursor(Qt.OpenHandCursor))
        # Set a visual indicator that we're in move mode (e.g., lighter color)
        self.setBrush(QColor(255, 128, 128))  # Lighter red to indicate move mode
    
    def delete_module(self):
        """Delete this module from the subspace"""
        self.parent_screen._remove_module_from_subspace(self.module, self.subspace)


class ZoomableGraphicsView(QGraphicsView):
    """A custom QGraphicsView that supports zoom functionality with mouse wheel."""
    def __init__(self, scene=None):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)  # Enable drag to pan
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)  # Zoom centers on mouse
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setMinimumHeight(200)
        
        # Set initial scale
        self.scale_factor = 1.0
        self.min_scale = 0.1
        self.max_scale = 10.0
        
    def wheelEvent(self, event):
        """Handle zoom in/out with mouse wheel."""
        # Calculate zoom factor - smaller value = more sensitive zoom
        zoom_factor = 1.1
        
        if event.angleDelta().y() > 0:
            # Zoom in
            self.scale(zoom_factor, zoom_factor)
            self.scale_factor *= zoom_factor
        else:
            # Zoom out
            self.scale(1.0 / zoom_factor, 1.0 / zoom_factor)
            self.scale_factor /= zoom_factor
        
        # Clamp scale factor to min/max
        if self.scale_factor < self.min_scale:
            # Reset to min scale
            self.resetTransform()
            self.scale(self.min_scale, self.min_scale)
            self.scale_factor = self.min_scale
        elif self.scale_factor > self.max_scale:
            # Reset to max scale
            self.resetTransform()
            self.scale(self.max_scale, self.max_scale)
            self.scale_factor = self.max_scale
        
        # Don't call parent implementation to avoid default behavior
        
    def resetZoom(self):
        """Reset zoom to original scale."""
        self.resetTransform()
        self.scale_factor = 1.0


class ExteriorScreen(QWidget):
    def __init__(self, exterior_space: ExteriorSpace, available_modules: list[Module]):
        super().__init__()
        if not isinstance(exterior_space, ExteriorSpace):
            raise TypeError(f"Expected ExteriorSpace object, but received {type(exterior_space)}")
        self.exterior_space: ExteriorSpace = exterior_space
        self.available_modules = available_modules
        self.subspace_scenes = {}  # Dictionary to store scenes: {(x, y): scene}
        self.subspace_module_lists = {}  # Dictionary to store module lists: {(x, y): list_widget}
        self.module_connections = []  # List of all module connections
        self.connection_lines = []    # List of all connection visual lines
        self.boundary_boxes = []      # List of boundary IO boxes
        
        # Track active connection drawing
        self.temp_connection_line = None
        self.connection_start_item = None
        self.connection_start_type = None
        self.connection_is_output = False

        # Main layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Splitter to divide the exterior space draw and the subspace editors
        self.splitter = QSplitter(Qt.Vertical)
        self.main_layout.addWidget(self.splitter)

        # Top widget: Graphics view for space representation
        self.top_widget = QWidget()
        self.top_layout = QVBoxLayout()
        self.top_widget.setLayout(self.top_layout)
        self.scene = QGraphicsScene()
        self.view = ZoomableGraphicsView(self.scene)
        self.top_layout.addWidget(self.view)
        self.splitter.addWidget(self.top_widget)

        # Draw the exterior space and subspaces
        self._draw_space()

        # Bottom widget: Subspace editors
        self.bottom_widget = QWidget()
        self.bottom_layout = QVBoxLayout()
        self.bottom_widget.setLayout(self.bottom_layout)
        self.splitter.addWidget(self.bottom_widget)

        # Button to create subspaces
        self.add_subspace_button = QPushButton("Add Subspace")
        self.bottom_layout.addWidget(self.add_subspace_button)
        self.add_subspace_button.clicked.connect(self._add_subspace)

        # Scroll area for subspace editors
        self.scroll_area = QScrollArea()
        self.scroll_area_widget = QWidget()
        self.scroll_area_layout = QVBoxLayout()
        self.scroll_area_widget.setLayout(self.scroll_area_layout)
        self.scroll_area.setWidget(self.scroll_area_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(500)  # Set minimum height for the scroll area
        self.bottom_layout.addWidget(self.scroll_area)

    def _draw_space(self):
        self.scene.clear()

        # Draw the exterior space
        space_rect = QGraphicsRectItem(0, 0, self.exterior_space.get_size_x(), self.exterior_space.get_size_y())
        space_rect.setBrush(QColor(200, 200, 200))
        self.scene.addItem(space_rect)

        # Draw each subspace and its modules
        for subspace in self.exterior_space.get_subspaces():
            # Draw the subspace boundary
            subspace_rect = QGraphicsRectItem(subspace.x, subspace.y, subspace.size_x, subspace.size_y)
            subspace_rect.setBrush(QColor(100, 150, 200))
            self.scene.addItem(subspace_rect)
            
            # Add boundary IO boxes
            #self._add_boundary_io_boxes(subspace)
            
            # Draw modules inside the subspace
            for module in subspace.get_modules():
                module_x = subspace.x + module.x  # Absolute position = subspace position + module relative position
                module_y = subspace.y + module.y
                
                # Use the actual module size for drawing
                # No need to check for zero size - if size is properly set from CSVs
                module_rect = QGraphicsRectItem(module_x, module_y, module.size_x, module.size_y)
                # Set RED color for modules (255, 0, 0)
                module_rect.setBrush(QColor(255, 0, 0))  
                # Add a black border to make it stand out
                module_rect.setPen(QColor(0, 0, 0))
                self.scene.addItem(module_rect)

    def _add_subspace(self):
        # Create a new subspace with default size
        new_subspace = Subspace(50, 50)

        # Calculate a position for the new subspace (simple horizontal placement)
        num_existing_subspaces = len(self.exterior_space.get_subspaces())
        new_x = num_existing_subspaces * (new_subspace.size_x + 10) # Place horizontally with a 10px gap
        new_y = 10 # Place near the top

        # Check if it fits within the exterior space boundaries
        if (new_x + new_subspace.size_x <= self.exterior_space.get_size_x() and
            new_y + new_subspace.size_y <= self.exterior_space.get_size_y()):

            # Set the calculated position
            new_subspace.set_position(new_x, new_y)

            # Add to data structure, redraw exterior, and add editor
            self.exterior_space.add_subspace(new_subspace)
            self._draw_space() # Redraw exterior to show the new subspace
            self._add_subspace_editor(new_subspace) # Add editor using the subspace with correct coords
        else:
            QMessageBox.warning(self, "Error", "Cannot add new subspace, not enough space in the exterior area.")

    def _add_subspace_editor(self, subspace: Subspace):
        # Create a group box for the subspace editor
        subspace_coords = (subspace.x, subspace.y)
        subspace_editor_group = QGroupBox(f"Subspace Editor ({subspace.x}, {subspace.y})")
        subspace_editor_layout = QHBoxLayout()
        subspace_editor_group.setLayout(subspace_editor_layout)

        # Column 1: Available modules
        available_modules_list = QListWidget()
        available_modules_list.setMinimumHeight(200)
        subspace_editor_layout.addWidget(available_modules_list)
        self._populate_available_modules(available_modules_list, subspace)

        # Column 2: Divided into two sections
        column2_widget = QWidget()
        column2_layout = QVBoxLayout()
        column2_widget.setLayout(column2_layout)
        
        # Section 1: Subspace properties
        properties_groupbox = QGroupBox("Subspace Properties")
        properties_layout = QVBoxLayout()
        properties_groupbox.setLayout(properties_layout)
        
        # Name input
        name_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        name_input = QLineEdit(subspace.name if hasattr(subspace, "name") else f"Subspace ({subspace.x}, {subspace.y})")
        name_input.textChanged.connect(lambda text: self._update_subspace_name(subspace, text, subspace_editor_group))
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_input)
        properties_layout.addLayout(name_layout)
        
        # Size X input
        size_x_layout = QHBoxLayout()
        size_x_label = QLabel("Size X:")
        size_x_input = QLineEdit(str(subspace.size_x))
        size_x_input.textChanged.connect(lambda text: self._update_subspace_size(subspace, "x", text))
        size_x_layout.addWidget(size_x_label)
        size_x_layout.addWidget(size_x_input)
        properties_layout.addLayout(size_x_layout)
        
        # Size Y input
        size_y_layout = QHBoxLayout()
        size_y_label = QLabel("Size Y:")
        size_y_input = QLineEdit(str(subspace.size_y))
        size_y_input.textChanged.connect(lambda text: self._update_subspace_size(subspace, "y", text))
        size_y_layout.addWidget(size_y_label)
        size_y_layout.addWidget(size_y_input)
        properties_layout.addLayout(size_y_layout)
        
        # Delete subspace button
        delete_subspace_btn = QPushButton("Delete Subspace")
        delete_subspace_btn.clicked.connect(lambda: self._delete_subspace(subspace, subspace_editor_group))
        properties_layout.addWidget(delete_subspace_btn)
        
        column2_layout.addWidget(properties_groupbox)
        
        # Section 2: Subspace modules list
        modules_groupbox = QGroupBox("Subspace Modules")
        modules_layout = QVBoxLayout()
        modules_groupbox.setLayout(modules_layout)
        
        subspace_modules_list = QListWidget()
        # Store reference to this list widget
        self.subspace_module_lists[subspace_coords] = subspace_modules_list
        subspace_modules_list.setMinimumHeight(100)
        modules_layout.addWidget(subspace_modules_list)
        
        column2_layout.addWidget(modules_groupbox)
        subspace_editor_layout.addWidget(column2_widget)

        # Column 3: Subspace graphical representation
        subspace_scene = QGraphicsScene()
        # Store reference to this scene
        self.subspace_scenes[subspace_coords] = subspace_scene
        
        # Use the new ZoomableGraphicsView instead of the standard view
        subspace_view = ZoomableGraphicsView(subspace_scene)
        subspace_view.setMinimumHeight(200)
        subspace_editor_layout.addWidget(subspace_view)
        
        # Add zoom control buttons
        zoom_controls = QWidget()
        zoom_layout = QHBoxLayout()
        zoom_controls.setLayout(zoom_layout)
        
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setMaximumWidth(30)
        zoom_in_btn.clicked.connect(lambda: subspace_view.scale(1.2, 1.2))
        
        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setMaximumWidth(30)
        zoom_out_btn.clicked.connect(lambda: subspace_view.scale(1/1.2, 1/1.2))
        
        reset_zoom_btn = QPushButton("Reset")
        reset_zoom_btn.clicked.connect(subspace_view.resetZoom)
        
        zoom_layout.addWidget(zoom_in_btn)
        zoom_layout.addWidget(zoom_out_btn)
        zoom_layout.addWidget(reset_zoom_btn)
        
        # Create a container for the view and controls
        view_container = QWidget()
        view_layout = QVBoxLayout()
        view_container.setLayout(view_layout)
        view_layout.addWidget(subspace_view)
        view_layout.addWidget(zoom_controls)
        
        subspace_editor_layout.addWidget(view_container)

        # Initial update using the direct references
        self._update_subspace_editor(subspace, subspace_modules_list, subspace_scene)

        # Add the group box to the scroll area layout
        self.scroll_area_layout.addWidget(subspace_editor_group)

    def _populate_available_modules(self, available_modules_list, subspace: Subspace):
        available_modules_list.clear()
        for module in self.available_modules:
            print(f"Module {module}")
            # Create a horizontal layout for each module item
            module_item_widget = QWidget()
            module_item_layout = QHBoxLayout()
            module_item_widget.setLayout(module_item_layout)

            # Add module name label
            module_label = QLabel(module.id)
            module_item_layout.addWidget(module_label)

            # Add button for each module
            add_button = QPushButton("Add")
            add_button.clicked.connect(lambda _, m=module: self._add_module_to_subspace(m, subspace))
            module_item_layout.addWidget(add_button)

            # Add the custom widget to the list
            item = QListWidgetItem()
            item.setSizeHint(module_item_widget.sizeHint())
            available_modules_list.addItem(item)
            available_modules_list.setItemWidget(item, module_item_widget)

    def _add_module_to_subspace(self, module: Module, subspace: Subspace):
        subspace_coords = (subspace.x, subspace.y)
        print(f"Attempting to add module {module.id} to subspace {subspace_coords}")

        # Create a copy of the module with a unique identifier
        # Count existing modules with the same base name to create a unique ID
        base_module_id = module.id
        existing_count = 0
        for existing_module in subspace.get_modules():
            if existing_module.id.startswith(base_module_id):
                existing_count += 1
        
        # Create a new module with a unique identifier
        unique_module = Module(
            id=f"{base_module_id}_{existing_count + 1}",
            inputs=module.inputs.copy(),
            outputs=module.outputs.copy(),
            size_x=module.size_x,
            size_y=module.size_y
        )
        
        # Add the unique module to the subspace
        subspace.add_module(unique_module)
        
        # Clear all connections when a new module is added
        self._clear_all_connections()
        
        # Clear the subspace's inputs and outputs to set them up again
        subspace.remove_all_inputs()
        subspace.remove_all_outputs()
        # Add all inputs/outputs to the subspace
        for m in subspace.get_modules():
            for i in m.inputs:
                subspace.add_input(i, m.inputs[i])
            for o in m.outputs:
                subspace.add_output(o, m.outputs[o])

        # Retrieve the stored list widget and scene directly
        subspace_modules_list = self.subspace_module_lists.get(subspace_coords)
        subspace_scene = self.subspace_scenes.get(subspace_coords)

        if subspace_modules_list and subspace_scene:
            print(f"Found stored list and scene for subspace {subspace_coords}. Updating editor.")
            self._update_subspace_editor(subspace, subspace_modules_list, subspace_scene)
            # Redraw the main exterior space as the subspace size might have changed
            self._draw_space()
        else:
            print(f"Error: Could not find stored components (list or scene) for subspace {subspace_coords}")
            if not subspace_modules_list:
                print("  Reason: Subspace module list not found in dictionary.")
            if not subspace_scene:
                print("  Reason: Subspace scene not found in dictionary.")

    def _update_subspace_editor(self, subspace: Subspace, subspace_modules_list=None, subspace_scene=None):
        subspace_coords = (subspace.x, subspace.y)
        print(f"Updating editor for subspace {subspace_coords}")
        # Update subspace modules list (Column 2)
        if subspace_modules_list:
            print(f"  Updating list widget for {subspace_coords}")
            subspace_modules_list.clear()
            modules_in_subspace = subspace.get_modules()
            print(f"  Modules found in subspace object: {[m.id for m in modules_in_subspace]}")
            for module in modules_in_subspace:
                print(f"    Adding module {module.id} to list widget")
                # Create a horizontal layout for each module item
                module_item_widget = QWidget()
                module_item_layout = QHBoxLayout()
                module_item_widget.setLayout(module_item_layout)

                # Add module name label
                module_label = QLabel(module.id)
                module_item_layout.addWidget(module_label)

                # Add delete button for each module
                delete_button = QPushButton("Delete")
                # Ensure lambda captures the correct module instance 'm'
                delete_button.clicked.connect(lambda checked=False, m=module, s=subspace: self._remove_module_from_subspace(m, s))
                module_item_layout.addWidget(delete_button)

                # Add the custom widget to the list
                item = QListWidgetItem()
                item.setSizeHint(module_item_widget.sizeHint())
                subspace_modules_list.addItem(item)
                subspace_modules_list.setItemWidget(item, module_item_widget)
            print(f"  List widget item count after update: {subspace_modules_list.count()}")
        else:
            print(f"  Subspace modules list widget not provided for {subspace_coords}.")

        # Update subspace graphical representation (Column 3)
        if subspace_scene:
            print(f"  Updating graphics scene for {subspace_coords}")
            subspace_scene.clear()
            # Draw the subspace background using its current potentially resized dimensions
            subspace_rect = QGraphicsRectItem(0, 0, subspace.size_x, subspace.size_y)
            subspace_rect.setBrush(QColor(150, 200, 250))
            subspace_scene.addItem(subspace_rect)

            # Removed the four white circle handles that were previously at the perimeter
            
            # Render modules using their actual coordinates within the subspace
            modules_in_subspace = subspace.get_modules() # Get modules again for drawing
            for module in modules_in_subspace:
                module_item = DraggableModuleItem(
                    module.x, module.y, 
                    module.size_x, module.size_y, 
                    module, subspace, self
                )
                subspace_scene.addItem(module_item)
                
            # Force a refresh of the graphical view
            view = subspace_scene.views()
            if view:
                 view[0].setSceneRect(subspace_scene.itemsBoundingRect()) # Adjust view to fit content
            subspace_scene.update()
            print(f"  Graphics scene updated for {subspace_coords}")
        else:
            print(f"  Subspace scene not provided for {subspace_coords}.")

    def _remove_module_from_subspace(self, module: Module, subspace: Subspace):
        subspace_coords = (subspace.x, subspace.y)
        print(f"Attempting to remove module {module.id} from subspace {subspace_coords}")

        # Remove module from the subspace data structure
        subspace.remove_module(module)
        # Remove inputs/outputs logic is handled by the subspace.remove_module method now
        
        # Clear all connections when a module is removed
        self._clear_all_connections()
        
        # Clear the subspace's inputs and outputs to set them up again
        subspace.remove_all_inputs()
        subspace.remove_all_outputs()
        # Add all inputs/outputs to the subspace
        for m in subspace.get_modules():
            for i in m.inputs:
                subspace.add_input(i, m.inputs[i])
            for o in m.outputs:
                subspace.add_output(o, m.outputs[o])
        
        # Retrieve the stored list widget and scene directly
        subspace_modules_list = self.subspace_module_lists.get(subspace_coords)
        subspace_scene = self.subspace_scenes.get(subspace_coords)

        if subspace_modules_list and subspace_scene:
            print(f"Found stored list and scene for subspace {subspace_coords}. Updating editor after removal.")
            self._update_subspace_editor(subspace, subspace_modules_list, subspace_scene)
            # Redraw the main exterior space to show the updated subspace with module removed
            self._draw_space()
        else:
            print(f"Error: Could not find stored components for subspace {subspace_coords} during removal.")

    def add_module_connection(self, connection, connection_line):
        """Add a new module connection to the tracking system."""
        self.module_connections.append(connection)
        self.connection_lines.append(connection_line)
        
    def add_boundary_connection(self, connection, connection_line, boundary_box):
        """Add a connection between a module and a boundary box.
        
        This will update the subspace inputs/outputs based on the connection.
        
        Args:
            connection: The ModuleConnection object
            connection_line: The visual line representing the connection
            boundary_box: The boundary box being connected to
        """
        # Store the connection and visual line
        self.module_connections.append(connection)
        self.connection_lines.append(connection_line)
        
        # Get the module and data type from the connection
        data_type = connection.source_type  # Same for source and target
        
        # Get the subspace from the boundary box
        subspace = boundary_box.subspace
        
        # Determine if this is connecting to an input or output boundary
        is_input = boundary_box.is_input
        
        # Get the amount from the connection
        amount = connection.amount
        
        # Update the subspace's inputs/outputs based on the connection
        subspace.update_boundary_connection(data_type, is_input, amount, add=True)
        
        # Update boundary box tooltip to show the new connection
        if is_input:
            boundary_box.setToolTip(f"Input Boundary: {data_type} = {amount}")
        else:
            boundary_box.setToolTip(f"Output Boundary: {data_type} = {amount}")
            
    def remove_boundary_connection(self, connection_line):
        """Remove a connection between a module and a boundary box.
        
        This will update the subspace inputs/outputs accordingly.
        
        Args:
            connection_line: The visual line representing the connection to remove
        """
        # Find the connection object from the visual line
        connection = connection_line.connection
        
        # Get the boundary box this connection connects to
        boundary_box = None
        for box in self.boundary_boxes:
            if box.sceneBoundingRect().contains(connection_line.end_point) or \
               box.sceneBoundingRect().contains(connection_line.start_point):
                boundary_box = box
                break
                
        if boundary_box is None:
            print("Warning: Could not find boundary box for connection")
            return
            
        # Get the module and data type from the connection
        data_type = connection.source_type  # Same for source and target
        
        # Get the subspace from the boundary box
        subspace = boundary_box.subspace
        
        # Determine if this is connecting to an input or output boundary
        is_input = boundary_box.is_input
        
        # Get the amount from the connection
        amount = connection.amount
        
        # Update the subspace's inputs/outputs
        subspace.update_boundary_connection(data_type, is_input, amount, add=False)
        
        # Remove the connection from our tracking
        if connection in self.module_connections:
            self.module_connections.remove(connection)
        if connection_line in self.connection_lines:
            self.connection_lines.remove(connection_line)
            
        # Remove the visual line from the scene
        self.scene.removeItem(connection_line)
            
    def get_current_output_usage(self, module, output_type):
        """Get the total amount of an output type currently being used in connections.
        
        Args:
            module: The Module object
            output_type: The type of output to check
            
        Returns:
            The total amount of the output currently used in connections
        """
        total_usage = 0.0
        
        # Check all connections
        for connection in self.module_connections:
            if connection.source_module == module and connection.source_type == output_type:
                total_usage += connection.amount
            elif connection.target_module == module and connection.target_type == output_type:
                total_usage += connection.amount
                
        return total_usage
        
    def get_current_input_usage(self, module, input_type):
        """Get the total amount of an input type currently being used in connections.
        
        Args:
            module: The Module object
            input_type: The type of input to check
            
        Returns:
            The total amount of the input currently used in connections
        """
        total_usage = 0.0
        
        # Check all connections
        for connection in self.module_connections:
            if connection.source_module == module and connection.source_type == input_type:
                total_usage += connection.amount
            elif connection.target_module == module and connection.target_type == input_type:
                total_usage += connection.amount
                
        return total_usage

    def remove_connection(self, connection_line):
        """Remove a connection from the system."""
        if connection_line in self.connection_lines:
            # Find the associated connection
            index = self.connection_lines.index(connection_line)
            connection = self.module_connections[index]
            
            # Remove from tracking lists
            self.module_connections.pop(index)
            self.connection_lines.pop(index)
            
            # Remove the visual line from the scene
            connection_line.scene().removeItem(connection_line)
            
            return True
        return False

    def _clear_all_connections(self):
        """Clear all connections and their visual representations."""
        for connection_line in self.connection_lines:
            connection_line.scene().removeItem(connection_line)
        self.module_connections.clear()
        self.connection_lines.clear()

    def _delete_connection(self, connection, connection_line):
        """Delete an existing connection between modules or to a boundary box."""
        # First check if it's a boundary connection
        is_boundary_connection = connection.is_boundary_connection()
        
        if is_boundary_connection:
            # Find the boundary box involved in this connection
            boundary_box = None
            for box in self.boundary_boxes:
                # Check both endpoints of the connection line to find which matches the boundary box
                box_center = box.sceneBoundingRect().center()
                line_p1 = connection_line.line().p1()
                line_p2 = connection_line.line().p2()
                
                # Simple distance check to see if either end of the line is at the boundary box
                distance1 = ((box_center.x() - line_p1.x())**2 + (box_center.y() - line_p1.y())**2)**0.5
                distance2 = ((box_center.x() - line_p2.x())**2 + (box_center.y() - line_p2.y())**2)**0.5
                
                if distance1 < 20 or distance2 < 20:  # 20 is a reasonable threshold for "closeness"
                    boundary_box = box
                    break
            
            if boundary_box and hasattr(boundary_box, 'subspace'):
                # Update the subspace inputs/outputs when removing a boundary connection
                data_type = connection.source_type if connection.source_module else connection.target_type
                is_input = boundary_box.is_input
                amount = connection.amount
                
                # Remove this connection from the subspace's inputs/outputs
                boundary_box.subspace.update_boundary_connection(data_type, is_input, amount, add=False)
                
                # Remove from the subspace's boundary connections list if it exists
                if hasattr(boundary_box.subspace, 'boundary_connections'):
                    for i, (conn, box) in enumerate(boundary_box.subspace.boundary_connections):
                        if conn == connection:
                            boundary_box.subspace.boundary_connections.pop(i)
                            break
        
        # Remove the connection line from the scene
        self.scene.removeItem(connection_line)
        
        # Remove connection from tracking lists
        if connection in self.module_connections:
            index = self.module_connections.index(connection)
            self.module_connections.pop(index)
            self.connection_lines.pop(index)

    def _update_subspace_name(self, subspace, name, group_box):
        """Update the name of a subspace when the user changes the input field."""
        if not name:
            # If the name is empty, use a default
            name = f"Subspace ({subspace.x}, {subspace.y})"
        
        # Set the name attribute on the subspace
        subspace.name = name
        
        # Update the group box title to reflect the new name
        group_box.setTitle(f"Subspace Editor: {name}")
        
        # Also update the main view to show the updated name
        self._draw_space()

    def _update_subspace_size(self, subspace, dimension, value):
        """Update the size of a subspace when the user changes the input field."""
        try:
            # Convert the input to an integer
            new_value = int(value)
            if new_value <= 0:
                # Prevent negative or zero sizes
                return
                
            # Update the appropriate dimension
            if dimension == "x":
                subspace.resize(new_value, subspace.size_y)
            elif dimension == "y":
                subspace.resize(subspace.size_x, new_value)
                
            # If the subspace is in the scenes dictionary, update its visual representation
            subspace_coords = (subspace.x, subspace.y)
            if subspace_coords in self.subspace_scenes:
                subspace_scene = self.subspace_scenes[subspace_coords]
                self._update_subspace_editor(subspace, self.subspace_module_lists[subspace_coords], subspace_scene)
            
            # Update the main space view as well
            self._draw_space()
                
        except ValueError:
            # If the input is not a valid integer, do nothing
            pass

    def _delete_subspace(self, subspace, subspace_editor_group):
        """Delete a subspace from the exterior space."""
        # Confirm deletion with user
        confirm = QMessageBox.question(
            self, 
            "Confirm Deletion",
            f"Are you sure you want to delete {subspace.name if hasattr(subspace, 'name') else f'Subspace ({subspace.x}, {subspace.y})'}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Remove the subspace from the exterior space
            self.exterior_space.remove_subspace(subspace)
            
            # Remove the subspace editor from the UI
            subspace_editor_group.setParent(None)
            subspace_editor_group.deleteLater()
            
            # Remove the subspace from our tracking dictionaries
            subspace_coords = (subspace.x, subspace.y)
            if subspace_coords in self.subspace_scenes:
                del self.subspace_scenes[subspace_coords]
            if subspace_coords in self.subspace_module_lists:
                del self.subspace_module_lists[subspace_coords]
            
            # Update the main space view
            self._draw_space()
