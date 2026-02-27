# 🚀 AI Data Studio: Premium SaaS Data Workbench

**AI Data Studio** is a modern, high-performance web application designed to transform raw, messy data into clean, actionable insights. Powered by **Ollama (qwen3:1.7b)** and **Streamlit**, it provides a professional-grade workspace for data cleaning, transformation, and visualization.

![Version](https://img.shields.io/badge/version-2.0.0-22C55E)
![Python](https://img.shields.io/badge/python-3.9+-0E1117)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B)

## ✨ Core Features

- **💎 Premium SaaS UI**: A high-contrast Dark/Light theme dashboard with modular card-based architecture.
- **🚀 Magic Auto-Clean**: A robust, 3-step modular cleaning process (Duplicates, Gaps, Types) optimized for small LLMs.
- **🤖 AI Data Assistant**: Chat directly with your dataset using natural language to perform complex transformations.
- **📈 Viz Studio**: Generate stunning visualizations (Seaborn/Matplotlib) simply by describing what you want to see.
- **🔌 Ollama Integration**: Built-in health checks and diagnostic tools for local LLM connectivity.
- **📥 Direct Export**: One-click export of your cleaned data back to professional CSV format.

## 🛠️ Tech Stack

- **Frontend**: Streamlit (with Custom SaaS CSS)
- **Data Engine**: Pandas
- **AI Engine**: Ollama (Running `qwen3:1.7b`)
- **Plotting**: Matplotlib & Seaborn
- **API**: Requests (Localhost)

## 🏁 Getting Started

### 1. Prerequisites
- Python 3.9+
- [Ollama](https://ollama.ai/) installed and running.

### 2. Pull the Model
Open your terminal and run:
```bash
ollama pull qwen3:1.7b
```

### 3. Installation
Clone the repository and install dependencies:
```bash
git clone <your-repo-url>
cd CSV_cleaner
pip install -r requirements.txt
```

### 4. Run the App
```bash
streamlit run app.py
```

## 🛠️ Troubleshooting
If you encounter "Model Failure" or "Empty Response":
1. Ensure Ollama is running (`ollama serve`).
2. Use the **Test AI Connection** button in the app sidebar.
3. Enable **Debug Mode** to see raw AI logic and logs.

---
*Created with ❤️ for professional data engineers.*
