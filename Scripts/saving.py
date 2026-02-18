#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 18 11:58:01 2026

@author: rabea
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 30 14:20:41 2025

@author: rabea
"""

import json
import pandas as pd
import os
from pathlib import Path
from json_repair import repair_json


## Merge all json coords files (redundant if only one company is analysed)
os.chdir("/Users/yourname/Documents/GitHub/CSI_Database/Example")

coords_dir = Path("merged_outputs/coords")
output_file = coords_dir / "all_companies_coord.json"

# Skip processing if the output file already exists
if output_file.exists():
    print(f" Output file already exists: {output_file}")
else:
    # Initialize combined list
    combined_data = []

    # Loop through JSON files
    for json_file in coords_dir.glob("*.json"):
        if json_file.name == output_file.name:
            continue  # Skip the output file if it somehow exists in the directory

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    combined_data.extend(data)
                else:
                    print(f"⚠️ Skipped (not a list): {json_file}")
        except Exception as e:
            print(f" Error reading {json_file}: {e}")

    # Save combined data
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, indent=2)

    print(f" Combined JSON saved to: {output_file}")
    
### And finally finally: fix formatting (May not be necessary; depends on wether GPT followed output instructions preciseley)

def fix_json(directory):
    for file in Path(directory).glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                raw = f.read().strip()

            # Remove placeholders and fix list joins
            raw = raw.replace("[CONTINUE]", "")
            raw = raw.replace("]\n[", ",")
            raw = raw.replace("]\n\n[", ",")
            raw = raw.replace("],\n[", ",")  # <- handles your specific case
            raw = raw.replace("],\n  [", ",")  # <- handles indented version

            # Repair broken JSON
            repaired = repair_json(raw)
            data = json.loads(repaired)

            with open(file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f" Fixed and saved: {file.name}")

        except Exception as e:
            print(f" Error processing {file.name}: {e}")

fix_json(coords_dir)

### And export as csv (because the R package doesn't do it for me)

# Load the JSON data
with open(output_file, encoding='utf-8') as f:
    data = json.load(f)

# Flatten: extract projects and include report-level metadata
all_projects = []

for report in data:
    company = report.get("company")
    year = report.get("report_year")
    report_type = report.get("report_type")

    for project in report.get("projects", []):
        flat_project = {
            "company": company,
            "report_year": year,
            "report_type": report_type,
            **project  # Unpack all project-level fields
        }
        all_projects.append(flat_project)

# Convert to DataFrame
df = pd.DataFrame(all_projects)

# Save to CSV
df.to_csv("project_data.csv", index=False)
print(" CSV saved as: project_data.csv")