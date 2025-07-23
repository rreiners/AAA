# Advanced Analytics and Application - SS 2025

**Team Assignment: Smart Mobility Ride-Hailing Analysis**<br>
**Student:** Saied Farham Nia
**Student ID:** 7441573
**Email:** sfarham1@smail.uni-koeln.de

**Course:** Advanced Analytics and Application (AAA) - SS 2025
**Institution:** University of Cologne, Faculty of Management, Economics, and Social Sciences, Department of Information Systems for Sustainable Society
**Instructor:** Prof. Dr. Wolfgang Ketter
**TA:** Janik Muires

## Setup and Installation

This project is configured to be used with a Devcontainer environment (e.g., using VS Code with the Dev Containers extension or GitHub Codespaces).

1.  **Prerequisites:**
    * Docker Desktop installed and running.
    * VS Code installed.
    * VS Code "Dev Containers" extension installed (ms-vscode-remote.remote-containers).

2.  **Clone the repository:**
    ```bash
    git clone https://github.com/rreiners/AAA
    cd AAA
    ```

3.  **Open in Devcontainer:**
    * Open the cloned repository folder in VS Code.
    * VS Code should automatically detect the `.devcontainer/devcontainer.json` configuration (if present).
    * Click on the "Reopen in Container" notification that appears in the bottom-right corner.
    * Alternatively, open the Command Palette (Ctrl+Shift+P or Cmd+Shift+P) and type/select "Dev Containers: Reopen in Container".
    * The devcontainer will build (if it's the first time) and start. This process will automatically handle the creation of the environment and installation of dependencies listed in `requirements.txt`

## 1. Project Overview

This project is part of the Advanced Analytics and Application course and focuses on analyzing the smart mobility market, specifically ride-hailing services. The goal is to act as a Data Science Team for "Bane & Wayne Partners (BWP)" consultancy, advising a renowned German car company looking to establish an electrified ride-hailing platform in the US market. The project involves understanding the dynamics of ride-hailing in a US city (Chicago) through temporal and spatial analysis of taxi trip data, weather data, and potentially Point-of-Interest (POI) data.

The core objectives include data collection and preparation, descriptive spatial analytics, predictive modeling of taxi demand using Support Vector Machines (SVM) and Neural Networks (NN), and exploring smart charging strategies for an electric vehicle fleet using Reinforcement Learning (RL).

## 2. Dataset Description

This project utilizes several data sources:

* **Chicago Taxi Trip Data:**
    * **Source:** Provided by the Chicago Data Portal. Contains taxi trips from 2024 onwards.
    * **Location in Repo:** A sample or preprocessed version is expected in `data/raw/chicago_taxi_trips.parquet`.
    * **Documentation:** [Chicago Taxi Trips Data Details](https://data.cityofchicago.org/Transportation/Taxi-Trips-2024-/ajtu-isnz/about_data)
* **Weather Data:**
    * **Task:** To be collected independently.
    * **Recommended Sources:**
        * NOAA NCEI: [Past Weather for Chicago](https://www.ncei.noaa.gov/access/past-weather/chicago)
        * Kaggle Datasets: [Kaggle](https://www.kaggle.com/datasets/)
        * Other open data sources (e.g., Open-Meteo via `src/api/weather.py`).
    * **Location in Repo:** Raw weather data is expected to be stored in `data/weather/`.
* **Point-of-Interest (POI) Data (Optional):**
    * **Task:** Consideration for collection is optional, based on skills, resources, and time.
    * **Possible Source:** OpenStreetMap.

## 3. Repository Structure

```
.
├── config/                             # Configuration files (general, logging, styling)
│   ├── config.yaml
│   ├── logging.yaml
│   └── styling.yaml
├── data/                               
│   ├── AAA_Team_Assignment.pdf         
│   ├── processed/                      
│   ├── raw/                            
│   ├── results/                        
│   └── weather/                        
├── LICENSE                             
├── notebooks/                          # Jupyter notebooks for exploration, analysis, and modeling
│   ├── 00_template.ipynb
│   └── 01_Data_Preparation.ipynb
├── README.md               
├── requirements.txt        
└── src/                                # Source code for the project
├── api/                                # Modules for interacting with external data APIs
│   ├── taxi.py         
│   └── weather.py      
├── init.py
└── utils/                              # Utility scripts and helper functions
├── init.py
├── logger.py       
├── notebook_setup.py 
└── styling.py      
```

## 4. Configuration

* **`config/config.yaml`:** General project configurations (e.g., file paths, parameters, `APP_TOKEN`).
* **`config/logging.yaml`:** Configuration for the Python logging module, used by `src/utils/logger.py`.
* **`config/styling.yaml`:** Styling preferences for plots or notebook outputs, potentially used by `src/utils/styling.py`.

## 5. Key Components

* **`src/api/taxi.py`:** <br> Python client to interact with the City of Chicago taxi trips Socrata API using the `sodapy` library. Handles fetching and basic processing of taxi data.
* **`src/api/weather.py`:** <br>Python client to fetch weather data. The current implementation is for the Open-Meteo API, which provides historical and forecast weather information.
* **`src/utils/logger.py`:** <br>Sets up a standardized logger for the project.
* **`src/utils/notebook_setup.py`:** <br>Contains common imports and setup routines for Jupyter notebooks to ensure consistency.
* **`src/utils/styling.py`:** <br>May contain functions or constants for consistent plot styling (e.g., matplotlib themes).
* **`notebooks/`:**
    * `00_template.ipynb`: A template for new notebooks.
    * `01_Data_Preparation.ipynb`: Notebook focused on loading, cleaning, and preparing the taxi and weather datasets for analysis. Subsequent notebooks will likely cover descriptive analytics, predictive modeling, and reinforcement learning.

## 6. License

This project is licensed under the terms of the [LICENSE](LICENSE) file. Please review it for details on usage and distribution.

## 7. Contact

Saied Farham Nia
sfarham1@smail.uni-koeln.de

---

