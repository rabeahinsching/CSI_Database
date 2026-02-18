#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 18 12:05:43 2026

@author: rabea
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 20 16:21:52 2025

@author: rabea
"""

import os
import json
from openai import OpenAI
from pathlib import Path


## Set directory and ensure API Key is stored in session 
print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
os.chdir("/Users/yourname/documents/CSI_Database/Example")


## Get access to API

client = OpenAI(api_key=os.getenv("API_KEY"))

# Define paths
input_base_dir = Path("company_reports_extracts")       # PDF extracts (one folder per company)
output_base_dir = Path("outputs")                       # JSON schemes per report
merged_output_dir = Path("merged_outputs/raw")          # Merged raw JSON data per company
dupprep_dir = Path("merged_outputs/dup_prep")           # JSON files prepared for duplicate analysis

# Prompt and model settings
prompt1 = {"id": "pmpt_685294d46264819085eb480c5e5a64e0064bc082b34f9d57", "version": "8"} # Identifies projects from pdf extracts and lists them in json format
prompt2 = {"id": "pmpt_685294d59f888197b426bc25a104067608733608c9ef5bc3", "version": "5"} # Cleans project list extracted under prompt 1
prompt3 = {"id": "pmpt_685294d4f6488197bf90ca2ae1a23ee1082f2d1b95397595", "version": "8"} # Takes cleaned project list and adds information to the json scheme, based on pdf extracts


# Loop through all subfolders in the input directory, and feed each pdf extract to prompt 1 in the API
for root, _, files in os.walk(input_base_dir):
    for filename in files:
        if filename.lower().endswith(".pdf"):
            pdf_path = Path(root) / filename
            rel_path = pdf_path.relative_to(input_base_dir)
            output_path = output_base_dir / rel_path.with_suffix(".txt")

            # Skip if output already exists
            if output_path.exists():
                print(f"Skipping existing file: {output_path}")
                continue

            print(f"\nProcessing: {pdf_path}")

            try:
                # Upload PDF
                file = client.files.create(
                    file=open(pdf_path, "rb"),
                    purpose="user_data"
                )
                file_id = file.id
                print(f"Uploaded: {file_id}")  # Uploads pdf extract in API

                # Prompt 1
                response1 = client.responses.create(
                    prompt=prompt1,
                    model="gpt-4.1-mini",
                    input=[{
                        "role": "user",
                        "content": [{"type": "input_file", "file_id": file_id}] # inputs pdf extract
                    }],
                    reasoning={},
                    max_output_tokens=21687, # can be changed, this was the default
                    store=False
                )
                output1 = response1.output_text # responses of the model (i.e., the json scheme) get stored temporarily under output1

                # Prompt 2
                response2 = client.responses.create(
                    prompt=prompt2,
                    model="o4-mini",
                    input=[{
                        "role": "user",
                        "content": [{"type": "input_text", "text": output1}] # inputs prompt 1 response into prompt 2
                    }],
                    reasoning={"effort": "medium"},
                    store=False
                )
                output2 = response2.output_text # response from model 2 gets saved under output2

                # Prompt 3
                response3 = client.responses.create(
                    prompt=prompt3,
                    model="gpt-4.1",
                    input=[{
                        "role": "user",
                        "content": [
                            {"type": "input_file", "file_id": file_id}, # inputs pdf extract
                            {"type": "input_text", "text": output2}  # inputs prompt 2 response
                        ]
                    }],
                    max_output_tokens=22000,
                    store=False
                )
                output3 = response3.output_text  # Final output

                # Write result to output
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(output3)
                print(f"Saved to: {output_path}")

            except Exception as e:
                print(f" Error processing {pdf_path.name}: {e}")

            finally:
                # Always delete uploaded file to avoid quota issues
                try:
                    client.files.delete(file_id)
                    print(f"Deleted file from API: {file_id}")
                except Exception as e:
                    print(f" Failed to delete file: {e}")
                    
#### Add the company and year (metadata)

# Loop through all .txt files in all subfolders in the output directory and extract report metadata from the file names
for txt_file in output_base_dir.rglob("*.txt"):
    filename = txt_file.stem

    if filename.count("_") < 2:
        print(f" Skipping {txt_file.name}: filename doesn't match expected pattern.")
        continue

    try:
        company, report_year, report_type = filename.split("_", 2)

        with open(txt_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        updated_data = {
            "company": company,
            "report_year": report_year,
            "report_type": report_type,
            "projects": data.get("projects", [])
        }

        with open(txt_file, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, indent=2, ensure_ascii=False)

        print(f" Updated: {txt_file.name}")

    except Exception as e:
        print(f" Error processing {txt_file.name}: {e}")
                    
#### Merge the project txt files per company
# Loop through each subfolder in the output directory
for subfolder in output_base_dir.iterdir():
    if subfolder.is_dir():
        txt_files = sorted(subfolder.glob("*.txt"))
        if not txt_files:
            continue  # Skip if no .txt files in this subfolder

        all_entries = []

        for txt_file in txt_files:
            try:
                with open(txt_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        entry = json.loads(content)  # parse JSON from text
                        all_entries.append(entry)
            except Exception as e:
                print(f" Could not process {txt_file.name} in {subfolder.name}: {e}")

        if all_entries:
            # Save all combined entries into one JSON file
            merged_output_dir.mkdir(parents=True, exist_ok=True)
            merged_filename = f"{subfolder.name}_complete.json"
            merged_file_path = merged_output_dir / merged_filename

            with open(merged_file_path, "w", encoding="utf-8") as f:
                json.dump(all_entries, f, indent=2)

            print(f" Merged {len(txt_files)} files into {merged_file_path}")
            
            
### Before running the prompt that identifies duplicates: Make the token size smaller by keeping only relevant variables temporarily 

for root, _, files in os.walk(merged_output_dir):
    for filename in files:
        if filename.lower().endswith(".json"):
            json_path = Path(root) / filename
            rel_path = json_path.relative_to(merged_output_dir)
            output_path = dupprep_dir / rel_path.with_suffix(".json")

            if output_path.exists():
                print(f"Skipping existing file: {output_path}")
                continue

            print(f"\n Processing: {json_path}")

            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data_list = json.load(f)

                if not isinstance(data_list, list):
                    raise ValueError("Expected top-level JSON to be a list.")

                filtered_list = []

                for entry in data_list:
                    if not isinstance(entry, dict):
                        continue

                    filtered_entry = {
                        "company": entry.get("company", ""),
                        "report_year": entry.get("report_year", ""),
                        "report_type": entry.get("report_type", ""),
                        "projects": []
                    }

                    for project in entry.get("projects", []):
                        if isinstance(project, dict):
                            filtered_project = {
                                "project_name": project.get("project_name", ""),
                                "description": project.get("description", ""),
                                "location": project.get("location", "")
                            }
                            filtered_entry["projects"].append(filtered_project)

                    filtered_list.append(filtered_entry)

                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as out_f:
                    json.dump(filtered_list, out_f, indent=2)

                print(f" Saved filtered output: {output_path}")

            except Exception as e:
                print(f" Error processing {json_path.name}: {e}")
                
                
                
                
            