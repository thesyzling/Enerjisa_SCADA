🌟 SCADA Fault Analyzer 🚀
📖 Overview
Welcome to the SCADA Fault Analyzer! 🎉 This Python-powered tool is your go-to solution for diving deep into SCADA (Supervisory Control and Data Acquisition) data to uncover and diagnose electrical system faults, such as those in power grids or industrial setups. 🔌 It’s like a detective 🕵️‍♂️ for your electrical data, sniffing out anomalies like high currents or protection relay signals (e.g., ANSI 67 directional overcurrent) with precision and flair! 
What makes this project extra special? ✨ It harnesses the power of a local large language model (LLM) via Ollama (using the Llama 3.1 8B model 🦙) to provide fine-tuned, natural language-based fault analysis—all without needing the cloud! 🌐 This ensures your sensitive data stays safe and secure, making it perfect for high-stakes industrial environments. 🔒
From loading and cleaning data 📊 to spotting critical events ⚡ and generating insightful reports 📝, this tool does it all while keeping you informed with detailed logs. Let’s explore how this magic happens! 🪄
🌈 Key Features

📂 Data Loading & Preprocessing: Reads CSV files from a data folder, tidies up column names (no more pesky spaces or special characters! 😎), and sorts everything by timestamp for smooth analysis.
🔍 Fault Scenario Analysis: 
Detects PICK UP and TRIP signals for protection relays (like those with '67' in the name 🛠️).
Spots critical events, like phase currents (IL1, IL2, IL3) spiking above 10A or neutral currents (Io) exceeding 5A. 🚨


📄 Summary Generation: Turns raw data into a clear, human-readable summary of record counts, time ranges, and critical events. 📜
🧠 LLM-Powered Analysis: Sends the summary to a fine-tuned Llama 3.1 model via Ollama for smart, context-aware fault diagnosis. Think of it as your AI assistant pondering, “Hmm, is this a short circuit?” 🤔
💾 Output Management: Saves results as neatly formatted, timestamped TXT files in the output folder, with a sneak peek in the console. 🖥️
📋 Logging: Keeps a detailed log (scada_fault_analysis.log) and prints updates to the console, so you’re never out of the loop! 🔎
🗂️ Directory Setup: Automatically creates prompts, data, and output folders to keep everything organized. 🧹

🛠️ How It Works
The SCADAFaultAnalyzer class is the heart of this project, orchestrating a seamless workflow. Here’s the step-by-step journey:

🚀 Initialization:

Sets up directories (prompts, data, output) to keep things tidy. 🗄️
Loads a customizable fault analysis prompt from prompts/fault_analysis_prompt.txt to guide the LLM. 📝
Configures Ollama’s API (running locally at http://localhost:11434 with Llama 3.1 8B) for optimal performance, including GPU settings for speed. ⚡


📥 Data Loading (load_scada_data):

Reads CSV files using Pandas, cleaning up column names (e.g., turning "Phase (A)" into "Phase_A"). 🧼
Sorts data by the time column (in seconds) to ensure chronological order. ⏳


🔬 Fault Analysis (analyze_fault_scenarios):

Counts total records and calculates the time range. 📈
Hunts for PICK UP and TRIP signals in columns containing '67', logging their frequency and first few timestamps. 🔔
Flags critical events when phase currents (>10A) or neutral currents (>5A) go wild, linking them to active signals. 🚨


📜 Summary Generation (generate_data_summary):

Crafts a readable text summary of the analysis, highlighting key stats and up to 5 critical events. 📄


🧠 LLM Analysis (analyze_with_ollama):

Inserts the summary into the prompt and sends it to Ollama’s API for a detailed fault interpretation. 🗣️
Handles errors gracefully, like reminding you to start the Ollama server if it’s not running. 😅


💾 Result Saving (save_results):

Writes the LLM’s insights to a timestamped file in the output folder, complete with a header showing the date and time. 🕰️


🏃 Full Pipeline (run_analysis):

Ties everything together for a single CSV file. The main function loops through all CSVs in data/, processing each one and printing previews. 🎥



The LLM is fine-tuned through clever prompt engineering in fault_analysis_prompt.txt, which guides the model to interpret SCADA data (e.g., linking current spikes to faults like short circuits ⚡ or ground faults 🌍). No training data is needed—the prompt does the heavy lifting! 💪
📋 Requirements

🐍 Python 3.10+: Install dependencies with:pip install pandas numpy requests


🦙 Ollama: Install from ollama.com, then:
Pull the model: ollama pull llama3.1:8b
Start the server: ollama serve (run in a separate terminal).


💻 Hardware: A GPU is recommended for faster LLM inference (configured with 10 GPU layers). 🖥️
📄 Input Files: Place SCADA data CSVs in the data folder (e.g., comtrade40_data.csv). Expected columns include time, IL1, IL2, IL3, Io, and signals like 67_Phase_PICK_UP.

🚀 Usage

Clone the repo:
git clone https://github.com/thesyzling/scada-fault-analyzer.git
cd scada-fault-analyzer


Set up your environment:

Create prompts/fault_analysis_prompt.txt with your custom prompt (e.g., instructions for fault diagnosis). 📝
Add CSV files to the data folder. 📂


Run the script:
python main.py


It processes all CSVs in data/, saves results in output/, and shows previews in the console. 🎉


Customize:

Tweak fault_analysis_prompt.txt to fine-tune the LLM’s reasoning. 🧠
Adjust Ollama settings in __init__ (e.g., temperature, num_ctx) for better performance. ⚙️



📄 Example Output
Here’s a taste of what you might see in the output folder:
## SCADA Arıza Analiz Raporu
## Tarih: 2025-08-15 21:50:00

Based on the data summary, a phase-to-ground short circuit in Phase A was detected at 0.1234s with a high IL1 current (12.5A) and 67_Phase_PICK_UP activation, followed by a TRIP at 0.1500s. Possible cause: insulation failure. Recommended action: inspect Phase A wiring. ⚡

⚠️ Limitations

Assumes specific column names in CSVs (e.g., IL1, 67_Phase_PICK_UP). Customize if needed. 🛠️
Hardcoded thresholds (10A for phase currents, 5A for neutral) may need adjustment. 📏
Requires a running Ollama server; no fallback to other models. 🦙
Batch processing only—no real-time monitoring. ⏰

🔒 Security Note
To keep things safe, we’ve included three sample input files (e.g., anonymized or synthetic CSVs) in the repository to showcase the tool’s capabilities without risking real SCADA data exposure. 🔐 These files simulate fault scenarios, ensuring you can test the tool securely. Always use anonymized or synthetic data in production to protect sensitive information! 🛡️
