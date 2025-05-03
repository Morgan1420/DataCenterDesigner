# Import the necessary components from the new modules file
# Import new classes and functions
from modules import (Module, ModuleInterior, Environment,
                   HighPowerLine, LowPowerLine, _load_module_like, load_exterior_modules,
                   load_interior_modules, load_environment_variables,
                   load_high_power_lines, load_low_power_lines, WaterConnection, AccessRoad,
                   load_water_connections, load_access_roads) # Añadido WaterConnection, AccessRoad, load_water_connections, load_access_roads
import os # Keep os import if needed for path joining below


import sys
# Eliminar imports de PySide6 que ya no se usan directamente en main.py
# (Se mantienen los necesarios para QApplication, QMainWindow, QTabWidget)
from PySide6 import QtWidgets
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

# Importar las clases de pantalla desde los nuevos archivos
from environment_screen import EnvironmentSetupScreen
from screens.exterior_screen import ExteriorScreen
from screens.exterior_screen_modules import ExteriorSpace, Subspace
from interior_screen import InteriorScreen

# --- Ventana Principal con Pestañas ---
class MainWindow(QMainWindow):
    def __init__(self, env_params, hpls, lpls, wcs, ars, ext_mods, int_mods):
        super().__init__()
        self.setWindowTitle("Data Center Designer")

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Crear instancia de la pantalla de entorno y añadirla a la primera pestaña
        self.environment_screen = EnvironmentSetupScreen(env_params, hpls, lpls, wcs, ars)
        self.tab_widget.addTab(self.environment_screen, "Entorno")

        # Obtener el Environment inicial (si existe)
        env = self.environment_screen.get_active_environment()
        env_size_x = float(env.parameters.get('Space_X', 1000)) if env else 1000
        env_size_y = float(env.parameters.get('Space_Y', 500)) if env else 500
        self.exterior_space = ExteriorSpace(env_size_x, env_size_y)
        self.exterior_modules = load_exterior_modules("CSV/ExteriorModules/")
        self.exterior_screen = ExteriorScreen(self.exterior_space, self.exterior_modules, environment=env)
        self.tab_widget.addTab(self.exterior_screen, "Exterior")

        # Crear instancia de la pantalla interior y añadirla a la tercera pestaña
        self.interior_screen = InteriorScreen(int_mods)
        self.tab_widget.addTab(self.interior_screen, "Interior")

        # Conectar la señal para actualización en tiempo real
        self.environment_screen.environment_changed.connect(self.on_environment_changed)

    def on_environment_changed(self, environment):
        if environment:
            try:
                size_x = float(environment.parameters.get('Space_X', 1000))
                size_y = float(environment.parameters.get('Space_Y', 500))
                self.exterior_space.resize(size_x, size_y)
                self.exterior_screen.set_environment(environment)
            except Exception as e:
                print(f"Error actualizando exterior: {e}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # --- Carga de Datos ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_base_dir = os.path.join(script_dir, 'CSV') # Directorio base CSV

    # Cargar Módulos de Entorno
    env_modules_dir = os.path.join(csv_base_dir, 'EnvironmentModules')
    env_param_file_path = os.path.join(env_modules_dir, 'Environment.csv')
    environment_params = load_environment_variables(env_param_file_path)
    hpl_file_path = os.path.join(env_modules_dir, 'High_Power_Lines.csv')
    high_power_lines = load_high_power_lines(hpl_file_path)
    lpl_file_path = os.path.join(env_modules_dir, 'Low_Power_Lines.csv')
    low_power_lines = load_low_power_lines(lpl_file_path)
    wc_file_path = os.path.join(env_modules_dir, 'Water_connection.csv')
    water_connections = load_water_connections(wc_file_path)
    ar_file_path_typo = os.path.join(env_modules_dir, 'Acess_Roads.csv') # Mantener la comprobación del typo
    ar_file_path_correct = os.path.join(env_modules_dir, 'Access_Roads.csv')
    ar_file_path = ar_file_path_correct if os.path.exists(ar_file_path_correct) else ar_file_path_typo
    access_roads = load_access_roads(ar_file_path)
    if not os.path.exists(ar_file_path):
         print(f"Advertencia: No se encontró el archivo de carreteras de acceso en {ar_file_path_correct} ni en {ar_file_path_typo}")

    # Cargar Módulos Exteriores
    exterior_modules_dir = os.path.join(csv_base_dir, 'ExteriorModules')
    exterior_modules = []
    if os.path.exists(exterior_modules_dir):
        for filename in os.listdir(exterior_modules_dir):
            if filename.endswith(".csv"):
                file_path = os.path.join(exterior_modules_dir, filename)
                # Usar _load_module_like con ExteriorSpace
                mods_from_file = _load_module_like(file_path, ExteriorSpace, "ExteriorSpace")
                exterior_modules.extend(mods_from_file)
    else:
        print(f"Advertencia: Directorio de módulos exteriores no encontrado en {exterior_modules_dir}")


    # Cargar Módulos Interiores
    interior_modules_dir = os.path.join(csv_base_dir, 'InteriorModules')
    interior_modules = []
    if os.path.exists(interior_modules_dir):
        for filename in os.listdir(interior_modules_dir):
            if filename.endswith(".csv"):
                file_path = os.path.join(interior_modules_dir, filename)
                # Usar _load_module_like con ModuleInterior
                mods_from_file = _load_module_like(file_path, ModuleInterior, "ModuleInterior")
                interior_modules.extend(mods_from_file)
    else:
         print(f"Advertencia: Directorio de módulos interiores no encontrado en {interior_modules_dir}")


    # --- Mostrar Advertencias ---
    if not environment_params and os.path.exists(env_param_file_path):
         # ... (código de advertencia existente) ...
         # Podríamos añadir un mensaje si el archivo existe pero está vacío o mal formateado
         print(f"Advertencia: No se cargaron parámetros de entorno desde {env_param_file_path}. ¿Está vacío o mal formateado?")
         pass # Mantener pass si no hay acción específica
    elif not os.path.exists(env_param_file_path):
         print(f"Advertencia: No se encontró el archivo de parámetros de entorno en {env_param_file_path}")

    # --- Crear y Mostrar Ventana Principal ---
    # Pasar todos los datos cargados a la ventana principal
    main_window = MainWindow(
        environment_params,
        high_power_lines,
        low_power_lines,
        water_connections,
        access_roads,
        exterior_modules,
        interior_modules
    )
    main_window.showMaximized()
    main_window.show()

    sys.exit(app.exec())

