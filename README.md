## Project Summary

This project builds a structured dataset of Corporate Social Investment
(CSI) projects from company reports using the OpenAI API and the Google
Maps Geocoding API. It processes extracted PDF text from company
reports, applies large language models to identify and structure
project-level information, and stores the results in JSON and CSV
formats.

The final dataset includes information on the company, report type and
year, project name, description and implementation year, project
location, references to the report and page where the project is
mentioned, and additional structured metadata suitable for quantitative
and spatial analysis.

## Purpose and Motivation

Company annual and sustainability reports contain a wealth of
information that can be valuable for empirical research. Financial and
easily quantifiable environmental data are often already available in
structured datasets. In contrast, qualitative information for which no
standardised reporting framework exists is much harder to obtain.

Corporate social investment is one such example. Many companies
(particularly in the mining sector) invest in local communities through
initiatives such as infrastructure development, employment programmes,
and education or health projects. While firms often describe these
activities in considerable detail, extracting this information at scale
is challenging. Projects are often described in running text, summarised
in tables, or presented as a mix of the two.Manual extraction is
therefore highly time-consuming and impractical for large samples.

This workflow utilises large language models (specifically GPT via the
OpenAI API) to automate the extraction of project-level information from
company reports. The output is a structured, geo-coded dataset that can
be used for quantitative and spatial analysis.

Importantly, the code produces a *raw* dataset; further cleaning and
validation remain the researcher’s responsibility. This can include
removing irrelevant projects, filling in missing or unclear information,
and checking the extracted data against the original reports. In
addition, projects that span multiple years and appear in several
reports will be extracted multiple times. Although the workflow includes
an algorithm that flags potential duplicate entries, researchers must
manually verify these cases and determine project start and end years.

## Repository Structure

Below is a short overview of the repository structure.

    CSI_Database/
    ├── Example/
    │   ├── company_reports_extracts/   # PDF extracts from company reports
    │   ├── merged_outputs/             # JSON files resulting from merging individual report outputs
    │   │   ├── complete/               # Complete merged datasets
    │   │   ├── coords/                 # Geo-coded project locations
    │   │   ├── dup/                    # Identified duplicate projects
    │   │   ├── dup_prep/               # Prepared files for duplicate checking
    │   │   └── raw/                    # Raw merged outputs before cleaning
    │   └── outputs/                    # Extracted datasets for each report from the first extraction step
    ├── Prompts/
    │   ├── Prompt1.txt                  # Identifies projects from PDF extracts
    │   ├── Prompt2.txt                  # Regroups identified projects
    │   ├── Prompt3.txt                  # Extracts concrete project information from PDF extracts
    │   └── Prompt4.txt                  # Identifies duplicates in the raw database and flag them
    └── Scripts/
        ├── extraction.py                # Extracts projects, stores per-report JSON, merges per company
        ├── duplicates.py                # Identifies duplicates within each company’s JSON dataset 
        ├── geocoding.py                 # Convert location strings to lat/long, adds to dataset
        └── saving.py                    # Fixes formatting and exports the final dataset as CSV

### Example Folder

The `company_reports_extracts/` folder contains four example extracts
from different DRDGOLD reports used to illustrate the extraction
process. All files in the `outputs/` and `merged_outputs/` folders are
based on these example reports. When replicating the process:

-   Delete all existing files in `outputs/` and `merged_outputs/`
    first.  
-   The scripts will skip processing PDFs for which an output already
    exists, so failing to delete old outputs may prevent new extracts
    from being processed.

**DRDGOLD Report References:**

DRDGOLD Limited. (2011). *Integrated Report 2011*. Johannesburg: DRDGOLD
Limited.  
DRDGOLD Limited. (2015). *Sustainability Report 2015*. Johannesburg:
DRDGOLD Limited.  
DRDGOLD Limited. (2018–2022). *Ergo Social and Labour Plan (SLP)
2018–2022*. Johannesburg: DRDGOLD Limited.  
DRDGOLD Limited. (2019). *Integrated Report 2019*. Johannesburg: DRDGOLD
Limited.

## Step-by-step Overview of the Extraction Pipeline

### 1. Preparing PDF Extracts

Example/company\_reports\_extracts/ contains the PDF extracts of company
reports. The pipeline cannot handle full reports because they are too
large. It is therefore important to extract only the pages that may
contain relevant information, typically the “Communities” section of a
corporate report.

### 2. Identifying Projects and Eelevant Project Information (Prompt 1 to 3)

extraction.py uses Prompt 1 to scan each PDF extract. The model
identifies all potential CSI projects mentioned in the extract and
stores the information in a JSON file with two fields: project\_name and
subproject.

Prompt 2 takes the JSON file created by Prompt 1 and regroups related
projects and subprojects to reduce redundancy.

Prompt 3 extracts concrete project-level information based on Prompt 2’s
output, including:

-   Name
-   Description
-   Location
-   Implementation year
-   Beneficiaries
-   Report references and page numbers
-   And more

Prompt 3’s output is stored as a per-report JSON file in
Example/outputs/. In the next step, meta data for each report (type,
company, and year) and inferred from the extract name and added to the
information above. Individual JSON files for each report are then merged
into a company-level dataset and stored in Example/merged\_outputs/raw/.

Before identifying duplicates, a new folder
Example/merged\_outputs/dup\_prep/ is created. It contains the same JSON
files as raw/, but removes all information unnecessary for duplicate
detection, reducing file size and API costs.

### 3. Identifying Duplicates (Prompt 4)

duplicates.py takes the JSON files in Example/merged\_outputs/dup\_prep/
and runs Prompt 4 to identify duplicates in each company’s project
files.

The result is a new dataset with two new fields:

-   duplicate – indicates whether a project appears at least twice in
    the dataset
-   project\_id – assigns a unique ID to each project; duplicates
    inherit the ID of the original project

The new files are stored in Example/merged\_outputs/dup/. The script
also creates Example/merged\_outputs/complete/, which contains the
complete dataset for each company by merging back any information that
had been removed in dup\_prep/.

### 4. Geocoding Project Locations

geocoding.py uses JSON files in Example/merged\_outputs/complete/, reads
the location information from the dataset, and converts these location
strings into latitude and longitude using the Google Maps API. The
results add two new fields: lat and long, and are stored in
Example/merged\_outputs/coords/.

### 5. Finalising and Exporting Dataset

saving.py fixes formatting issues, merges all company JSON files, and
exports the dataset as a CSV. The final CSV is stored in the Example/
folder.

## Practical Issues and How to Run

### Preparing the Company Report Extracts

As mentioned above, the folder company\_reports\_extracts/ should only
contain extracts of company reports, not the full reports. Each extract
should be named in the following format: Company\_Year\_ReportType.pdf
(For example: Harmony\_2011\_IR.pdf for Harmony’s 2011 Integrated
Report).

This naming convention is important for the scripts to accurately infer
report metadata.

Reports should be saved in separate folders for each company. In the
example dataset, there is only one company: DRDGOLD. The folder
structure should therefore include a DRDGOLD/ folder containing all PDF
extracts for that company. The `company_reports_extracts/` directory is
the only directory that needs to be set up manually. All other
directories are created automatically by the scripts.

## Preparing the Prompts

Prompts 1 to 3 are not written directly in the code. Instead, they were
created beforehand in the OpenAI API. The Prompt\*.txt files contain the
exact wording of each prompt. To use them:

    1.  Copy the system and user message from the .txt file.
    2.  Create a new prompt in the OpenAI API using this text.
    3.  Once the prompt is saved, copy the Prompt ID by clicking the three dots in the results window.
    4.  Paste the Prompt ID in the scripts

It is not important which model or settings are displayed when creating
the prompt; the script sets these independently. The only requirement is
to insert the correct Prompt ID in the script. This approach offers
flexibility: prompts can be modified in the API, saved as a new version,
and the script can then be re-run by updating only the prompt version
number, without making any changes to the script itself.

Prompt 4, however, is written directly in the script. This is because it
requires interacting with the model after the initial prompt is entered.
The interaction is automated in the script and works fine when pasting
the prompt directly in the script. However, when trying to read Prompt 4
via a Prompt ID (as with Prompts 1–3), the script breaks. If anyone has
a fix for this problem, please let me know.

## Preparing API Keys

The script requires access to two APIs:

    1.  OpenAI API
    2.  Google Maps Geocoding API (via Google Cloud)

Both APIs need to be set up in advance, and the corresponding API keys
need to be obtained before running the scripts.

Notes:

-   Accessing the OpenAI API requires a positive credit balance. The
    process is not costly; running the four example extracts only costs
    a few cents. However, the code will not run without available
    credit.
-   The Google Geocoding API offers generous free usage limits, so for
    typical use (including the example dataset) there is usually no
    cost. However, Google requires a payment method to be linked to the
    API in case the free quota is exceeded.

### Setting up the API Keys

Before running the scripts, it is important to store the two API keys in
environment variables and run the scripts from the terminal. For MacOS,
you can do this as follows:

-   export OPENAI\_API\_KEY=“your\_actual\_openai\_key”
-   export GMAPS\_API\_KEY=“your\_actual\_google\_maps\_key”

After setting the environment variables, run your Python script (or your
IDE) from the same terminal session to ensure the keys are accessible.

## Python Packages and Version

The scripts were tested on Python 3.9.13 and run on macOS. The following
external packages need to be installed for running the script (can be
installed via pip):

-   openai
-   googlemaps
-   pandas
-   json\_repair

## Running the Scripts

Before running the scripts, the two API keys must be stored in
environment variables, and the scripts must be executed from the
terminal. For macOS, this can be done as follows:

-   `export OPENAI_API_KEY="your_actual_openai_key"`
-   `export GMAPS_API_KEY="your_actual_google_maps_key"`

After setting the environment variables, the Python script (or IDE) must
be run from the same terminal session to ensure that the keys are
accessible.

## Expected Outputs

The following outputs are generated by the scripts:

<table>
<colgroup>
<col style="width: 21%" />
<col style="width: 43%" />
<col style="width: 35%" />
</colgroup>
<thead>
<tr>
<th>Script</th>
<th>Output Location</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>extraction.py</code></td>
<td><code>Example/outputs/</code></td>
<td>Per-report JSON files containing extracted projects and
project-level information.</td>
</tr>
<tr>
<td></td>
<td><code>Example/merged_outputs/raw/</code></td>
<td>Company-level merged dataset before duplicate detection.</td>
</tr>
<tr>
<td></td>
<td><code>Example/merged_outputs/dup_prep/</code></td>
<td>JSON files prepared for duplicate detection (some fields removed to
reduce size and API costs).</td>
</tr>
<tr>
<td><code>duplicates.py</code></td>
<td><code>Example/merged_outputs/dup/</code></td>
<td>JSON files with duplicates flagged (<code>duplicate</code> field)
and unique project IDs (<code>project_id</code>).</td>
</tr>
<tr>
<td><code>duplicates.py</code></td>
<td><code>Example/merged_outputs/complete/</code></td>
<td>Complete company-level datasets with all original project
information restored.</td>
</tr>
<tr>
<td><code>geocoding.py</code></td>
<td><code>Example/merged_outputs/coords/</code></td>
<td>Geo-coded datasets with <code>lat</code> and <code>long</code>
fields added for each project location.</td>
</tr>
<tr>
<td><code>saving.py</code></td>
<td><code>Example/</code></td>
<td>Final merged dataset exported as CSV, ready for analysis.</td>
</tr>
</tbody>
</table>

**Notes:**

-   All output directories are **created automatically** by the scripts
    if they do not already exist.  
-   The final CSV contains all companies and all projects, including
    metadata, geolocation, and duplicate flags.  
-   Intermediate JSON files allow for inspection or further cleaning
    before generating the final CSV.

## Data Structure of the Final Output File

The final CSV and JSON files contain the following fields:

<table>
<colgroup>
<col style="width: 35%" />
<col style="width: 65%" />
</colgroup>
<thead>
<tr>
<th>Field</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>company</code></td>
<td>Name of the mining company reporting the project.</td>
</tr>
<tr>
<td><code>report_year</code></td>
<td>Year of the report from which the project was extracted.</td>
</tr>
<tr>
<td><code>report_type</code></td>
<td>Type of the report (e.g., Integrated Report <code>"IR"</code>,
Sustainability Report <code>"SR"</code>).</td>
</tr>
<tr>
<td><code>projects</code></td>
<td>List of projects extracted from the report.</td>
</tr>
<tr>
<td><code>project_name</code></td>
<td>Name of the project.</td>
</tr>
<tr>
<td><code>subprojects</code></td>
<td>Detailed listing of sub-projects or specific activities within the
main project.</td>
</tr>
<tr>
<td><code>description</code></td>
<td>Narrative description of the project and its objectives.</td>
</tr>
<tr>
<td><code>mine</code></td>
<td>The mine or operational site associated with the project, if
applicable.</td>
</tr>
<tr>
<td><code>partners</code></td>
<td>Project partners or collaborating organizations.</td>
</tr>
<tr>
<td><code>stage</code></td>
<td>Implementation stage(s) of the project (e.g., Operating,
Completed).</td>
</tr>
<tr>
<td><code>years</code></td>
<td>Year(s) during which the project was implemented.</td>
</tr>
<tr>
<td><code>project_value_company</code></td>
<td>Amount invested by the company in the project (if reported).</td>
</tr>
<tr>
<td><code>project_value_partners</code></td>
<td>Amount invested by project partners (if reported).</td>
</tr>
<tr>
<td><code>category</code></td>
<td>Project category or type (e.g., Community Training, Infrastructure,
Health, Education). Multiple categories are separated by dots.</td>
</tr>
<tr>
<td><code>location</code></td>
<td>Textual description of the project location. May contain multiple
locations separated by semicolons.</td>
</tr>
<tr>
<td><code>location_accuracy</code></td>
<td>Granularity of the location information (e.g., Municipality,
Building).</td>
</tr>
<tr>
<td><code>pages</code></td>
<td>Pages in the report where the project is described.</td>
</tr>
<tr>
<td><code>project_id</code></td>
<td>Unique identifier assigned to each project; used to track duplicates
across reports.</td>
</tr>
<tr>
<td><code>duplicate</code></td>
<td>Indicates whether the project appears in more than one report
(<code>Yes</code>/<code>No</code>).</td>
</tr>
<tr>
<td><code>lat1</code></td>
<td>Latitude coordinate of the project location (from Google Maps
Geocoding API).</td>
</tr>
<tr>
<td><code>long1</code></td>
<td>Longitude coordinate of the project location (from Google Maps
Geocoding API).</td>
</tr>
</tbody>
</table>

**Notes:**

-   Some projects may have multiple locations. In that case, additional
    fields `lat2`, `long2`, etc., may be added to store coordinates for
    each location.  
-   Some fields (e.g., `project_value_company`, `partners`) may be empty
    if the information was not reported in the source document.  
-   The dataset is **raw**; further cleaning and verification is
    required
