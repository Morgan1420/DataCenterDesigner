\
import sys
import random
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QBrush, QColor, QPainter
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
    QScrollArea, QFormLayout, QLineEdit, QSplitter, QGroupBox, QMessageBox,
    QDoubleSpinBox
)
# Importar clases base necesarias de modules
from modules import Module, Environment

# --- Pantalla de Configuración del Entorno ---
class EnvironmentSetupScreen(QWidget):
    # Modificar constructor para aceptar todos los tipos de módulos de entorno
    def __init__(self, available_envs, available_hpls, available_lpls, available_wcs, available_ars):
        super().__init__()
        # Almacenar todas las listas de objetos disponibles
        self.available_items = {
            "Environment": available_envs,
            "HighPowerLine": available_hpls,
            "LowPowerLine": available_lpls,
            "WaterConnection": available_wcs,
            "AccessRoad": available_ars
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
        left_layout.setContentsMargins(5, 5, 5, 5)

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
        self.view = QGraphicsView(self.scene)
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
        # Limpiar detalles al inicio
        self.clear_details()

    def populate_available_items(self):
        self.item_list_widget.clear()
        for item_type, item_list in self.available_items.items():
            if not item_list:
                continue

            header_item = QListWidgetItem(f"--- {item_type} ---")
            header_item.setFlags(Qt.ItemFlag.NoItemFlags) # Usar Qt.ItemFlag
            header_item.setForeground(Qt.GlobalColor.gray) # Usar Qt.GlobalColor
            self.item_list_widget.addItem(header_item)

            for item_obj in item_list:
                item_widget = QWidget()
                item_layout = QHBoxLayout(item_widget)
                item_layout.setContentsMargins(0, 0, 0, 0)
                item_layout.setSpacing(5)

                label = QLabel(item_obj.id)
                label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
                add_button = QPushButton("+")
                add_button.setFixedSize(25, 25)
                add_button.setToolTip(f"Añadir '{item_obj.id}' ({item_type}) al mapa")
                add_button.clicked.connect(lambda checked=False, obj=item_obj, type_str=item_type: self.add_item_to_map(obj, type_str))

                item_layout.addWidget(label)
                item_layout.addWidget(add_button)

                list_item = QListWidgetItem(self.item_list_widget)
                list_item.setSizeHint(item_widget.sizeHint())
                self.item_list_widget.addItem(list_item)
                self.item_list_widget.setItemWidget(list_item, item_widget)

    def add_item_to_map(self, item_object, item_type_str):
        unique_map_id = f"{item_type_str}_{item_object.id}_{self.map_item_counter}"
        self.map_item_counter += 1

        print(f"Añadiendo '{item_object.id}' ({item_type_str}) al mapa con ID único: {unique_map_id}")
        self.active_items_on_map[unique_map_id] = (item_object, item_type_str)

        # --- Determinar tamaño del bloque ---
        min_size = 30 # Tamaño mínimo visual
        default_size_x = 60
        default_size_y = 40
        item_width = default_size_x
        item_height = default_size_y

        if isinstance(item_object, Module):
            # Intentar obtener Space_X y Space_Y de los inputs
            try:
                # Usar .get con valor por defecto 0 si no existe la clave
                space_x = float(item_object.inputs.get('Space_X', default_size_x))
                space_y = float(item_object.inputs.get('Space_Y', default_size_y))
                # Aplicar tamaño mínimo y quizás un máximo o escalado si es necesario
                item_width = max(min_size, space_x)
                item_height = max(min_size, space_y)
                # print(f"  Usando Space_X={space_x}, Space_Y={space_y} -> Tamaño visual: {item_width}x{item_height}")
            except (ValueError, TypeError, AttributeError):
                # Si falla la conversión o no hay 'inputs', usar tamaño por defecto
                print(f"  Advertencia: No se pudo obtener Space_X/Y numérico para {item_object.id}. Usando tamaño por defecto.")
                item_width = default_size_x
                item_height = default_size_y
        elif isinstance(item_object, Environment):
             # Los Environment no tienen Space_X/Y, usar tamaño por defecto
             item_width = default_size_x
             item_height = default_size_y

        # --- Crear representación gráfica ---
        color = QtGui.QColor(200, 200, 200) # Gris por defecto
        # ... (código existente para asignar color basado en tipo) ...
        if item_type_str == "Environment":
            color = QtGui.QColor(180, 220, 180) # Verde claro
        elif "PowerLine" in item_type_str:
            color = QtGui.QColor(255, 200, 150) # Naranja claro
        elif "WaterConnection" in item_type_str:
            color = QtGui.QColor(150, 200, 255) # Azul claro
        elif "AccessRoad" in item_type_str:
            color = QtGui.QColor(220, 220, 220) # Gris más claro


        x = random.randint(10, int(self.scene.width()) - int(item_width) - 10)
        y = random.randint(10, int(self.scene.height()) - int(item_height) - 10)

        rect_item = QGraphicsRectItem(x, y, item_width, item_height)
        rect_item.setBrush(color)
        rect_item.setPen(QPen(Qt.GlobalColor.black)) # Borde negro
        rect_item.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        rect_item.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        rect_item.setToolTip(f"{item_type_str}: {item_object.id}")
        rect_item.unique_map_id = unique_map_id

        # --- Añadir texto centrado ---
        text_item = QGraphicsTextItem(item_object.id, rect_item) # Padre es rect_item
        text_item.setDefaultTextColor(Qt.GlobalColor.black)
        # Centrar texto dentro del rectángulo
        text_rect = text_item.boundingRect()
        text_x = x + (item_width - text_rect.width()) / 2
        text_y = y + (item_height - text_rect.height()) / 2
        text_item.setPos(text_x, text_y)
        # Asegurarse que el texto no sea seleccionable/movible independientemente
        text_item.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        text_item.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)


        self.scene.addItem(rect_item)
        rect_item.setSelected(True)
        # No es necesario llamar a display_item_details aquí, on_map_item_selected lo hará

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
                item_object.parameters[key] = new_value # Asume que el valor ya es del tipo correcto (str)
                self.update_map_tooltip(unique_map_id, item_object) # Actualizar tooltip
            elif param_type == "input" and isinstance(item_object, Module):
                print(f"Actualizando Input {item_object.id}: {key} = {new_value}")
                # Intentar convertir a float si es numérico, si no, mantener como está (str o float)
                try:
                    current_value = item_object.inputs.get(key)
                    if isinstance(current_value, (int, float)) or isinstance(new_value, float):
                         item_object.inputs[key] = float(new_value)
                    else: # Mantener como string si el original no era numérico y el nuevo tampoco es float
                         item_object.inputs[key] = new_value
                except ValueError:
                     item_object.inputs[key] = new_value # Guardar como texto si falla la conversión
                # Si el parámetro modificado es Space_X o Space_Y, redimensionar el item en el mapa
                if key in ['Space_X', 'Space_Y']:
                    self.resize_map_item(unique_map_id, item_object)
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
                    params_str = '\\n'.join([f'  {k}: {v}' for k, v in item_object.parameters.items()])
                    tooltip_text += f"\\nParámetros:\\n{params_str}"
                elif isinstance(item_object, Module):
                    inputs_str = '\\n'.join([f'  {k}: {v}' for k, v in item_object.inputs.items()])
                    outputs_str = '\\n'.join([f'  {k}: {v}' for k, v in item_object.outputs.items()])
                    if inputs_str: tooltip_text += f"\\nInputs:\\n{inputs_str}"
                    if outputs_str: tooltip_text += f"\\nOutputs:\\n{outputs_str}"
                item.setToolTip(tooltip_text)
                break

    def resize_map_item(self, unique_map_id, item_object):
        """Redimensiona un item en el mapa basado en Space_X y Space_Y."""
        for item in self.scene.items():
             # Buscar el rectángulo principal
            if isinstance(item, QGraphicsRectItem) and hasattr(item, 'unique_map_id') and item.unique_map_id == unique_map_id:
                rect_item = item
                min_size = 30
                default_size_x = 60
                default_size_y = 40
                new_width = default_size_x
                new_height = default_size_y

                try:
                    space_x = float(item_object.inputs.get('Space_X', default_size_x))
                    space_y = float(item_object.inputs.get('Space_Y', default_size_y))
                    new_width = max(min_size, space_x)
                    new_height = max(min_size, space_y)
                except (ValueError, TypeError):
                    pass # Mantener tamaño por defecto si hay error

                current_rect = rect_item.rect()
                # Mantener la posición superior izquierda (x, y)
                rect_item.setRect(current_rect.x(), current_rect.y(), new_width, new_height)

                # Reposicionar el texto hijo
                text_item = None
                for child in rect_item.childItems():
                    if isinstance(child, QGraphicsTextItem):
                        text_item = child
                        break
                if text_item:
                    text_rect = text_item.boundingRect()
                    # Usar la nueva posición x, y del rectángulo padre
                    text_x = current_rect.x() + (new_width - text_rect.width()) / 2
                    text_y = current_rect.y() + (new_height - text_rect.height()) / 2
                    text_item.setPos(text_x, text_y)

                print(f"Item {item_object.id} redimensionado a {new_width}x{new_height}")
                self.scene.update() # Forzar redibujo si es necesario
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
