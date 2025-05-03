import pandas as pd
import os

# --- Module Classes ---
class Module:
    def __init__(self, id, inputs, outputs):
        self.id = id
        self.inputs = inputs  # Dictionary {Unit: Amount}
        self.outputs = outputs # Dictionary {Unit: Amount}

    def __repr__(self):
        # Provides a readable representation of the object
        return f"Module(id='{self.id}', inputs={self.inputs}, outputs={self.outputs})"

class ModuleExterior(Module):
    def __init__(self, id, inputs, outputs):
        super().__init__(id, inputs, outputs)
        # Extract common attributes like Space_X, Space_Y, Price from inputs for easier access
        # Uses .get() to avoid errors if the key doesn't exist
        self.space_x = inputs.get('Space_X')
        self.space_y = inputs.get('Space_Y')
        self.price = inputs.get('Price')

    def __repr__(self):
        # Customize representation for ModuleExterior
        base_repr = super().__repr__().replace("Module(", "ModuleExterior(", 1)
        # Adds specific attributes to the representation
        return f"{base_repr[:-1]}, space_x={self.space_x}, space_y={self.space_y}, price={self.price})"

# --- New Interior Module Class ---
class ModuleInterior(Module):
    def __init__(self, id, inputs, outputs):
        super().__init__(id, inputs, outputs)
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
    def __init__(self, id, inputs, outputs):
        super().__init__(id, inputs, outputs)
        # Add specific attributes if needed

    def __repr__(self):
        return super().__repr__().replace("Module(", "HighPowerLine(", 1)

class LowPowerLine(Module):
    def __init__(self, id, inputs, outputs):
        super().__init__(id, inputs, outputs)
        # Add specific attributes if needed

    def __repr__(self):
        return super().__repr__().replace("Module(", "LowPowerLine(", 1)

# --- New Environment Module Classes ---
class WaterConnection(Module):
    def __init__(self, id, inputs, outputs):
        super().__init__(id, inputs, outputs)

    def __repr__(self):
        return super().__repr__().replace("Module(", "WaterConnection(", 1)

class AccessRoad(Module):
    def __init__(self, id, inputs, outputs):
        super().__init__(id, inputs, outputs)

    def __repr__(self):
        return super().__repr__().replace("Module(", "AccessRoad(", 1)

# --- Function to load modules ---
def load_exterior_modules(file_path):
    modules = []
    try:
        # Reads the Excel file
        # Note: Changed to read CSV as per user's file structure. Assumes first column is index.
        # If the CSV doesn't have sheet-like separation, this logic needs adjustment.
        # Assuming the CSV 'ModulsExterior.csv' contains all modules and needs a way to group them.
        # For now, treating the whole CSV as one 'sheet' or module source.
        # This part might need refinement based on the actual CSV structure.
        # If 'ModulsExterior.csv' represents *one* module type, the logic is simpler.
        # If it contains *multiple* modules identified by a column, pandas groupby is needed.

        # Let's assume ModulsExterior.csv contains data for *multiple* modules,
        # and there's a column identifying the module (e.g., 'Module_ID').
        # If not, this needs to be adapted. For now, reading the whole CSV.

        # Check if the file exists before attempting to read
        if not os.path.exists(file_path):
             print(f"Error: File not found at {file_path}")
             return modules # Return empty list if file not found

        # Read the CSV file
        df = pd.read_csv(file_path) # Assuming standard CSV format

        # --- Adaptation needed based on actual CSV structure ---
        # Example: If CSV has a 'Module_ID' column to group rows by module
        if 'Module_ID' in df.columns:
             grouped = df.groupby('Module_ID')
             for module_id, group_df in grouped:
                 inputs = {}
                 outputs = {}
                 required_cols = ['Is_Input', 'Is_Output', 'Unit', 'Amount']
                 if not all(col in group_df.columns for col in required_cols):
                      print(f"Warning: Module '{module_id}' in {file_path} is missing required columns ({required_cols}). Skipping.")
                      continue

                 for _, row in group_df.iterrows():
                     unit = row['Unit']
                     amount = row['Amount']
                     is_input = row['Is_Input']
                     is_output = row['Is_Output']

                     try:
                         if pd.notna(is_input) and int(is_input) == 1:
                              inputs[unit] = amount
                     except (ValueError, TypeError):
                          print(f"Warning: Invalid value in 'Is_Input' for unit '{unit}' in module '{module_id}'. Skipping input.")

                     try:
                         if pd.notna(is_output) and int(is_output) == 1:
                             outputs[unit] = amount
                     except (ValueError, TypeError):
                          print(f"Warning: Invalid value in 'Is_Output' for unit '{unit}' in module '{module_id}'. Skipping output.")

                 if inputs or outputs:
                      module = ModuleExterior(id=module_id, inputs=inputs, outputs=outputs)
                      modules.append(module)
                 else:
                      print(f"Warning: No valid input or output data found for module '{module_id}'. Skipping module creation.")

        else:
             # If no 'Module_ID', treat the whole CSV as one module source (e.g., file name is ID)
             # This might not be the intended behavior based on the 'sheets' description.
             print(f"Warning: 'Module_ID' column not found in {file_path}. Treating entire file as one source. Adapt if needed.")
             # Example: Use filename as ID (without extension)
             module_id = os.path.splitext(os.path.basename(file_path))[0]
             inputs = {}
             outputs = {}
             required_cols = ['Is_Input', 'Is_Output', 'Unit', 'Amount']
             if not all(col in df.columns for col in required_cols):
                 print(f"Warning: File {file_path} is missing required columns ({required_cols}). Skipping.")
             else:
                 for _, row in df.iterrows():
                     unit = row['Unit']
                     amount = row['Amount']
                     is_input = row['Is_Input']
                     is_output = row['Is_Output']
                     try:
                         if pd.notna(is_input) and int(is_input) == 1: inputs[unit] = amount
                     except (ValueError, TypeError): pass # Simplified error handling for brevity
                     try:
                         if pd.notna(is_output) and int(is_output) == 1: outputs[unit] = amount
                     except (ValueError, TypeError): pass

                 if inputs or outputs:
                     module = ModuleExterior(id=module_id, inputs=inputs, outputs=outputs)
                     modules.append(module)
                 else:
                     print(f"Warning: No valid input or output data found in file '{file_path}'.")


    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except pd.errors.EmptyDataError:
        print(f"Error: File {file_path} is empty.")
    except Exception as e:
        print(f"Error reading or processing file {file_path}: {e}")
    return modules

# --- Function to load interior modules ---
def load_interior_modules(file_path):
    modules = []
    try:
        if not os.path.exists(file_path):
             print(f"Error: File not found at {file_path}")
             return modules

        df = pd.read_csv(file_path)

        if 'Module_ID' in df.columns:
             grouped = df.groupby('Module_ID')
             for module_id, group_df in grouped:
                 inputs = {}
                 outputs = {}
                 required_cols = ['Is_Input', 'Is_Output', 'Unit', 'Amount']
                 if not all(col in group_df.columns for col in required_cols):
                      print(f"Warning: Interior Module '{module_id}' in {file_path} is missing required columns ({required_cols}). Skipping.")
                      continue

                 for _, row in group_df.iterrows():
                     unit = row['Unit']
                     amount = row['Amount']
                     is_input = row['Is_Input']
                     is_output = row['Is_Output']

                     try:
                         if pd.notna(is_input) and int(is_input) == 1:
                              inputs[unit] = amount
                     except (ValueError, TypeError):
                          print(f"Warning: Invalid value in 'Is_Input' for unit '{unit}' in interior module '{module_id}'. Skipping input.")

                     try:
                         if pd.notna(is_output) and int(is_output) == 1:
                             outputs[unit] = amount
                     except (ValueError, TypeError):
                          print(f"Warning: Invalid value in 'Is_Output' for unit '{unit}' in interior module '{module_id}'. Skipping output.")

                 if inputs or outputs:
                      # Create ModuleInterior instance
                      module = ModuleInterior(id=module_id, inputs=inputs, outputs=outputs)
                      modules.append(module)
                 else:
                      print(f"Warning: No valid input or output data found for interior module '{module_id}'. Skipping module creation.")

        else:
             print(f"Warning: 'Module_ID' column not found in {file_path}. Treating entire file as one source for interior modules. Adapt if needed.")
             module_id = os.path.splitext(os.path.basename(file_path))[0]
             inputs = {}
             outputs = {}
             required_cols = ['Is_Input', 'Is_Output', 'Unit', 'Amount']
             if not all(col in df.columns for col in required_cols):
                 print(f"Warning: File {file_path} (interior) is missing required columns ({required_cols}). Skipping.")
             else:
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
                     module = ModuleInterior(id=module_id, inputs=inputs, outputs=outputs)
                     modules.append(module)
                 else:
                     print(f"Warning: No valid input or output data found in file '{file_path}' (interior).")


    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except pd.errors.EmptyDataError:
        print(f"Error: File {file_path} is empty.")
    except Exception as e:
        print(f"Error reading or processing file {file_path}: {e}")
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
            # print(f"Info: {class_name_str} file not found at {file_path}")
            return modules

        df = pd.read_csv(file_path)
        required_cols = ['Is_Input', 'Is_Output', 'Unit', 'Amount']

        # Assuming optional 'Module_ID' column, otherwise use filename
        if 'Module_ID' in df.columns:
            grouped = df.groupby('Module_ID')
            for module_id, group_df in grouped:
                if not all(col in group_df.columns for col in required_cols):
                    print(f"Warning: {class_name_str} '{module_id}' in {file_path} is missing required columns ({required_cols}). Skipping.")
                    continue
                inputs = {}
                outputs = {}
                for _, row in group_df.iterrows():
                    unit = row['Unit']
                    amount = row['Amount']
                    is_input = row['Is_Input']
                    is_output = row['Is_Output']
                    try:
                        if pd.notna(is_input) and int(is_input) == 1: inputs[unit] = amount
                    except (ValueError, TypeError): pass # Simplified
                    try:
                        if pd.notna(is_output) and int(is_output) == 1: outputs[unit] = amount
                    except (ValueError, TypeError): pass # Simplified

                if inputs or outputs:
                    module = module_class(id=module_id, inputs=inputs, outputs=outputs)
                    modules.append(module)
                else:
                     print(f"Warning: No valid I/O data for {class_name_str} '{module_id}'.")
        else:
            # print(f"Warning: 'Module_ID' column not found in {file_path}. Treating file as one {class_name_str}.")
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
                    module = module_class(id=module_id, inputs=inputs, outputs=outputs)
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
