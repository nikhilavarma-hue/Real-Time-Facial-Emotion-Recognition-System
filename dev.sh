#!/bin/bash

# Check if the zip file is provided as an argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 <zip_file>"
    exit 1
fi

ZIP_FILE=$1
TEMP_DIR="temp_extract"

# Create a temporary directory for extraction
mkdir -p "$TEMP_DIR"

# Extract the zip file to the temporary directory
echo "Extracting $ZIP_FILE to temporary directory..."
unzip -q "$ZIP_FILE" -d "$TEMP_DIR"

# Function to check if extracted content has a single root directory
function check_single_root() {
    local dir_count=$(find "$TEMP_DIR" -maxdepth 1 -type d | wc -l)
    # We subtract 1 because the temp directory itself is counted
    if [ $((dir_count - 1)) -eq 1 ]; then
        # Get the name of the single root directory
        local root_dir=$(find "$TEMP_DIR" -maxdepth 1 -type d -not -path "$TEMP_DIR" | head -1)
        echo "$root_dir"
    else
        echo ""
    fi
}

# Check if there's a single root directory
ROOT_DIR=$(check_single_root)

if [ -n "$ROOT_DIR" ]; then
    echo "Found single root directory: $ROOT_DIR"
    echo "Moving files from root directory to current directory..."
    
    # Move all contents from the single root directory to the current directory
    cp -r "$ROOT_DIR"/* .
else
    echo "No single root directory found. Moving all extracted files to current directory..."
    
    # Move all contents from the temp directory to the current directory
    cp -r "$TEMP_DIR"/* .
fi

# Clean up temporary directory
echo "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

# Now ensure all the required directories exist for both structures
echo "Ensuring all required directories exist..."

# First structure (from your first message)
mkdir -p app/{models,routes,services,static/{css,img,js/{charts,tracking}},templates/{auth,dashboard,landing,projects},utils}
mkdir -p instance
mkdir -p migrations/versions
mkdir -p templates

# Second structure (from your second message)
mkdir -p app/{api,blueprints,database,models/{data,detectors,saved_models},static/{css,img,js},templates,utils}
mkdir -p instance
mkdir -p tests

# Make sure all __init__.py files exist
find app -type d -exec touch {}/__init__.py \; 2>/dev/null || true

echo "Project structure setup complete!"