\
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox
)

# --- Pantalla Placeholder para Exterior ---
class ExteriorScreen(QWidget):
    def __init__(self, available_exterior_modules):
        super().__init__()
        self.available_exterior_modules = available_exterior_modules
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Centrar contenido

        title = QLabel("Configuración Exterior")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Aquí iría la lógica similar a EnvironmentSetupScreen pero para módulos exteriores
        # Por ahora, solo un botón "Crear Place"
        create_place_button = QPushButton("Crear Place")
        create_place_button.clicked.connect(self.create_place_placeholder)
        layout.addWidget(create_place_button)

        # Espacio para la lista de módulos disponibles (similar a Environment)
        self.module_list_widget = QListWidget()
        # TODO: Poblar esta lista con available_exterior_modules
        layout.addWidget(QLabel("Módulos Exteriores Disponibles:"))
        layout.addWidget(self.module_list_widget)

        layout.addStretch() # Empujar contenido hacia arriba

    def create_place_placeholder(self):
        print("Botón 'Crear Place' (Exterior) pulsado. Lógica pendiente.")
        QMessageBox.information(self, "Pendiente", "La funcionalidad 'Crear Place' aún no está implementada.")
