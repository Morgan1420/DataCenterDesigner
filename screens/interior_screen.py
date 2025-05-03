from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox, QGraphicsView, QGraphicsScene, 
    QGraphicsRectItem, QGroupBox, QScrollArea, QSplitter, QListWidgetItem, QGraphicsItem, QGraphicsEllipseItem,
    QGraphicsPolygonItem, QMenu, QTreeView, QGraphicsLineItem, QLineEdit
)
from PySide6.QtCore import Qt, QSize, QRectF, QPointF
from PySide6.QtGui import QColor, QPen, QBrush, QCursor, QPainter, QPolygonF, QStandardItemModel
from modules import Module
from screens.interior_screen_modules import InteriorSpace, Subspace, BoundaryIOBox

# Constants
PADDING = 10  # Padding between modules

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
            "Chilled_Water": QColor(135, 206, 250),  # Light Sky Blue
            "Fresh_Water": QColor(70, 130, 180),  # Steel Blue
            "Distilled_Water": QColor(70, 130, 180),  # Steel Blue
            
            # Space-related
            "Space_X": QColor(169, 169, 169),  # Dark Gray
            "Space_Y": QColor(169, 169, 169),  # Dark Gray
            
            # Network-related
            "Internal_Network": QColor(50, 205, 50),  # Lime Green
            "External_Network": QColor(0, 100, 0),  # Dark Green
            
            # Data-related
            "Data_Storage": QColor(255, 20, 147),  # Deep Pink
            "Processing": QColor(255, 182, 193), # Light Pink

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
        
    def resetZoom(self):
        """Reset zoom to original scale."""
        self.resetTransform()
        self.scale_factor = 1.0


class DraggableModuleItem(QGraphicsRectItem):
    """Represents a draggable module in the graphics scene."""
    def __init__(self, x, y, width, height, module, parent_screen):
        super().__init__(x, y, width, height)
        self.module = module
        self.parent_screen = parent_screen
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setBrush(QColor(0, 128, 255))  # Different color from exterior modules
        self.setPen(QColor(0, 0, 0))
        self.setAcceptHoverEvents(True)
        self.setZValue(1)
        self.start_pos = QPointF(x, y)
        self.is_moving = False
        
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Handle grid snapping
            grid_size = PADDING
            new_pos = value
            new_pos.setX(round(new_pos.x() / grid_size) * grid_size)
            new_pos.setY(round(new_pos.y() / grid_size) * grid_size)
            
            return new_pos
        elif change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            # Update the module's position in the data model
            self.module.x = self.x()
            self.module.y = self.y()
            
        return super().itemChange(change, value)

    def hoverEnterEvent(self, event):
        if self.is_moving:
            self.setCursor(QCursor(Qt.OpenHandCursor))
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))
        self.setOpacity(0.8)  # Slightly transparent when hovered
        self.setToolTip(f"Module ID: {self.module.id}")
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setCursor(QCursor(Qt.ArrowCursor))
        self.setOpacity(1.0)  # Full opacity when not hovered
        self.setBrush(QColor(0, 128, 255))  # Reset to original color
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_moving:
                self.setCursor(QCursor(Qt.ClosedHandCursor))
                self.start_pos = self.pos()
                super().mousePressEvent(event)
            else:
                self.setSelected(True)
                event.accept()
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event)
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_moving:
            self.setCursor(QCursor(Qt.OpenHandCursor))
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
        self.setBrush(QColor(100, 175, 255))  # Lighter blue to indicate move mode
    
    def delete_module(self):
        """Delete this module from the interior space"""
        self.parent_screen._remove_module(self.module)


class InteriorScreen(QWidget):
    def __init__(self, available_modules: list[Module]):
        super().__init__()
        self.available_modules = available_modules
        self.modules = []  # List of modules placed in the interior space
        self.module_items = []  # List of draggable module items
        
        # Main layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Splitter to divide the space
        self.splitter = QSplitter(Qt.Vertical)
        self.main_layout.addWidget(self.splitter)

        # Top widget: Graphics view for interior space representation
        self.top_widget = QWidget()
        self.top_layout = QVBoxLayout()
        self.top_widget.setLayout(self.top_layout)
        self.scene = QGraphicsScene()
        self.view = ZoomableGraphicsView(self.scene)
        self.top_layout.addWidget(self.view)
        self.splitter.addWidget(self.top_widget)

        # Draw the initial interior space
        self._draw_space()

        # Bottom widget: Module selection and controls
        self.bottom_widget = QWidget()
        self.bottom_layout = QVBoxLayout()
        self.bottom_widget.setLayout(self.bottom_layout)
        self.splitter.addWidget(self.bottom_widget)

        # Available modules section
        self.modules_groupbox = QGroupBox("Available Modules")
        self.modules_layout = QVBoxLayout()
        self.modules_groupbox.setLayout(self.modules_layout)
        
        self.available_modules_list = QListWidget()
        self.available_modules_list.setMinimumHeight(200)
        self.modules_layout.addWidget(self.available_modules_list)
        self._populate_available_modules()
        
        self.bottom_layout.addWidget(self.modules_groupbox)

        # Controls section
        self.controls_groupbox = QGroupBox("Controls")
        self.controls_layout = QHBoxLayout()
        self.controls_groupbox.setLayout(self.controls_layout)
        
        # Zoom controls
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setMaximumWidth(30)
        self.zoom_in_btn.clicked.connect(lambda: self.view.scale(1.2, 1.2))
        
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setMaximumWidth(30)
        self.zoom_out_btn.clicked.connect(lambda: self.view.scale(1/1.2, 1/1.2))
        
        self.reset_zoom_btn = QPushButton("Reset Zoom")
        self.reset_zoom_btn.clicked.connect(self.view.resetZoom)
        
        self.controls_layout.addWidget(self.zoom_in_btn)
        self.controls_layout.addWidget(self.zoom_out_btn)
        self.controls_layout.addWidget(self.reset_zoom_btn)
        
        self.bottom_layout.addWidget(self.controls_groupbox)

    def _draw_space(self):
        self.scene.clear()

        # Draw the interior space background
        space_width = 800
        space_height = 600
        space_rect = QGraphicsRectItem(0, 0, space_width, space_height)
        space_rect.setBrush(QColor(220, 220, 220))
        self.scene.addItem(space_rect)

        # Redraw any existing modules
        for module in self.modules:
            self._draw_module(module)

    def _populate_available_modules(self):
        self.available_modules_list.clear()
        for module in self.available_modules:
            # Create a horizontal layout for each module item
            module_item_widget = QWidget()
            module_item_layout = QHBoxLayout()
            module_item_widget.setLayout(module_item_layout)

            # Add module name label
            module_label = QLabel(module.id)
            module_item_layout.addWidget(module_label)

            # Add button for each module
            add_button = QPushButton("Add")
            add_button.clicked.connect(lambda _, m=module: self._add_module(m))
            module_item_layout.addWidget(add_button)

            # Add the custom widget to the list
            item = QListWidgetItem()
            item.setSizeHint(module_item_widget.sizeHint())
            self.available_modules_list.addItem(item)
            self.available_modules_list.setItemWidget(item, module_item_widget)

    def _add_module(self, module: Module):
        # Create a copy of the module with a unique identifier
        base_module_id = module.id
        existing_count = 0
        for existing_module in self.modules:
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
        
        # Set initial position in the center of the visible area
        unique_module.x = 100 + (existing_count * 20)  # Offset each new module slightly
        unique_module.y = 100 + (existing_count * 20)
        
        # Add the module to our list
        self.modules.append(unique_module)
        
        # Draw the module on the scene
        self._draw_module(unique_module)

    def _draw_module(self, module: Module):
        # Create a draggable module item
        module_item = DraggableModuleItem(
            module.x, module.y, 
            module.size_x, module.size_y, 
            module, self
        )
        
        # Add the module item to the scene
        self.scene.addItem(module_item)
        
        # Store a reference to the item
        self.module_items.append(module_item)

    def _remove_module(self, module: Module):
        # Remove the module from our list
        if module in self.modules:
            self.modules.remove(module)
            
            # Find and remove the corresponding module item from the scene
            for item in self.module_items:
                if item.module == module:
                    self.scene.removeItem(item)
                    self.module_items.remove(item)
                    break
        
        # Redraw the space
        self._draw_space()