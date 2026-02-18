#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 17 13:59:36 2026

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
import re


## Set directory and ensure API Key is stored in session 
print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
os.chdir("/Users/yourname/Documents/GitHub/CSI_Database/Example")


## Get access to API

client = OpenAI(api_key=os.getenv("API_KEY"))

#### Define paths

raw_dir = Path("merged_outputs/raw")
dup_dir = Path("merged_outputs/dup")
dupprep_dir = Path("merged_outputs/dup_prep")
complete_dir = Path("merged_outputs/complete")

### First: identify duplicate entries in json files in dupprep folder
                

# Loop through only files (no subfolders) in the input directory
for json_path in dupprep_dir.iterdir():
    if json_path.is_file() and json_path.suffix.lower() == ".json":
        rel_path = json_path.relative_to(dupprep_dir)
        output_path = dup_dir / rel_path.with_suffix(".json")

        if output_path.exists():
            print(f"Skipping existing file: {output_path}")
            continue

        print(f"\n Processing: {json_path}")

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)
                json_string = json.dumps(json_data, indent=2)

            # Prepare your OpenAI message setup
            messages = [
                {"role": "system", "content": "You are a diligent research assistant, specialised in identifying duplicate information in datasets."},
                {"role": "user", "content": "# General Processing Instruction\n\nThe JSON scheme that you will put out is too large to be returned in one output message. Therefore, please return the result in parts. At the end of each part, include '[CONTINUE]' unless this was the last chunk of output. n\n After you're done, check that no project in the input file was skipped; if\n\n Please find the task and input text below."},
                {"role": "user", "content": """# Task Overview

                                             You will be presented with a json schema that contains data on different projects run by different mining companies in South Africa. It will be your task to identify duplicate of these projects, i.e. projects that are listed twice or more. Do not change the order of projects in the file. Consider the exact task and definition of a duplicate below.

                                              # Task Breakdown

                                             In particular, do the following tasks in exactly this order:

                                             First: for each project, create two new fields: "project_id" and "duplicate", and set "duplicate" to the default "No".

                                             Second: run through the file project by project and give each project a unique "project_id", consisting of: the first three letters of the company that runs it + the report year + a number you can choose yourself (e.g. start with 1).

                                             Third: run through the file again. If you encounter a project that was already listed before, do the following:
                                                 a) Change the "duplicate" field from "No" to "Yes". mportant: Change the existing field. Do not create a new field. 
                                                 b) Replace the "project_id" you populated in the previous step with the value of "project_id" of the original project. Important: Change the existing field. Do not create a new field. 

                                             # Definition of a duplicate

                                             A project is a duplicate if the same project has been mentioned in an earlier entry already. This does not mean that two projects have the exact same values or the same information across all fields. Instead, infer whether a project was listed twice based on the core identifying variables: name and description and location. If the name and description sound similar, flag it. If you are unsure if it is a duplicate: flag it anyway. 

                                             # Output Format

                                             Provide the output exactly as specified below. Do not add any explanatory comments, or anything to indicate it is a json scheme.
                                             {
                                                 "company": "",
                                                 "report_year": "",
                                                 "report_type": "",
                                                 "projects": [
                                                     {
                                                         "project_id": "",
                                                         "duplicate": false,
                                                         "project_name": "",
                                                         "subprojects": "",
                                                         "description": "",
                                                         "mine": "",
                                                         "partners": "",
                                                         "stage": "",
                                                         "years": "",
                                                         "project_value_company": "",
                                                         "project_value_partners": "",
                                                         "category": "",
                                                         "location": "",
                                                         "location_accuracy": "",
                                                         "pages": ""
                                                     }
                                                 ]
                                             }
                                             """
                                             }, 
                {"role": "user", "content": json_string}
            ]

            full_output = ""
            max_rounds = 30

            for round_num in range(max_rounds):
                response = client.chat.completions.create(
                    model="gpt-5-mini",
                    messages=messages
                )

                assistant_output = response.choices[0].message.content
                full_output += assistant_output + "\n"

                messages.append({"role": "assistant", "content": assistant_output})

                if "[CONTINUE]" in assistant_output:
                    messages.append({"role": "user", "content": "Please continue with the next chunk."})
                else:
                    break

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(full_output)

            print(f" Saved: {output_path}")

        except Exception as e:
            print(f" Error processing {json_path.name}: {e}")
            
### Merge the new duplicate information with the original dataset 

### Remove the "[CONTINUES]" and put into [] 

for file_path in dup_dir.rglob("*.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # Replace [CONTINUE] placeholders with a comma
    if "[CONTINUE]" in content:
        content = content.replace("[CONTINUE]", ",")

    # Insert commas between adjacent JSON objects if missing
    # Looks for `}{` or `} \n {` patterns and inserts a comma
    content = re.sub(r"}\s*{", r"},\n{", content)

    # Ensure the content is wrapped as a JSON list
    if not content.startswith("["):
        content = "[" + content
    if not content.endswith("]"):
        content = content + "]"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Fixed: {file_path}")
        
        
### Merge information with original dataset

# Loop through each JSON file in the dup folder
for dup_file in dup_dir.rglob("*.json"):
    rel_path = dup_file.relative_to(dup_dir)
    raw_file = raw_dir / rel_path
    output_file = complete_dir / rel_path

    # Skip if already exists
    if output_file.exists():
        print(f" Skipping existing: {output_file}")
        continue

    try:
        with open(dup_file, "r", encoding="utf-8") as f:
            dup_data = json.load(f)

        with open(raw_file, "r", encoding="utf-8") as f:
            complete_data = json.load(f)

        # Create lookup
        dupdata_lookup = {}
        for entry in dup_data:
            key = (entry["company"], entry["report_year"], entry["report_type"])
            for project in entry["projects"]:
                project_key = key + (project["project_name"], project["description"])
                dupdata_lookup[project_key] = {
                    "project_id": project.get("project_id"),
                    "duplicate": project.get("duplicate")
                }

        # Merge
        for entry in complete_data:
            key = (entry["company"], entry["report_year"], entry["report_type"])
            for project in entry["projects"]:
                project_key = key + (project["project_name"], project["description"])
                dupdata = dupdata_lookup.get(project_key, {})
                project["project_id"] = dupdata.get("project_id")
                project["duplicate"] = dupdata.get("duplicate")

        # Save merged
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(complete_data, f, indent=2)

        print(f" Merged and saved: {output_file}")

    except Exception as e:
        print(f" Error processing {dup_file}: {e}")

                
                
                