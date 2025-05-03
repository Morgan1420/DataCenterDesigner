from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGroupBox, QScrollArea, QSplitter, QListWidgetItem
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor
from screens.exterior_screen_modules import ExteriorSpace, Subspace
from modules import Module, distancia_entre_modulos


class ExteriorScreen(QWidget):
    def __init__(self, exterior_space: ExteriorSpace, available_modules: list[Module], environment=None, center=None):
        super().__init__()
        if not isinstance(exterior_space, ExteriorSpace):
            raise TypeError(f"Expected ExteriorSpace object, but received {type(exterior_space)}")
        self.exterior_space: ExteriorSpace = exterior_space
        self.available_modules = available_modules
        self.environment = environment  # Guardar referencia al Environment
        self.center = center  # Guardar referencia al Center
        self.subspace_scenes = {}  # Dictionary to store scenes: {(x, y): scene}
        self.subspace_module_lists = {}  # Dictionary to store module lists: {(x, y): list_widget}

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
        self.view = QGraphicsView(self.scene)
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

        # Botón para visualizar en 3D los módulos
        self.visualize_3d_button = QPushButton("Visualizar en 3D")
        self.bottom_layout.addWidget(self.visualize_3d_button)
        self.visualize_3d_button.clicked.connect(self._visualize_modules_3d)

        # Scroll area for subspace editors
        self.scroll_area = QScrollArea()
        self.scroll_area_widget = QWidget()
        self.scroll_area_layout = QVBoxLayout()
        self.scroll_area_widget.setLayout(self.scroll_area_layout)
        self.scroll_area.setWidget(self.scroll_area_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(200)  # Set minimum height for the scroll area
        self.bottom_layout.addWidget(self.scroll_area)

    def set_center(self, center):
        self.center = center
        #print(f"[ExteriorScreen] Center actualizado: pos=({self.center.x}, {self.center.y})")
        self._draw_space()  # Forzar redibujado siempre

    def set_environment(self, environment):
        self.environment = environment
        if environment:
            try:
                size_x = float(environment.parameters.get('Space_X', 1000))
                size_y = float(environment.parameters.get('Space_Y', 500))
                self.exterior_space.resize(size_x, size_y)
            except Exception:
                pass
        self._draw_space()

    def _draw_space(self):
        self.scene.clear()

        # Dibujar el rectángulo del Environment si existe
        env_width = None
        env_height = None
        if self.environment:
            try:
                env_width = float(self.environment.parameters.get('Space_X', 1000))
                env_height = float(self.environment.parameters.get('Space_Y', 500))
                env_rect = QGraphicsRectItem(0, 0, env_width, env_height)
                env_rect.setBrush(QColor(180, 220, 180))
                self.scene.addItem(env_rect)
            except Exception:
                env_width = self.exterior_space.get_size_x()
                env_height = self.exterior_space.get_size_y()
        else:
            # Draw the exterior space (fallback)
            env_width = self.exterior_space.get_size_x()
            env_height = self.exterior_space.get_size_y()
            space_rect = QGraphicsRectItem(0, 0, env_width, env_height)
            space_rect.setBrush(QColor(200, 200, 200))
            self.scene.addItem(space_rect)

        # Dibujar el Center si existe
        if self.center:
            try:
                center_width = float(self.center.inputs.get('Space_X', 100))
                center_height = float(self.center.inputs.get('Space_Y', 50))
                # Usar la posición relativa respecto al Environment
                if self.environment:
                    center_x, center_y = self.center.get_position(self.environment)
                else:
                    center_x, center_y = getattr(self.center, 'x', 0), getattr(self.center, 'y', 0)
                center_rect = QGraphicsRectItem(center_x, center_y, center_width, center_height)
                center_rect.setBrush(QColor(255, 255, 150))
                center_rect.setPen(QColor(180, 180, 80))
                self.scene.addItem(center_rect)
            except Exception as e:
                print(f"No se pudo dibujar el Center: {e}")
        else:
            print("No se ha definido un Center para dibujar.")
            
        # Draw each subspace and its modules
        for subspace in self.exterior_space.get_subspaces():
            # Draw the subspace boundary
            subspace_rect = QGraphicsRectItem(subspace.x, subspace.y, subspace.size_x, subspace.size_y)
            subspace_rect.setBrush(QColor(100, 150, 200))
            self.scene.addItem(subspace_rect)
            
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

        # Column 2: Subspace modules
        subspace_modules_list = QListWidget()
        # Store reference to this list widget
        self.subspace_module_lists[subspace_coords] = subspace_modules_list
        subspace_modules_list.setMinimumHeight(200)
        subspace_editor_layout.addWidget(subspace_modules_list)

        # Column 3: Subspace graphical representation
        subspace_scene = QGraphicsScene()
        # Store reference to this scene
        self.subspace_scenes[subspace_coords] = subspace_scene
        subspace_view = QGraphicsView(subspace_scene)
        subspace_view.setMinimumHeight(200)
        subspace_editor_layout.addWidget(subspace_view)

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

            # Render modules using their actual coordinates within the subspace
            modules_in_subspace = subspace.get_modules() # Get modules again for drawing
            for module in modules_in_subspace:
                # Use module.x and module.y set by subspace.add_module
                # Use the actual module size for drawing
                module_rect = QGraphicsRectItem(module.x, module.y, module.size_x, module.size_y)
                # Set RED color for modules (255, 0, 0) to match exterior space
                module_rect.setBrush(QColor(255, 0, 0))
                # Add a black border to make it stand out
                module_rect.setPen(QColor(0, 0, 0))
                subspace_scene.addItem(module_rect)

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

    def _visualize_modules_3d(self):
        """Llama a la función de visualización 3D con todos los módulos de todos los subespacios, el Center y el Environment como suelo si existe."""
        from visualization_3d import draw_modules_3d
        all_modules = []
        for subspace in self.exterior_space.get_subspaces():
            all_modules.extend(subspace.get_modules())
        if all_modules or self.center:
            center_width = float(self.center.inputs.get('Space_X', 100))
            center_height = float(self.center.inputs.get('Space_Y', 50))
            draw_modules_3d(all_modules, title="Visualización 3D de Módulos en ExteriorSpace", environment=self.environment, center=self.center, center_width=center_width, center_height=center_height)
        else:
            QMessageBox.information(self, "Sin módulos", "No hay módulos para visualizar en 3D.")

    def distancia_entre_center_y_modulo(self, modulo):
        """
        Devuelve la distancia entre el Center y un módulo (en el exterior), usando el Environment si está disponible.
        """
        if self.center is None or modulo is None:
            return None
        return distancia_entre_modulos(self.center, modulo, self.environment)
