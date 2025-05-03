from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGroupBox, QScrollArea, QSplitter, QListWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from screens.interior_screen_modules import InteriorSpace, Subspace
from modules import Module

class InteriorScreen(QWidget):
    def __init__(self, interior_space: InteriorSpace, available_modules: list[Module]):
        super().__init__()
        if not isinstance(interior_space, InteriorSpace):
            raise TypeError(f"Expected InteriorSpace object, but received {type(interior_space)}")
        self.interior_space: InteriorSpace = interior_space
        self.available_modules = available_modules
        self.subspace_scenes = {}
        self.subspace_module_lists = {}

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.splitter = QSplitter(Qt.Vertical)
        self.main_layout.addWidget(self.splitter)

        self.top_widget = QWidget()
        self.top_layout = QVBoxLayout()
        self.top_widget.setLayout(self.top_layout)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.top_layout.addWidget(self.view)
        self.splitter.addWidget(self.top_widget)

        self._draw_space()

        self.bottom_widget = QWidget()
        self.bottom_layout = QVBoxLayout()
        self.bottom_widget.setLayout(self.bottom_layout)
        self.splitter.addWidget(self.bottom_widget)

        self.add_subspace_button = QPushButton("Add Subspace")
        self.bottom_layout.addWidget(self.add_subspace_button)
        self.add_subspace_button.clicked.connect(self._add_subspace)

        self.scroll_area = QScrollArea()
        self.scroll_area_widget = QWidget()
        self.scroll_area_layout = QVBoxLayout()
        self.scroll_area_widget.setLayout(self.scroll_area_layout)
        self.scroll_area.setWidget(self.scroll_area_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(200)
        self.bottom_layout.addWidget(self.scroll_area)

    def _draw_space(self):
        self.scene.clear()
        space_rect = QGraphicsRectItem(0, 0, self.interior_space.get_size_x(), self.interior_space.get_size_y())
        space_rect.setBrush(QColor(220, 220, 200))
        self.scene.addItem(space_rect)
        for subspace in self.interior_space.get_subspaces():
            subspace_rect = QGraphicsRectItem(subspace.x, subspace.y, subspace.size_x, subspace.size_y)
            subspace_rect.setBrush(QColor(100, 200, 150))
            self.scene.addItem(subspace_rect)
            for module in subspace.get_modules():
                module_x = subspace.x + getattr(module, 'x', 0)
                module_y = subspace.y + getattr(module, 'y', 0)
                module_width = getattr(module, 'size_x', 20)
                module_height = getattr(module, 'size_y', 20)
                if module_width > 0 and module_height > 0:
                    module_rect = QGraphicsRectItem(module_x, module_y, module_width, module_height)
                    module_rect.setBrush(QColor(200, 100, 200))
                    self.scene.addItem(module_rect)

    def _add_subspace(self):
        new_subspace = Subspace(50, 50)
        num_existing_subspaces = len(self.interior_space.get_subspaces())
        new_x = num_existing_subspaces * (new_subspace.size_x + 10)
        new_y = 10
        if (new_x + new_subspace.size_x <= self.interior_space.get_size_x() and
            new_y + new_subspace.size_y <= self.interior_space.get_size_y()):
            new_subspace.set_position(new_x, new_y)
            self.interior_space.add_subspace(new_subspace)
            self._draw_space()
            self._add_subspace_editor(new_subspace)
        else:
            QMessageBox.warning(self, "Error", "Cannot add new subspace, not enough space in the interior area.")

    def _add_subspace_editor(self, subspace: Subspace):
        subspace_coords = (subspace.x, subspace.y)
        subspace_editor_group = QGroupBox(f"Subspace Editor ({subspace.x}, {subspace.y})")
        subspace_editor_layout = QHBoxLayout()
        subspace_editor_group.setLayout(subspace_editor_layout)
        available_modules_list = QListWidget()
        available_modules_list.setMinimumHeight(200)
        subspace_editor_layout.addWidget(available_modules_list)
        self._populate_available_modules(available_modules_list, subspace)
        subspace_modules_list = QListWidget()
        self.subspace_module_lists[subspace_coords] = subspace_modules_list
        subspace_modules_list.setMinimumHeight(200)
        subspace_editor_layout.addWidget(subspace_modules_list)
        subspace_scene = QGraphicsScene()
        self.subspace_scenes[subspace_coords] = subspace_scene
        subspace_view = QGraphicsView(subspace_scene)
        subspace_view.setMinimumHeight(200)
        subspace_editor_layout.addWidget(subspace_view)
        self._update_subspace_editor(subspace, subspace_modules_list, subspace_scene)
        self.scroll_area_layout.addWidget(subspace_editor_group)

    def _populate_available_modules(self, available_modules_list, subspace: Subspace):
        available_modules_list.clear()
        for module in self.available_modules:
            module_item_widget = QWidget()
            module_item_layout = QHBoxLayout()
            module_item_widget.setLayout(module_item_layout)
            module_label = QLabel(module.id)
            module_item_layout.addWidget(module_label)
            add_button = QPushButton("Add")
            add_button.clicked.connect(lambda _, m=module: self._add_module_to_subspace(m, subspace))
            module_item_layout.addWidget(add_button)
            item = QListWidgetItem()
            item.setSizeHint(module_item_widget.sizeHint())
            available_modules_list.addItem(item)
            available_modules_list.setItemWidget(item, module_item_widget)

    def _add_module_to_subspace(self, module: Module, subspace: Subspace):
        subspace_coords = (subspace.x, subspace.y)
        base_module_id = module.id
        existing_count = 0
        for existing_module in subspace.get_modules():
            if existing_module.id.startswith(base_module_id):
                existing_count += 1
        unique_module = Module(
            id=f"{base_module_id}_{existing_count + 1}",
            inputs=module.inputs.copy(),
            outputs=module.outputs.copy(),
            size_x=getattr(module, 'size_x', 20),
            size_y=getattr(module, 'size_y', 20)
        )
        subspace.add_module(unique_module)
        subspace_modules_list = self.subspace_module_lists.get(subspace_coords)
        subspace_scene = self.subspace_scenes.get(subspace_coords)
        if subspace_modules_list and subspace_scene:
            self._update_subspace_editor(subspace, subspace_modules_list, subspace_scene)
            self._draw_space()

    def _update_subspace_editor(self, subspace: Subspace, subspace_modules_list=None, subspace_scene=None):
        subspace_coords = (subspace.x, subspace.y)
        if subspace_modules_list:
            subspace_modules_list.clear()
            modules_in_subspace = subspace.get_modules()
            for module in modules_in_subspace:
                module_item_widget = QWidget()
                module_item_layout = QHBoxLayout()
                module_item_widget.setLayout(module_item_layout)
                module_label = QLabel(module.id)
                module_item_layout.addWidget(module_label)
                delete_button = QPushButton("Delete")
                delete_button.clicked.connect(lambda checked=False, m=module, s=subspace: self._remove_module_from_subspace(m, s))
                module_item_layout.addWidget(delete_button)
                item = QListWidgetItem()
                item.setSizeHint(module_item_widget.sizeHint())
                subspace_modules_list.addItem(item)
                subspace_modules_list.setItemWidget(item, module_item_widget)
        if subspace_scene:
            subspace_scene.clear()
            subspace_rect = QGraphicsRectItem(0, 0, subspace.size_x, subspace.size_y)
            subspace_rect.setBrush(QColor(180, 220, 250))
            subspace_scene.addItem(subspace_rect)
            modules_in_subspace = subspace.get_modules()
            for module in modules_in_subspace:
                module_width = getattr(module, 'size_x', 20)
                module_height = getattr(module, 'size_y', 20)
                module_rect = QGraphicsRectItem(getattr(module, 'x', 0), getattr(module, 'y', 0), module_width, module_height)
                module_rect.setBrush(QColor(200, 100, 200))
                subspace_scene.addItem(module_rect)
            view = subspace_scene.views()
            if view:
                view[0].setSceneRect(subspace_scene.itemsBoundingRect())
            subspace_scene.update()

    def _remove_module_from_subspace(self, module: Module, subspace: Subspace):
        subspace_coords = (subspace.x, subspace.y)
        subspace.remove_module(module)
        subspace_modules_list = self.subspace_module_lists.get(subspace_coords)
        subspace_scene = self.subspace_scenes.get(subspace_coords)
        if subspace_modules_list and subspace_scene:
            self._update_subspace_editor(subspace, subspace_modules_list, subspace_scene)
            self._draw_space()
