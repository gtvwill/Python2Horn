import os
import pandas as pd
import numpy as np
from stl import mesh

# Define the paths to the CSV and 3D folders
csv_folder = os.path.join(os.getcwd(), 'csv')
stl_folder = os.path.join(os.getcwd(), '3d')

# Ensure the 3D folder exists
os.makedirs(stl_folder, exist_ok=True)

# List all CSV files in the folder
csv_files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]

# Check if there are any CSV files
if not csv_files:
    print("No CSV files found in the 'csv' folder.")
    exit()

# Print available CSV files for selection
print("Please Select your Horn to export:")
for i, file in enumerate(csv_files, start=1):
    print(f"{i}. {file}")

# Get user input for file selection
selection = input(">> ")
while not selection.isdigit() or not (1 <= int(selection) <= len(csv_files)):
    print("Invalid selection. Please enter a number corresponding to the CSV file.")
    selection = input(">> ")
selection = int(selection) - 1

# Load the selected CSV file
selected_csv_file = os.path.join(csv_folder, csv_files[selection])
data = pd.read_csv(selected_csv_file)

# Get the base name of the CSV file (without the extension)
filename = os.path.splitext(csv_files[selection])[0]

# Path for saving the STL file
stl_file_path = os.path.join(stl_folder, f"{filename}.stl")

# Identify column names
print("\nColumns found in the CSV file:")
print(data.columns.tolist())

# Expected column names (modify these to match your CSV)
expected_columns = {
    'length': None,
    'height_half': None,
    'width_half': None
}

# Attempt to map expected columns to actual columns
for col in data.columns:
    col_lower = col.lower().strip()
    if 'length' in col_lower:
        expected_columns['length'] = col
    elif 'height' in col_lower and '/2' in col_lower:
        expected_columns['height_half'] = col
    elif 'width' in col_lower and '/2' in col_lower:
        expected_columns['width_half'] = col

# Check if all expected columns are found
if None in expected_columns.values():
    print("\nError: The script could not find the necessary columns in the CSV file.")
    print("Please ensure the CSV file contains columns for Length (cm), Height/2 (cm), and Width/2 (cm).")
    exit()

# Extract and convert columns to numeric values
try:
    data_length = pd.to_numeric(data[expected_columns['length']], errors='coerce')
    data_height_half = pd.to_numeric(data[expected_columns['height_half']], errors='coerce')
    data_width_half = pd.to_numeric(data[expected_columns['width_half']], errors='coerce')
except KeyError as e:
    print(f"\nError: Missing expected column in the CSV file: {e}")
    exit()

# Check for NaN values and drop them
if data_length.isnull().any() or data_height_half.isnull().any() or data_width_half.isnull().any():
    print("\nWarning: Some rows contain non-numeric values and will be skipped.")
    valid_rows = ~(data_length.isnull() | data_height_half.isnull() | data_width_half.isnull())
    data_length = data_length[valid_rows].reset_index(drop=True)
    data_height_half = data_height_half[valid_rows].reset_index(drop=True)
    data_width_half = data_width_half[valid_rows].reset_index(drop=True)

# Function to create a vertex from the CSV data
def create_vertex(length, height_half, width_half):
    return np.array([
        [length * 10,  width_half * 10,  height_half * 10],  # Top right
        [length * 10, -width_half * 10,  height_half * 10],  # Top left
        [length * 10, -width_half * 10, -height_half * 10],  # Bottom left
        [length * 10,  width_half * 10, -height_half * 10]   # Bottom right
    ])

# Prepare vertices and faces
vertices = []
faces = []

num_steps = len(data_length)
for i in range(num_steps - 1):
    length1 = data_length[i]
    length2 = data_length[i + 1]

    height_half1 = data_height_half[i]
    height_half2 = data_height_half[i + 1]

    width_half1 = data_width_half[i]
    width_half2 = data_width_half[i + 1]

    print(f"\nProcessing step {i+1}/{num_steps - 1}")
    print(f"Length1: {length1} cm, Length2: {length2} cm")
    print(f"Height1/2: {height_half1} cm, Height2/2: {height_half2} cm")
    print(f"Width1/2: {width_half1} cm, Width2/2: {width_half2} cm")

    vertices1 = create_vertex(length1, height_half1, width_half1)
    vertices2 = create_vertex(length2, height_half2, width_half2)

    # Add vertices to the list
    vertices.extend(vertices1)
    vertices.extend(vertices2)

    print(f"Vertices1:\n{vertices1}")
    print(f"Vertices2:\n{vertices2}")

    # Calculate offset
    offset = i * 8

    # Define faces between the two cross-sections
    faces.extend([
        [offset,     offset + 1, offset + 5],
        [offset,     offset + 5, offset + 4],
        [offset + 1, offset + 2, offset + 6],
        [offset + 1, offset + 6, offset + 5],
        [offset + 2, offset + 3, offset + 7],
        [offset + 2, offset + 7, offset + 6],
        [offset + 3, offset,     offset + 4],
        [offset + 3, offset + 4, offset + 7]
    ])

# Convert lists to numpy arrays
vertices = np.array(vertices).reshape(-1, 3)
faces = np.array(faces)

# Create mesh
horn_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
for i, face in enumerate(faces):
    for j in range(3):
        horn_mesh.vectors[i][j] = vertices[face[j], :]

# Save to STL file in the /3d/ folder
horn_mesh.save(stl_file_path)

print(f"\nSTL file saved as {stl_file_path}")
