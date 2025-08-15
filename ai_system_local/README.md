SCADA Fault Analyzer
Overview
This project is a Python-based tool designed for analyzing SCADA (Supervisory Control and Data Acquisition) data to detect and diagnose fault scenarios in electrical systems, such as power grids or industrial control environments. It processes CSV-formatted SCADA logs, identifies key events like pickup and trip signals (specifically related to protection relays like ANSI 67 for directional overcurrent), and detects critical anomalies such as high phase or neutral currents.
To enhance the analysis, the tool integrates a local large language model (LLM) via Ollama (using the Llama 3.1 8B model) for fine-tuned fault detection. This allows for natural language-based interpretation of the data summary, enabling the model to reason about potential faults without relying on cloud-based AI services. The approach emphasizes privacy and offline capability, making it suitable for sensitive industrial applications where data security is paramount.
The analysis pipeline includes data loading, cleaning, event detection, summarization, LLM-based reasoning, and result logging. All operations are logged for traceability, and outputs are saved in a structured format.
Key Features

Data Loading and Preprocessing: Loads CSV files from a data directory, cleans column names, and sorts data by timestamp.
Fault Scenario Analysis:

Detects "PICK UP" and "TRIP" signals in columns containing '67' (directional protection).
Identifies critical events based on high currents (e.g., phase currents >10A or neutral current >5A).


Summary Generation: Creates a textual summary of total records, time range, signal activations, and critical events.
LLM Integration: Uses Ollama's local API to send the data summary to a fine-tuned Llama 3.1 model for detailed fault interpretation. The prompt is loaded from a customizable file in the prompts directory.
Output Management: Saves analysis results as timestamped TXT files in an output directory, including a preview in the console.
Logging: Comprehensive logging to both file (scada_fault_analysis.log) and console for debugging and auditing.
Stateful Directories: Automatically creates prompts, data, and output directories if they don't exist.

How It Works
The tool is structured around a SCADAFaultAnalyzer class, which handles the entire workflow. Here's a step-by-step breakdown:

Initialization:

Sets up directories for prompts, data, and outputs.
Loads the fault analysis prompt from prompts/fault_analysis_prompt.txt (this prompt is customizable and includes placeholders for data summaries).
Configures Ollama API settings (host: http://localhost:11434, model: llama3.1:8b, with options like GPU layers, context size, and temperature for fine-tuned responses).


Data Loading (load_scada_data):

Reads CSV files using Pandas.
Cleans column names by replacing spaces and special characters.
Converts and sorts the 'time' column (in seconds) for chronological analysis.


Fault Analysis (analyze_fault_scenarios):

Computes basic statistics: total records and time range.
Scans for PICK UP signals (e.g., columns like '67_Phase_Pick_Up') and counts activations, recording the first few timestamps.
Similarly analyzes TRIP signals.
Detects critical events by iterating through rows and checking for high currents in phases (IL1, IL2, IL3) or neutral (Io), associating them with active signals.


Summary Generation (generate_data_summary):

Formats the analysis into a readable text block, including counts, timestamps, and details of up to 5 critical events.


LLM Analysis (analyze_with_ollama):

Replaces placeholders in the prompt with the data summary.
Sends a POST request to Ollama's generate API for non-streaming response.
Handles errors gracefully (e.g., connection issues if Ollama isn't running).


Result Saving (save_results):

Writes the LLM's response to a file with a header including the current date/time.


Full Pipeline (run_analysis):

Orchestrates the above steps for a given CSV file.
In the main function, it scans the data directory for all CSV files and processes them sequentially, printing previews.



The LLM fine-tuning aspect is achieved through prompt engineering: the fault_analysis_prompt.txt is designed to guide the model in interpreting SCADA-specific patterns, such as correlating signal activations with current spikes to infer faults like short circuits or ground faults. No explicit training data is used; instead, the prompt acts as a "fine-tune" by providing context and examples within the query.
Requirements

Python 3.10+: With libraries: pandas, numpy, requests, pathlib, logging, datetime.

Install via: pip install pandas numpy requests


Ollama: Must be installed and running locally.

Download from ollama.com.
Pull the model: ollama pull llama3.1:8b
Start the server: ollama serve (run in a separate terminal).


Hardware: GPU recommended for faster inference (configured with 10 GPU layers by default).
Input Files: Place SCADA data as CSV files in the data directory (e.g., comtrade40_data.csv). Columns should include 'time', phase currents (IL1, IL2, IL3), neutral (Io), and signal columns like '67_Phase_PICK_UP'.

Usage

Clone the repository:
textgit clone https://github.com/yourusername/scada-fault-analyzer.git
cd scada-fault-analyzer

Prepare directories:

Create prompts/fault_analysis_prompt.txt with your custom prompt (e.g., instructions for fault reasoning).
Add CSV files to data/.


Run the script:
textpython main.py

It will process all CSV files in data/, generate analyses, and save results in output/.
Console output includes previews and log messages.


Customize:

Edit fault_analysis_prompt.txt to fine-tune the LLM's behavior (e.g., add domain-specific examples).
Adjust Ollama options in __init__ for performance.



Example Output
An example analysis result might look like:
text## SCADA Arıza Analiz Raporu
## Tarih: 2025-08-15 14:30:00

Based on the data summary, the fault appears to be a phase-to-ground short circuit in Phase A, triggered at 0.1234s with high IL1 current and 67_Phase_PICK_UP activation, followed by a TRIP at 0.1500s.
Limitations

Assumes specific column naming conventions in CSV files.
Thresholds for critical events (e.g., 10A for phases) are hardcoded; customize as needed.
Ollama must be running; no fallback to other models.
No real-time monitoring; batch processing only.

Security Note
For security reasons, we have included three sample input files in the repository (e.g., anonymized or synthetic CSV datasets) to demonstrate the tool without exposing real SCADA data. These files are designed to mimic fault scenarios while ensuring no sensitive information is shared. Always anonymize or use synthetic data in production to prevent data leaks.
