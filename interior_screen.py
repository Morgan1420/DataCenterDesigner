\
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox
)

# --- Pantalla Placeholder para Interior ---
class InteriorScreen(QWidget):
    def __init__(self, available_interior_modules):
        super().__init__()
        self.available_interior_modules = available_interior_modules
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Centrar contenido

        title = QLabel("Configuración Interior")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Aquí iría la lógica similar a EnvironmentSetupScreen pero para módulos interiores
        # Por ahora, solo un botón "Crear Place"
        create_place_button = QPushButton("Crear Place")
        create_place_button.clicked.connect(self.create_place_placeholder)
        layout.addWidget(create_place_button)

        # Espacio para la lista de módulos disponibles (similar a Environment)
        self.module_list_widget = QListWidget()
        # TODO: Poblar esta lista con available_interior_modules
        layout.addWidget(QLabel("Módulos Interiores Disponibles:"))
        layout.addWidget(self.module_list_widget)

        layout.addStretch() # Empujar contenido hacia arriba

    def create_place_placeholder(self):
        print("Botón 'Crear Place' (Interior) pulsado. Lógica pendiente.")
        QMessageBox.information(self, "Pendiente", "La funcionalidad 'Crear Place' aún no está implementada.")
