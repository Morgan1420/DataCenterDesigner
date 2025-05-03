import pandas as pd
import os

# --- Module Classes ---
class Module:
    def __init__(self, id, inputs, outputs, size_x, size_y):
        self.id = id
        self.inputs = inputs  # Dictionary {Unit: Amount}
        self.outputs = outputs  # Dictionary {Unit: Amount}
        self.size_x = size_x  # Width of the module
        self.size_y = size_y  # Height of the module
        self.x = 0.0  # Position x
        self.y = 0.0  # Position y

    def set_position(self, x: float, y: float):
        """Sets the position of the module."""
        self.x = x
        self.y = y

    def get_position(self) -> tuple[float, float]:
        """Returns the position of the module as a tuple (x, y)."""
        return self.x, self.y

    def __repr__(self):
        """Provides a readable representation of the module."""
        return (f"Module(id='{self.id}', inputs={self.inputs}, outputs={self.outputs}, "
                f"size_x={self.size_x}, size_y={self.size_y}, x={self.x}, y={self.y})")

# --- New Interior Module Class ---
class ModuleInterior(Module):
    def __init__(self, id, inputs, outputs, size_x, size_y):
        super().__init__(id, inputs, outputs, size_x, size_y)
        # Add specific attributes for Interior modules if needed, similar to ModuleExterior
        # For now, it just inherits from Module
        pass # Placeholder if no specific attributes are needed immediately

    def __repr__(self):
        # Customize representation for ModuleInterior
        return super().__repr__().replace("Module(", "ModuleInterior(", 1)

# --- Environment Class ---
class Environment:
    def __init__(self, id, parameters):
        self.id = id
        self.parameters = parameters # Dictionary {Parameter: Value}

    def __repr__(self):
        return f"Environment(id='{self.id}', parameters={self.parameters})"

# --- Power Line Classes (Inheriting from Module) ---
class HighPowerLine(Module):
    def __init__(self, id, inputs, outputs, size_x, size_y):
        super().__init__(id, inputs, outputs, size_x, size_y)
        # Add specific attributes if needed

    def __repr__(self):
        return super().__repr__().replace("Module(", "HighPowerLine(", 1)

class LowPowerLine(Module):
    def __init__(self, id, inputs, outputs, size_x, size_y):
        super().__init__(id, inputs, outputs, size_x, size_y)
        # Add specific attributes if needed

    def __repr__(self):
        return super().__repr__().replace("Module(", "LowPowerLine(", 1)

# --- New Environment Module Classes ---
class WaterConnection(Module):
    def __init__(self, id, inputs, outputs, size_x, size_y):
        super().__init__(id, inputs, outputs, size_x, size_y)

    def __repr__(self):
        return super().__repr__().replace("Module(", "WaterConnection(", 1)

class AccessRoad(Module):
    def __init__(self, id, inputs, outputs, size_x, size_y):
        super().__init__(id, inputs, outputs, size_x, size_y)

    def __repr__(self):
        return super().__repr__().replace("Module(", "AccessRoad(", 1)

# --- Function to load modules ---
def load_exterior_modules(directory_path):
    modules = []
    try:
        if not os.path.exists(directory_path):
            print(f"Error: Directory not found at {directory_path}")
            return modules

        for filename in os.listdir(directory_path):
            if filename.endswith(".csv"):
                file_path = os.path.join(directory_path, filename)
                module_id = os.path.splitext(os.path.basename(file_path))[0]
                inputs = {}
                outputs = {}
                try:
                    df = pd.read_csv(file_path)
                    required_cols = ['Is_Input', 'Is_Output', 'Unit', 'Amount']
                    if not all(col in df.columns for col in required_cols):
                        print(f"Warning: File {file_path} is missing required columns ({required_cols}). Skipping.")
                        continue

                    for _, row in df.iterrows():
                        unit = row['Unit']
                        amount = row['Amount']
                        is_input = row['Is_Input']
                        is_output = row['Is_Output']
                        try:
                            if pd.notna(is_input) and int(is_input) == 1: inputs[unit] = amount
                        except (ValueError, TypeError): pass
                        try:
                            if pd.notna(is_output) and int(is_output) == 1: outputs[unit] = amount
                        except (ValueError, TypeError): pass

                    if inputs or outputs:
                        # Assuming Module class is appropriate here, adjust if a specific ExteriorModule class exists
                        module = Module(id=module_id, inputs=inputs, outputs=outputs, size_x=0.0, size_y=0.0)
                        modules.append(module)
                    else:
                        print(f"Warning: No valid input or output data found in file '{file_path}'.")

                except pd.errors.EmptyDataError:
                    print(f"Error: File {file_path} is empty.")
                except Exception as e:
                    print(f"Error reading or processing file {file_path}: {e}")

    except Exception as e:
        print(f"Error accessing directory {directory_path}: {e}")
    return modules

# --- Function to load interior modules ---
def load_interior_modules(directory_path): # Changed parameter to directory_path
    modules = []
    try:
        if not os.path.exists(directory_path):
             print(f"Error: Directory not found at {directory_path}")
             return modules

        for filename in os.listdir(directory_path):
            if filename.endswith(".csv"):
                file_path = os.path.join(directory_path, filename)
                module_id = os.path.splitext(os.path.basename(file_path))[0]
                inputs = {}
                outputs = {}
                try:
                    df = pd.read_csv(file_path)
                    required_cols = ['Is_Input', 'Is_Output', 'Unit', 'Amount']
                    if not all(col in df.columns for col in required_cols):
                        print(f"Warning: File {file_path} (interior) is missing required columns ({required_cols}). Skipping.")
                        continue

                    for _, row in df.iterrows():
                        unit = row['Unit']
                        amount = row['Amount']
                        is_input = row['Is_Input']
                        is_output = row['Is_Output']
                        try:
                            if pd.notna(is_input) and int(is_input) == 1: inputs[unit] = amount
                        except (ValueError, TypeError): pass
                        try:
                            if pd.notna(is_output) and int(is_output) == 1: outputs[unit] = amount
                        except (ValueError, TypeError): pass

                    if inputs or outputs:
                        # Create ModuleInterior instance
                        module = ModuleInterior(id=module_id, inputs=inputs, outputs=outputs, size_x=0.0, size_y=0.0)
                        modules.append(module)
                    else:
                        print(f"Warning: No valid input or output data found in file '{file_path}' (interior).")

                except pd.errors.EmptyDataError:
                    print(f"Error: File {file_path} (interior) is empty.")
                except Exception as e:
                    print(f"Error reading or processing file {file_path} (interior): {e}")

    except Exception as e:
        print(f"Error accessing directory {directory_path}: {e}")
    return modules

# --- Function to load environment variables ---
def load_environment_variables(file_path):
    environments = []
    try:
        if not os.path.exists(file_path):
            print(f"Warning: Environment file not found at {file_path}")
            return environments

        df = pd.read_csv(file_path)
        # Assuming columns 'Parameter' and 'Value' and optionally 'Environment_ID'
        required_cols = ['Unit', 'Amount'] # Adjust if column names are different

        if 'Environment_ID' in df.columns:
            grouped = df.groupby('Environment_ID')
            for env_id, group_df in grouped:
                if not all(col in group_df.columns for col in required_cols):
                    print(f"Warning: Environment '{env_id}' in {file_path} is missing required columns ({required_cols}). Skipping.")
                    continue
                parameters = {}
                for _, row in group_df.iterrows():
                    # Handle potential missing values gracefully
                    param = row.get('Unit')
                    value = row.get('Amount')
                    if pd.notna(param):
                         parameters[param] = value # Store value even if it's NaN/None
                    else:
                         print(f"Warning: Missing 'Parameter' in row for Environment '{env_id}'. Skipping row.")

                if parameters:
                    env = Environment(id=env_id, parameters=parameters)
                    environments.append(env)
                else:
                    print(f"Warning: No valid parameters found for environment '{env_id}'.")

        else: # Treat entire file as one environment object
            print(f"Warning: 'Environment_ID' column not found in {file_path}. Treating entire file as one environment object.")
            if not all(col in df.columns for col in required_cols):
                 print(f"Warning: File {file_path} is missing required columns ({required_cols}). Skipping.")
            else:
                env_id = os.path.splitext(os.path.basename(file_path))[0]
                parameters = {}
                for _, row in df.iterrows():
                    param = row.get('Unit')
                    value = row.get('Amount')
                    if pd.notna(param):
                        parameters[param] = value
                    else:
                        print(f"Warning: Missing 'Parameter' in row for Environment '{env_id}'. Skipping row.")

                if parameters:
                    env = Environment(id=env_id, parameters=parameters)
                    environments.append(env)
                else:
                     print(f"Warning: No valid parameters found in file '{file_path}'.")

    except FileNotFoundError: # Should be caught by os.path.exists, but good practice
        print(f"Error: File not found at {file_path}")
    except pd.errors.EmptyDataError:
        print(f"Error: File {file_path} is empty.")
    except Exception as e:
        print(f"Error reading or processing environment file {file_path}: {e}")
    return environments

# --- Generic function to load Module-like classes (High/Low Power Lines) ---
def _load_module_like(file_path, module_class, class_name_str):
    modules = []
    try:
        if not os.path.exists(file_path):
            # Don't print error if file simply doesn't exist for optional types
            return modules

        df = pd.read_csv(file_path)
        required_cols = ['Is_Input', 'Is_Output', 'Unit', 'Amount']

        # Always use filename as the module ID, remove Module_ID column check
        module_id = os.path.splitext(os.path.basename(file_path))[0]
        if not all(col in df.columns for col in required_cols):
            print(f"Warning: File {file_path} ({class_name_str}) is missing required columns ({required_cols}). Skipping.")
        else:
            inputs = {}
            outputs = {}
            for _, row in df.iterrows():
                unit = row['Unit']
                amount = row['Amount']
                is_input = row['Is_Input']
                is_output = row['Is_Output']
                try:
                    if pd.notna(is_input) and int(is_input) == 1: inputs[unit] = amount
                except (ValueError, TypeError): pass
                try:
                    if pd.notna(is_output) and int(is_output) == 1: outputs[unit] = amount
                except (ValueError, TypeError): pass

            if inputs or outputs:
                module = module_class(id=module_id, inputs=inputs, outputs=outputs, size_x=0.0, size_y=0.0)
                modules.append(module)
            else:
                print(f"Warning: No valid I/O data in file '{file_path}' ({class_name_str}).")

    except pd.errors.EmptyDataError:
        print(f"Error: File {file_path} ({class_name_str}) is empty.")
    except Exception as e:
        print(f"Error reading or processing {class_name_str} file {file_path}: {e}")
    return modules

# --- Functions to load power lines ---
def load_high_power_lines(file_path):
    return _load_module_like(file_path, HighPowerLine, "HighPowerLine")

def load_low_power_lines(file_path):
    return _load_module_like(file_path, LowPowerLine, "LowPowerLine")

# --- Functions to load other environment modules ---
def load_water_connections(file_path):
    return _load_module_like(file_path, WaterConnection, "WaterConnection")

def load_access_roads(file_path):
    return _load_module_like(file_path, AccessRoad, "AccessRoad")
