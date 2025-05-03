import sys
import random
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QPen, QBrush, QColor, QPainter
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
    QScrollArea, QFormLayout, QLineEdit, QSplitter, QGroupBox, QMessageBox,
    QDoubleSpinBox, QMenu
)
# Importar clases base necesarias de modules
from modules import Module, Environment, Center

# --- Pantalla de Configuración del Entorno ---
class EnvironmentSetupScreen(QWidget):
    environment_changed = Signal(object)  # Señal que envía el Environment activo
    # Modificar constructor para aceptar todos los tipos de módulos de entorno
    def __init__(self, available_envs, available_hpls, available_lpls, available_wcs, available_ars, available_centers=None):
        super().__init__()
        # Almacenar todas las listas de objetos disponibles
        self.available_items = {
            "Environment": available_envs,
            "HighPowerLine": available_hpls,
            "LowPowerLine": available_lpls,
            "WaterConnection": available_wcs,
            "AccessRoad": available_ars,
            "Center": available_centers if available_centers is not None else []
        }
        
        # Diccionario unificado para guardar items añadidos al mapa {unique_id: (object, type_str)}
        self.active_items_on_map = {}
        self.map_item_counter = 0
        self.selected_map_item_unique_id = None

        self.setWindowTitle("Configuración del Entorno")
        main_layout = QHBoxLayout(self)
        main_splitter = QSplitter(Qt.Orientation.Horizontal) # Usar Qt.Orientation

        # --- Panel Izquierdo (Elementos Disponibles) ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 5, 0, 5)

        left_title = QLabel("Elementos de Entorno Disponibles")
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter) # Usar Qt.AlignmentFlag
        left_layout.addWidget(left_title)

        self.item_list_widget = QListWidget()
        self.item_list_widget.setStyleSheet("QListWidget::item { border-bottom: 1px solid lightgray; padding: 5px; }")
        left_layout.addWidget(self.item_list_widget)

        self.populate_available_items() # Llenar la lista con todos los tipos

        # --- Panel Derecho (Control de Entorno) ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_splitter = QSplitter(Qt.Orientation.Vertical)

        # --- Zona Superior (Mapa) ---
        map_container = QWidget()
        map_layout = QVBoxLayout(map_container)
        map_layout.setContentsMargins(5,5,5,5)
        map_title = QLabel("Mapa del Entorno Exterior")
        map_title.setAlignment(Qt.AlignmentFlag.AlignCenter) # Usar Qt.AlignmentFlag
        map_layout.addWidget(map_title)

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 500, 300) # Aumentar tamaño inicial escena
        self.view = MapGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing) # Usar QPainter.RenderHint
        self.view.setStyleSheet("background-color: #e0f0e0;")
        # Permitir arrastrar para mover la vista
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        map_layout.addWidget(self.view)
        right_splitter.addWidget(map_container)

        # --- Zona Inferior (Detalles del Elemento) ---
        details_container = QWidget()
        details_layout = QVBoxLayout(details_container)
        details_layout.setContentsMargins(5,5,5,5)
        details_title = QLabel("Detalles del Elemento Seleccionado")
        details_title.setAlignment(Qt.AlignmentFlag.AlignCenter) # Usar Qt.AlignmentFlag
        details_layout.addWidget(details_title)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.details_widget = QWidget()
        self.details_main_layout = QVBoxLayout(self.details_widget)
        self.details_main_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Usar Qt.AlignmentFlag
        self.scroll_area.setWidget(self.details_widget)
        details_layout.addWidget(self.scroll_area)
        right_splitter.addWidget(details_container)

        # Ajustar tamaños iniciales del splitter vertical
        right_splitter.setSizes([400, 200]) # Más espacio para el mapa

        right_layout.addWidget(right_splitter)

        # Añadir paneles al splitter principal
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)

        # Ajustar tamaños iniciales del splitter horizontal (1/4 izquierda, 3/4 derecha)
        main_splitter.setSizes([250, 650]) # Ajustar según necesidad

        main_layout.addWidget(main_splitter)

        # Conexiones
        self.scene.selectionChanged.connect(self.on_map_item_selected)
        # Atajo Ctrl+A para seleccionar todo
        self._select_all_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+A"), self)
        self._select_all_shortcut.activated.connect(self.select_all_items)
        # Atajo Suprimir para eliminar seleccionados
        self._delete_shortcut = QtGui.QShortcut(QtGui.QKeySequence(Qt.Key_Delete), self)
        self._delete_shortcut.activated.connect(self.delete_selected_items)
        # Limpiar detalles al inicio
        self.clear_details()

    def select_all_items(self):
        for item in self.scene.items():
            if isinstance(item, QGraphicsRectItem):
                item.setSelected(True)

    def delete_selected_items(self):
        selected_items = self.scene.selectedItems()
        environment_ids = []
        to_delete = []
        for item in selected_items:
            if isinstance(item, QGraphicsTextItem):
                item = item.parentItem()
            if isinstance(item, QGraphicsRectItem) and hasattr(item, 'unique_map_id'):
                unique_id = getattr(item, 'unique_map_id', None)
                if unique_id and unique_id in self.active_items_on_map:
                    obj, t = self.active_items_on_map[unique_id]
                    if t == "Environment":
                        environment_ids.append(unique_id)
                    else:
                        to_delete.append((item, unique_id))
        # Eliminar solo los que no son Environment
        for item, unique_id in to_delete:
            del self.active_items_on_map[unique_id]
            self.scene.removeItem(item)
        self.clear_details()
        self.populate_available_items()

    def populate_available_items(self):
        self.item_list_widget.clear()
        # Comprobar si ya hay un Environment en el mapa
        environment_exists = any(
            isinstance(obj, Environment) for obj, t in self.active_items_on_map.values()
        )
        center_exists = any(isinstance(obj, Center) for obj, t in self.active_items_on_map.values())
        for item_type, item_list in self.available_items.items():
            if not item_list:
                continue

            header_item = QListWidgetItem(f"--- {item_type} ---")
            header_item.setFlags(Qt.ItemFlag.NoItemFlags)
            header_item.setForeground(Qt.GlobalColor.gray)
            self.item_list_widget.addItem(header_item)

            for item_obj in item_list:
                item_widget = QWidget()
                item_layout = QHBoxLayout(item_widget)
                item_layout.setContentsMargins(10, 5, 10, 5)  # Margen interno para cada item
                item_layout.setSpacing(5)
                
                

                label = QLabel(item_obj.id)
                label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
                add_button = QPushButton("+")
                add_button.setFixedSize(30, 30)
                add_button.setToolTip(f"Añadir '{item_obj.id}' ({item_type}) al mapa")
                # Deshabilitar el botón si ya hay un Environment o Center
                if (item_type == "Environment" and environment_exists) or (item_type == "Center" and center_exists):
                    add_button.setEnabled(False)
                    add_button.setToolTip(f"Solo puede haber un {item_type} en el mapa")
                else:
                    add_button.clicked.connect(lambda checked=False, obj=item_obj, type_str=item_type: self.add_item_to_map(obj, type_str))

                item_layout.addWidget(label)
                item_layout.addWidget(add_button)

                list_item = QListWidgetItem(self.item_list_widget)
                list_item.setSizeHint(item_widget.sizeHint())
                self.item_list_widget.addItem(list_item)
                self.item_list_widget.setItemWidget(list_item, item_widget)

    def _rects_overlap_completely(self, rect1, rect2):
        # Devuelve True si rect1 está completamente dentro de rect2 o viceversa
        return (rect1.contains(rect2) or rect2.contains(rect1))

    def _find_non_overlapping_position(self, item_width, item_height):
        # Intenta encontrar una posición donde el nuevo rect no se solape con otros
        scene_w = self.scene.width()
        scene_h = self.scene.height()
        x = random.randint(10, int(scene_w - item_width - 10)) if scene_w - item_width > 20 else 0
        y = random.randint(10, int(scene_h - item_height - 10)) if scene_h - item_height > 20 else 0
        max_attempts = 30
        for _ in range(max_attempts):
            new_rect = QRectF(x, y, item_width, item_height)
            collision = False
            for item in self.scene.items():
                if isinstance(item, QGraphicsRectItem):
                    if new_rect.intersects(item.rect()):
                        # Cualquier solapamiento, mover debajo usando la altura del nuevo item
                        y = item.rect().y() + item.rect().height() + item_height
                        collision = True
                        break
            if not collision:
                return x, y
        # Si no encuentra hueco tras varios intentos, devuelve la última posición
        return x, y

    def add_item_to_map(self, item_object, item_type_str):
        # Si es Environment y ya existe uno, actualizar sus parámetros sumando los valores numéricos
        if item_type_str == "Environment":
            for unique_id, (obj, t) in self.active_items_on_map.items():
                if isinstance(obj, Environment):
                    # Sumar los valores numéricos de los parámetros
                    for k, v in item_object.parameters.items():
                        try:
                            v_existente = obj.parameters.get(k, 0)
                            # Intentar convertir ambos a float y sumar
                            obj.parameters[k] = float(v_existente) + float(v)
                        except Exception:
                            # Si no es numérico, mantener el valor existente
                            pass
                    self.update_map_tooltip(unique_id, obj)
                    self.display_item_details(obj, "Environment")
                    self.environment_changed.emit(obj)  # Emitir señal al actualizar
                    QMessageBox.information(self, "Actualizado", "Los parámetros numéricos del Environment han sido actualizados (sumados). Solo puede haber uno en el mapa.")
                    return
        # Si es Center y ya existe uno, no permitir añadir otro
        if item_type_str == "Center":
            for unique_id, (obj, t) in self.active_items_on_map.items():
                if isinstance(obj, Center):
                    QMessageBox.information(self, "Center", "Solo puede haber un Center en el mapa.")
                    return
        unique_map_id = f"{item_type_str}_{item_object.id}_{self.map_item_counter}"
        self.map_item_counter += 1

        print(f"Añadiendo '{item_object.id}' ({item_type_str}) al mapa con ID único: {unique_map_id}")
        self.active_items_on_map[unique_map_id] = (item_object, item_type_str)

        # --- Determinar tamaño del bloque ---
        min_size = 30
        default_size_x = 60
        default_size_y = 40
        item_width = default_size_x
        item_height = default_size_y

        # Si es PowerLine o AccessRoad, forzar tamaño horizontal muy grande y vertical pequeño
        if item_type_str in ["HighPowerLine", "LowPowerLine", "AccessRoad", "WaterConnection"]:
            item_width = self.scene.width() * 4
            item_height = 20
            # Centrar la línea en la escena
            x = (self.scene.width() - item_width) / 2
            y = (self.scene.height() - item_height) / 2
        elif isinstance(item_object, Center):
            # Usar Space_X y Space_Y del Center para el tamaño
            try:
                item_width = max(min_size, self.available_items["Center"][0].inputs.get('Space_X'))
                item_height = max(min_size, self.available_items["Center"][0].inputs.get('Space_Y'))
            except Exception:
                item_width = default_size_x
                item_height = default_size_y
        elif isinstance(item_object, Module) and not isinstance(item_object, Center):
            print("jhdask")
            try:
                space_x = float(item_object.inputs.get('Space_X', default_size_x))
                space_y = float(item_object.inputs.get('Space_Y', default_size_y))
                item_width = max(min_size, space_x)
                item_height = max(min_size, space_y)
            except (ValueError, TypeError, AttributeError):
                print(f"  Advertencia: No se pudo obtener Space_X/Y numérico para {item_object.id}. Usando tamaño por defecto.")
                item_width = default_size_x
                item_height = default_size_y
        elif isinstance(item_object, Environment):
            # Usar Space_X y Space_Y del Environment para el tamaño
            try:
                item_width = max(min_size, self.available_items["Environment"][0].parameters.get('Space_X'))
                item_height = max(min_size, self.available_items["Environment"][0].parameters.get('Space_Y'))
            except Exception:
                item_width = default_size_x
                item_height = default_size_y
        

        
        # Limitar tamaño máximo al de la escena menos márgenes (excepto PowerLine y AccessRoad)
        if item_type_str not in ["HighPowerLine", "LowPowerLine", "AccessRoad", "WaterConnection", "Center"] and not isinstance(item_object, Environment):
            item_width = default_size_x
            item_height = default_size_y

        # --- Crear representación gráfica ---
        color = QtGui.QColor(200, 200, 200)
        if item_type_str == "Environment":
            color = QtGui.QColor(180, 220, 180)
        elif "PowerLine" in item_type_str:
            color = QtGui.QColor(255, 200, 150)
        elif "WaterConnection" in item_type_str:
            color = QtGui.QColor(150, 200, 255)
        elif "AccessRoad" in item_type_str:
            color = QtGui.QColor(220, 220, 220)
        elif "Center" in item_type_str:
            color = QtGui.QColor(255, 255, 150)

        # Calcular posición
        if item_type_str == "Environment":
            x = -int(item_width) / 4
            y = -int(item_height) / 4
        else:
            x, y = self._find_non_overlapping_position(item_width, item_height)

        rect_item = QGraphicsRectItem(x, y, item_width, item_height)
        rect_item.setBrush(color)
        rect_item.setPen(QPen(Qt.GlobalColor.black))
        rect_item.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        rect_item.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        rect_item.setToolTip(f"{item_type_str}: {item_object.id}")
        rect_item.unique_map_id = unique_map_id
        rect_item.rotation_angle = 0
        # Fijar el punto de rotación en el centro
        if item_type_str in ["HighPowerLine", "LowPowerLine", "AccessRoad", "WaterConnection"]:
            rect_item.setTransformOriginPoint(item_width/2, item_height/2)

        # --- Añadir soporte para menú contextual (clic derecho) ---
        rect_item.setAcceptHoverEvents(True)
        rect_item.contextMenuEvent = lambda event, item=rect_item: self.show_item_context_menu(event, item)

        # --- Siempre poner el Environment debajo ---
        if item_type_str == "Environment":
            rect_item.setZValue(-100)
        else:
            rect_item.setZValue(0)

        # --- Añadir texto centrado ---
        text_item = QGraphicsTextItem(item_object.id, rect_item)
        text_item.setDefaultTextColor(Qt.GlobalColor.black)
        text_rect = text_item.boundingRect()
        text_x = x + (item_width - text_rect.width()) / 2
        text_y = y + (item_height - text_rect.height()) / 2
        text_item.setPos(text_x, text_y)
        text_item.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        text_item.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)

        self.scene.addItem(rect_item)
        rect_item.setSelected(True)
        # Refrescar la lista para deshabilitar el botón si es necesario
        self.populate_available_items()
        # No es necesario llamar a display_item_details aquí, on_map_item_selected lo hará

        # Si es la primera PowerLine, AccessRoad o WaterConnection añadida, conectar el atajo Ctrl+R
        if item_type_str in ["HighPowerLine", "LowPowerLine", "AccessRoad", "WaterConnection"]:
            if not hasattr(self, '_powerline_shortcut_connected'):
                self._powerline_shortcut_connected = True
                self._powerline_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+R"), self)
                self._powerline_shortcut.activated.connect(self.rotate_selected_powerline)

        if item_type_str == "Environment":
            self.environment_changed.emit(item_object)  # Emitir señal al añadir

    def on_map_item_selected(self):
        selected_items = self.scene.selectedItems()
        if selected_items:
            item = selected_items[0]
            if isinstance(item, QGraphicsTextItem):
                 item = item.parentItem()

            if isinstance(item, QGraphicsRectItem) and hasattr(item, 'unique_map_id'):
                unique_id = item.unique_map_id
                if unique_id in self.active_items_on_map:
                    self.selected_map_item_unique_id = unique_id
                    item_object, item_type_str = self.active_items_on_map[unique_id]
                    self.display_item_details(item_object, item_type_str)
                else:
                    print(f"Error: ID de mapa único '{unique_id}' no encontrado en activos.")
                    self.clear_details()
            else:
                 self.clear_details()
        else:
            self.selected_map_item_unique_id = None
            self.clear_details()

    def display_item_details(self, item_object, item_type_str):
        # Limpiar detalles anteriores
        while self.details_main_layout.count():
            child = self.details_main_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                # Limpiar layout recursivamente
                layout = child.layout()
                while layout.count():
                    sub_item = layout.takeAt(0)
                    if sub_item and sub_item.widget():
                        sub_item.widget().deleteLater()
                layout.deleteLater()

        # Layout base para ID y Tipo (no editables)
        base_info_layout = QFormLayout()
        base_info_layout.addRow("ID:", QLabel(item_object.id))
        base_info_layout.addRow("Tipo:", QLabel(item_type_str))
        self.details_main_layout.addLayout(base_info_layout)

        # Si es PowerLine, AccessRoad o WaterConnection, mostrar botón Rotar y parámetro especial editable
        if item_type_str in ["HighPowerLine", "LowPowerLine", "AccessRoad", "WaterConnection"]:
            # Layout para parámetros especiales
            param_layout = QFormLayout()
            # PowerLine: mostrar y editar 'power'
            if item_type_str in ["HighPowerLine", "LowPowerLine"]:
                power_val = self.available_items[item_type_str][0].outputs["Usable_Power"]
                
                power_editor = QDoubleSpinBox()
                power_editor.setRange(-999999999, 999999999)
                power_editor.setValue(float(power_val) if power_val is not None else 0.0)
                power_editor.valueChanged.connect(
                    lambda val, obj=item_object, uid=self.selected_map_item_unique_id:
                        self.update_parameter(uid, "input", "power", val)
                )
                param_layout.addRow("Power:", power_editor)
            # WaterConnection: mostrar y editar 'water supply' y largo
            elif item_type_str == "WaterConnection":
                water_val = self.available_items[item_type_str][0].outputs["Water_flow"]
                
                water_editor = QDoubleSpinBox()
                water_editor.setRange(-999999999, 999999999)
                water_editor.setValue(float(water_val) if water_val is not None else 0.0)
                water_editor.valueChanged.connect(
                    lambda val, obj=item_object, uid=self.selected_map_item_unique_id:
                        self.update_parameter(uid, "input", "water supply", val)
                )
                param_layout.addRow("Water Supply:", water_editor)
                
            
            
            self.details_main_layout.addLayout(param_layout)
            rotate_btn = QPushButton("Rotar (Ctrl+R)")
            rotate_btn.clicked.connect(self.rotate_selected_powerline)
            self.details_main_layout.addWidget(rotate_btn)
            self.details_main_layout.addStretch(1)
            return

        # --- Detalles específicos y editables ---
        if isinstance(item_object, Environment):
            params_group_box = QGroupBox("Parámetros Editables")
            params_form_layout = QFormLayout()
            for param, value in item_object.parameters.items():
                value_str = str(value) if value is not None else ""
                editor = QLineEdit(value_str)
                editor.textChanged.connect(
                    # Usar unique_id para asegurar que actualizamos el correcto si hay duplicados
                    lambda text, p=param, obj=item_object, uid=self.selected_map_item_unique_id:
                    self.update_parameter(uid, "parameter", p, text)
                )
                params_form_layout.addRow(f"{param}:", editor)
            params_group_box.setLayout(params_form_layout)
            self.details_main_layout.addWidget(params_group_box)

        elif isinstance(item_object, Module):
            # Inputs Editables
            inputs_group_box = QGroupBox("Inputs Editables")
            inputs_form_layout = QFormLayout()
            if item_object.inputs:
                for unit, amount in item_object.inputs.items():
                    # Usar QDoubleSpinBox para valores numéricos como Amount, Space_X, Space_Y
                    # Usar QLineEdit para otros como Price, Unit (si fueran editables)
                    if unit in ['Space_X', 'Space_Y', 'Amount'] or isinstance(amount, (int, float)):
                         editor = QDoubleSpinBox()
                         editor.setRange(-999999999, 999999999) # Rango amplio
                         editor.setValue(float(amount) if amount is not None else 0.0)
                         editor.valueChanged.connect(
                             lambda val, u=unit, obj=item_object, uid=self.selected_map_item_unique_id:
                             self.update_parameter(uid, "input", u, val)
                         )
                    else: # Para otros tipos (ej. Price, Grid_Connection como texto)
                         editor = QLineEdit(str(amount) if amount is not None else "")
                         editor.textChanged.connect(
                             lambda text, u=unit, obj=item_object, uid=self.selected_map_item_unique_id:
                             self.update_parameter(uid, "input", u, text)
                         )
                    inputs_form_layout.addRow(f"{unit}:", editor)
            else:
                inputs_form_layout.addRow(QLabel("Ninguno"))
            inputs_group_box.setLayout(inputs_form_layout)
            self.details_main_layout.addWidget(inputs_group_box)

            # Outputs Editables (similar a Inputs)
            outputs_group_box = QGroupBox("Outputs Editables")
            outputs_form_layout = QFormLayout()
            if item_object.outputs:
                for unit, amount in item_object.outputs.items():
                    if isinstance(amount, (int, float)):
                         editor = QDoubleSpinBox()
                         editor.setRange(-999999999, 999999999)
                         editor.setValue(float(amount) if amount is not None else 0.0)
                         editor.valueChanged.connect(
                             lambda val, u=unit, obj=item_object, uid=self.selected_map_item_unique_id:
                             self.update_parameter(uid, "output", u, val)
                         )
                    else:
                         editor = QLineEdit(str(amount) if amount is not None else "")
                         editor.textChanged.connect(
                             lambda text, u=unit, obj=item_object, uid=self.selected_map_item_unique_id:
                             self.update_parameter(uid, "output", u, text)
                         )
                    outputs_form_layout.addRow(f"{unit}:", editor)
            else:
                outputs_form_layout.addRow(QLabel("Ninguno"))
            outputs_group_box.setLayout(outputs_form_layout)
            self.details_main_layout.addWidget(outputs_group_box)

        self.details_main_layout.addStretch(1) # Empujar todo hacia arriba

    def update_parameter(self, unique_map_id, param_type, key, new_value):
        """Actualiza un parámetro, input o output del objeto asociado al unique_map_id."""
        if unique_map_id is None or unique_map_id not in self.active_items_on_map:
            print(f"Error: No se puede actualizar parámetro, ID de mapa no válido o no encontrado: {unique_map_id}")
            return

        item_object, item_type_str = self.active_items_on_map[unique_map_id]
        try:
            if param_type == "parameter" and isinstance(item_object, Environment):
                print(f"Actualizando Parámetro {item_object.id}: {key} = {new_value}")
                item_object.parameters[key] = new_value
                # Si el parámetro es Space_X o Space_Y, intentar redimensionar
                if key in ['Space_X', 'Space_Y']:
                    self.resize_map_item(unique_map_id, item_object)
                self.update_map_tooltip(unique_map_id, item_object)
                self.environment_changed.emit(item_object)  # Emitir señal al editar
            elif param_type == "input" and isinstance(item_object, Module):
                print(f"Actualizando Input {item_object.id}: {key} = {new_value}")
                try:
                    current_value = item_object.inputs.get(key)
                    if isinstance(current_value, (int, float)) or isinstance(new_value, float):
                        item_object.inputs[key] = float(new_value)
                    else:
                        item_object.inputs[key] = new_value
                except ValueError:
                    item_object.inputs[key] = new_value
                if key in ['Space_X', 'Space_Y']:
                    self.resize_map_item(unique_map_id, item_object)
                self.update_map_tooltip(unique_map_id, item_object)
            elif param_type == "output" and isinstance(item_object, Module):
                print(f"Actualizando Output {item_object.id}: {key} = {new_value}")
                try:
                    current_value = item_object.outputs.get(key)
                    if isinstance(current_value, (int, float)) or isinstance(new_value, float):
                        item_object.outputs[key] = float(new_value)
                    else:
                        item_object.outputs[key] = new_value
                except ValueError:
                    item_object.outputs[key] = new_value
                # Si el output es Space_X o Space_Y, también redimensionar
                if key in ['Space_X', 'Space_Y']:
                    self.resize_map_item(unique_map_id, item_object)
                self.update_map_tooltip(unique_map_id, item_object)
            else:
                print(f"Advertencia: Tipo de parámetro '{param_type}' o tipo de objeto '{item_type_str}' no manejado para la actualización.")
        except Exception as e:
            print(f"Error actualizando parámetro {key} para {item_object.id}: {e}")

    def update_map_tooltip(self, unique_map_id, item_object):
        """Actualiza el tooltip de un item en el mapa."""
        for item in self.scene.items():
            if isinstance(item, QGraphicsRectItem) and hasattr(item, 'unique_map_id') and item.unique_map_id == unique_map_id:
                tooltip_text = f"{type(item_object).__name__}: {item_object.id}"
                if isinstance(item_object, Environment):
                    params_str = '\n'.join([f'  {k}: {v}' for k, v in item_object.parameters.items()])
                    tooltip_text += f"\nParámetros:\n{params_str}"
                elif isinstance(item_object, Module):
                    inputs_str = '\n'.join([f'  {k}: {v}' for k, v in item_object.inputs.items()])
                    outputs_str = '\n'.join([f'  {k}: {v}' for k, v in item_object.outputs.items()])
                    if inputs_str: tooltip_text += f"\nInputs:\n{inputs_str}"
                    if outputs_str: tooltip_text += f"\nOutputs:\n{outputs_str}"
                item.setToolTip(tooltip_text)
                break

    def resize_map_item(self, unique_map_id, item_object):
        """Redimensiona un item en el mapa basado en Space_X y Space_Y."""
        for item in self.scene.items():
            if isinstance(item, QGraphicsRectItem) and hasattr(item, 'unique_map_id') and item.unique_map_id == unique_map_id:
                rect_item = item
                min_size = 30
                default_size_x = 60
                default_size_y = 40
                new_width = default_size_x
                new_height = default_size_y
                try:
                    # Buscar Space_X y Space_Y en inputs o parameters
                    if hasattr(item_object, 'inputs') and 'Space_X' in item_object.inputs:
                        space_x = float(item_object.inputs.get('Space_X', default_size_x))
                        new_width = max(min_size, space_x)
                    elif hasattr(item_object, 'parameters') and 'Space_X' in item_object.parameters:
                        space_x = float(item_object.parameters.get('Space_X', default_size_x))
                        new_width = max(min_size, space_x)
                    else:
                        new_width = default_size_x
                    if hasattr(item_object, 'inputs') and 'Space_Y' in item_object.inputs:
                        space_y = float(item_object.inputs.get('Space_Y', default_size_y))
                        new_height = max(min_size, space_y)
                    elif hasattr(item_object, 'parameters') and 'Space_Y' in item_object.parameters:
                        space_y = float(item_object.parameters.get('Space_Y', default_size_y))
                        new_height = max(min_size, space_y)
                    else:
                        new_height = default_size_y
                except (ValueError, TypeError):
                    pass
                current_rect = rect_item.rect()
                rect_item.setRect(current_rect.x(), current_rect.y(), new_width, new_height)
                # Reposicionar el texto hijo
                text_item = None
                for child in rect_item.childItems():
                    if isinstance(child, QGraphicsTextItem):
                        text_item = child
                        break
                if text_item:
                    text_rect = text_item.boundingRect()
                    text_x = (new_width - text_rect.width()) / 2
                    text_y = (new_height - text_rect.height()) / 2
                    text_item.setPos(text_x, text_y)
                print(f"Item {item_object.id} redimensionado a {new_width}x{new_height}")
                self.scene.update()
                break

    def clear_details(self):
        # Limpiar layout de detalles
        while self.details_main_layout.count():
            item = self.details_main_layout.takeAt(0)
            widget = item.widget()
            layout = item.layout()
            if widget:
                widget.deleteLater()
            elif layout:
                # Limpiar layout recursivamente
                while layout.count():
                    sub_item = layout.takeAt(0)
                    sub_widget = sub_item.widget()
                    sub_layout = sub_item.layout()
                    if sub_widget:
                        sub_widget.deleteLater()
                    elif sub_layout: # Podría haber más niveles, pero para QFormLayout esto basta
                         while sub_layout.count():
                              ss_item = sub_layout.takeAt(0)
                              if ss_item and ss_item.widget(): ss_item.widget().deleteLater()
                         sub_layout.deleteLater()
                layout.deleteLater()

        placeholder_label = QLabel("Selecciona un elemento del mapa para ver/editar sus detalles.")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # Usar Qt.AlignmentFlag
        self.details_main_layout.addWidget(placeholder_label)
        self.details_main_layout.addStretch(1)

    def rotate_selected_powerline(self):
        # Solo rota si el seleccionado es PowerLine
        selected_items = self.scene.selectedItems()
        if not selected_items:
            return
        item = selected_items[0]
        if isinstance(item, QGraphicsTextItem):
            item = item.parentItem()
        if not (isinstance(item, QGraphicsRectItem) and hasattr(item, 'unique_map_id')):
            return
        unique_id = item.unique_map_id
        _, type_str = self.active_items_on_map.get(unique_id, (None, None))
        if type_str not in ["HighPowerLine", "LowPowerLine", "AccessRoad", "WaterConnection"]:
            return
        # Rotar 90 grados
        angle = getattr(item, 'rotation_angle', 0)
        angle = (angle + 90) % 360
        item.setRotation(angle)
        item.rotation_angle = angle
        # Opcional: centrar el texto de nuevo
        for child in item.childItems():
            if isinstance(child, QGraphicsTextItem):
                rect = item.rect()
                text_rect = child.boundingRect()
                child.setPos((rect.width() - text_rect.width()) / 2, (rect.height() - text_rect.height()) / 2)
        self.scene.update()

    def show_item_context_menu(self, event, rect_item):
        unique_id = getattr(rect_item, 'unique_map_id', None)
        if unique_id and unique_id in self.active_items_on_map:
            obj, t = self.active_items_on_map[unique_id]
            if t == "Environment":
                # No mostrar menú contextual para eliminar Environment
                return
        menu = QMenu()
        delete_action = menu.addAction("Eliminar")
        action = menu.exec(event.screenPos())
        if action == delete_action:
            if unique_id and unique_id in self.active_items_on_map:
                del self.active_items_on_map[unique_id]
                self.scene.removeItem(rect_item)
                self.clear_details()
                self.populate_available_items()
            if hasattr(self, 'view') and hasattr(self.view, '_rubber_band_active'):
                self.view._rubber_band_active = False
                self.view._rubber_band_rect = None
                self.view.viewport().update()

    def get_active_environment(self):
        # Devuelve el primer Environment en el mapa, o None si no hay
        for obj, t in self.active_items_on_map.values():
            if isinstance(obj, Environment):
                return obj
        return None

class MapGraphicsView(QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._zoom = 0
        self._zoom_step = 1.15
        self._zoom_range = (0.1, 10)
        # --- Selección por arrastre con botón derecho ---
        self._rubber_band_origin = None
        self._rubber_band_rect = None
        self._rubber_band_active = False

    def wheelEvent(self, event):
        # Zoom in/out con la rueda del ratón
        if event.angleDelta().y() > 0:
            zoom_factor = self._zoom_step
        else:
            zoom_factor = 1 / self._zoom_step
        current_scale = self.transform().m11()
        new_scale = current_scale * zoom_factor
        if self._zoom_range[0] <= new_scale <= self._zoom_range[1]:
            self.scale(zoom_factor, zoom_factor)
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Comprobar si el clic es sobre un item seleccionable y seleccionado
            pos = event.position().toPoint()
            scene_pos = self.mapToScene(pos)
            items = self.scene().items(scene_pos)
            for item in items:
                if item.isSelected() and item.flags() & QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable:
                    # Permitir mover el item normalmente
                    super().mousePressEvent(event)
                    return
            # Si no hay item seleccionado bajo el cursor, iniciar selección por arrastre
            self._rubber_band_origin = pos
            self._rubber_band_rect = QtCore.QRect(self._rubber_band_origin, self._rubber_band_origin)
            self._rubber_band_active = True
            self.viewport().update()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._rubber_band_active and self._rubber_band_origin is not None:
            current_pos = event.position().toPoint()
            self._rubber_band_rect = QtCore.QRect(self._rubber_band_origin, current_pos).normalized()
            self.viewport().update()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._rubber_band_active and event.button() == Qt.MouseButton.LeftButton:
            self._rubber_band_active = False
            # Seleccionar los items dentro del rectángulo
            if self._rubber_band_rect is not None:
                # Si el área es muy pequeña, comportarse como un click normal
                min_size = 5
                if self._rubber_band_rect.width() < min_size and self._rubber_band_rect.height() < min_size:
                    self._rubber_band_rect = None
                    self.viewport().update()
                    super().mouseReleaseEvent(event)
                    return
                # Convertir a coordenadas de escena
                scene_rect = self.mapToScene(self._rubber_band_rect).boundingRect()
                for item in self.scene().items(scene_rect):
                    if isinstance(item, QGraphicsRectItem):
                        # Seleccionar si hay intersección (no hace falta contener completamente)
                        if scene_rect.intersects(item.sceneBoundingRect()):
                            item.setSelected(True)
                self._rubber_band_rect = None
                self.viewport().update()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        # Dibuja el rectángulo de selección si está activo
        if self._rubber_band_active and self._rubber_band_rect is not None:
            painter = QtGui.QPainter(self.viewport())
            color = QtGui.QColor(100, 180, 255, 60)  # Azul clarito, opacidad baja
            pen = QtGui.QPen(QtGui.QColor(100, 180, 255, 180))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(QtGui.QBrush(color))
            painter.drawRect(self._rubber_band_rect)
            painter.end()
