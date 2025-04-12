#!/usr/bin/env python3
"""
Analyze the SKU ID to SKU Group mapping CSV file.
This script provides basic statistics about the mapping data.
"""

import csv
import sys
import os
from collections import Counter, defaultdict

def analyze_csv(csv_file):
    """Analyze the CSV file and print statistics."""
    if not os.path.exists(csv_file):
        print(f"Error: File '{csv_file}' not found.")
        return
    
    try:
        # Read the CSV file
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header row
            
            if header != ['SKU ID', 'SKU Group']:
                print(f"Warning: CSV header doesn't match expected format. Found: {header}")
            
            # Initialize counters
            total_sku_ids = 0
            sku_groups = Counter()
            sku_ids_per_group = defaultdict(list)
            
            # Process each row
            for row in reader:
                if len(row) < 2:
                    continue
                    
                sku_id, sku_group = row
                total_sku_ids += 1
                sku_groups[sku_group] += 1
                sku_ids_per_group[sku_group].append(sku_id)
        
        # Print statistics
        print("\n=== SKU ID to SKU Group Mapping Analysis ===\n")
        print(f"Total SKU IDs: {total_sku_ids}")
        print(f"Total SKU Groups: {len(sku_groups)}")
        print("\nTop 10 SKU Groups by number of SKU IDs:")
        
        for group, count in sku_groups.most_common(10):
            print(f"  {group}: {count} SKU IDs")
        
        print("\nGroups with only one SKU ID:")
        single_sku_groups = [group for group, count in sku_groups.items() if count == 1]
        print(f"  {len(single_sku_groups)} groups ({(len(single_sku_groups) / len(sku_groups) * 100):.1f}% of all groups)")
        
        # Calculate average SKUs per group
        avg_skus = total_sku_ids / len(sku_groups) if sku_groups else 0
        print(f"\nAverage SKU IDs per group: {avg_skus:.2f}")
        
        # Print SKU ID format statistics
        print("\nSKU ID format analysis:")
        sku_formats = Counter()
        for sku_id in [sku_id for group_skus in sku_ids_per_group.values() for sku_id in group_skus]:
            # Analyze format by counting segments separated by hyphens
            format_key = f"{len(sku_id.split('-'))} segment(s)"
            sku_formats[format_key] += 1
            
        for format_type, count in sku_formats.most_common():
            print(f"  {format_type}: {count} SKU IDs ({(count / total_sku_ids * 100):.1f}%)")
            
    except Exception as e:
        print(f"Error analyzing CSV file: {str(e)}")

if __name__ == "__main__":
    # Use the provided file or default to sku_id_to_group_mapping.csv
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "sku_id_to_group_mapping.csv"
    analyze_csv(csv_file) 