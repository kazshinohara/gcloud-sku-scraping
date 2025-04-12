#!/bin/bash
# Script to run the Google Cloud SKU ID to SKU Group Mapper

# Make sure the script is executable with: chmod +x run_scraper.sh

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the script
echo "Running SKU ID to SKU Group Mapper..."
python skuid_group_scraper.py

# Check if the script ran successfully
if [ $? -eq 0 ]; then
    echo "Script completed successfully."
    echo "Results are in $(pwd)/sku_id_to_group_mapping.csv"
else
    echo "Script encountered an error. Check scraper.log for details."
fi

# Deactivate virtual environment
deactivate 