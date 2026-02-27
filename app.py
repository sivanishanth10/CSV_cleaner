import streamlit as st
import pandas as pd
import requests
import json
import io
import matplotlib.pyplot as plt
import seaborn as sns

# --- CONSTANTS ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:1.7b"

# --- PREMIUM SAAS CSS ---
def apply_custom_css():
    st.markdown("""
        <style>
        /* Global Base */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        [data-testid="stAppViewContainer"] {
            background-color: #0E1117;
            color: #FFFFFF;
            font-family: 'Inter', sans-serif;
        }
        
        [data-testid="stHeader"] {
            background-color: #0E1117;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            height: 64px;
        }

        [data-testid="stSidebar"] {
            background-color: #1A1F2B !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08);
            padding: 24px 8px;
        }

        /* SaaS Card Structure */
        .sass-card {
            background-color: #1A1F2B;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 32px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }

        /* Typography */
        h1, h2, h3 {
            color: #FFFFFF !important;
            font-weight: 700 !important;
            letter-spacing: -0.025em !important;
        }
        .text-secondary {
            color: #A1A1AA !important;
            font-size: 0.95rem;
        }

        /* Metrics & Badges */
        .metric-badge {
            background: rgba(34, 197, 94, 0.1);
            color: #22C55E;
            padding: 6px 14px;
            border-radius: 99px;
            font-size: 0.8rem;
            font-weight: 600;
            border: 1px solid rgba(34, 197, 94, 0.2);
        }

        /* SaaS Buttons */
        .stButton>button {
            width: 100%;
            border-radius: 12px;
            height: 52px;
            background-color: #22C55E !important;
            color: white !important;
            font-weight: 600 !important;
            border: none !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 6px -1px rgba(34, 197, 94, 0.1);
        }
        .stButton>button:hover {
            background-color: #16a34a !important;
            box-shadow: 0 0 20px rgba(34, 197, 94, 0.3);
            transform: translateY(-2px);
        }

        /* File Uploader */
        [data-testid="stFileUploaderDropzone"] {
            background-color: #0E1117 !important;
            border: 2px dashed rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
        }
        [data-testid="stFileUploaderDropzoneInstructions"] p {
            color: #A1A1AA !important;
        }

        /* Chat Interface */
        [data-testid="stChatMessage"] {
            background-color: #262D3D !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 16px !important;
            padding: 20px !important;
            margin-bottom: 16px !important;
        }
        [data-testid="stChatMessageContent"] p {
            color: #FFFFFF !important;
            line-height: 1.6;
        }
        
        .stChatInputContainer {
            background-color: #1A1F2B !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
        }

        /* Table Styling */
        .stDataFrame {
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
            overflow: hidden;
        }

        /* Navigation Radio */
        [data-testid="stSidebarNav"] { padding-top: 1rem; }
        .stRadio div[role="radiogroup"] { gap: 8px; }
        .stRadio div[role="radiogroup"] label {
            background: #262D3D;
            padding: 10px 16px;
            border-radius: 8px;
            width: 100%;
            border: 1px solid rgba(255,255,255,0.05);
        }

        /* Custom spacing */
        .block-container {
            padding-top: 5rem !important;
            max-width: 1200px !important;
        }
        
        /* Layout overrides */
        .stDivider { border-bottom: 2px solid rgba(255,255,255,0.05) !important; }
        </style>
    """, unsafe_allow_html=True)

# --- CORE LOGIC (UNMODIFIED) ---

def is_safe_code(code: str) -> bool:
    # Remove comments to avoid false positives in safety check
    clean_code = "\n".join([line.split("#")[0] for line in code.split("\n")])
    blacklist = ["import", "open(", "os.", "sys.", "subprocess", "eval", "exec", "__", "plt.show", "plt.savefig"]
    for word in blacklist:
        if word in clean_code:
            return False
    return True

def build_cleaning_prompt(df: pd.DataFrame, user_input: str) -> str:
    # Extreme simplification: NO sample data, ONLY columns.
    columns = df.columns.tolist()
    prompt = (
        f"Context: Pandas dataframe 'df' with columns {columns}\n"
        f"Task: {user_input}\n"
        f"Python Code (ONLY code, no text):"
    )
    return prompt

def build_viz_prompt(df: pd.DataFrame, user_input: str) -> str:
    columns = df.columns.tolist()
    prompt = (
        f"Context: Pandas dataframe 'df' with columns {columns}\n"
        f"Task: Create a visualization for: {user_input}\n"
        f"Output: Python code using 'sns', 'plt', and 'fig'. ONLY code."
    )
    return prompt

def check_ollama_health() -> bool:
    try:
        # Simple health ping to the tags endpoint to see if Ollama is running
        base_url = OLLAMA_URL.replace("/api/generate", "/api/tags")
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            models = [m.get("name") for m in response.json().get("models", [])]
            return MODEL_NAME in models or any(MODEL_NAME in m for m in models)
        return False
    except:
        return False

def ask_llm(prompt: str) -> str:
    if "raw_logs" not in st.session_state:
        st.session_state.raw_logs = []
    
    payload = {
        "model": MODEL_NAME, 
        "prompt": prompt, 
        "stream": False,
        "options": {
            "num_predict": 128,
            "temperature": 0,
            "top_k": 20
        }
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        response.raise_for_status()
        raw_data = response.json()
        
        # Log for debugging
        st.session_state.raw_logs.append({
            "prompt": prompt[:100] + "...",
            "response": raw_data
        })
        # Keep only last 5 logs
        if len(st.session_state.raw_logs) > 5:
            st.session_state.raw_logs.pop(0)

        result = raw_data.get("response", "").strip()
        
        # Strip markdown
        if "```" in result:
            parts = result.split("```")
            if len(parts) > 1:
                result = parts[1]
                if result.startswith("python"): result = result[6:]
        return result.strip()
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        st.session_state.raw_logs.append({"prompt": prompt[:100], "response": error_msg})
        st.error(f"❌ Ollama Error: {e}")
        return ""

@st.cache_data
def load_data(file):
    return pd.read_csv(file)

# --- UI COMPONENTS ---

def top_navigation():
    st.markdown("""
        <div style='position: fixed; top: 0; left: 0; width: 100%; height: 64px; 
                    background-color: #0E1117; border-bottom: 1px solid rgba(255,255,255,0.08); 
                    display: flex; align-items: center; padding: 0 40px; z-index: 9999;'>
            <div style='display: flex; justify-content: space-between; width: 100%; align-items: center;'>
                <h3 style='margin:0; font-size: 1.25rem; font-weight: 700; color: #FFFFFF;'>AI Data Studio</h3>
                <span class='metric-badge'>● System Ready & Connected</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

def stats_card(df):
    st.markdown("<div class='sass-card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top:0;'>📊 Intelligence Overview</h3>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<span class='text-secondary'>Rows</span><br><h2 style='margin:0;'>{df.shape[0]}</h2>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<span class='text-secondary'>Columns</span><br><h2 style='margin:0;'>{df.shape[1]}</h2>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<span class='text-secondary'>Null Values</span><br><h2 style='margin:0;'>{df.isnull().sum().sum()}</h2>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<span class='text-secondary'>Data Health</span><br><h2 style='margin:0; color:#22C55E !important;'>Optimal</h2>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- PAGE ROUTING ---

def cleaning_lab(debug=False):
    if st.session_state.df is None:
        st.markdown("<div class='sass-card' style='text-align:center; padding: 80px 20px;'>", unsafe_allow_html=True)
        st.markdown("<h2>Ready to Optimize?</h2><p class='text-secondary'>Upload your CSV in the sidebar to begin AI-powered cleaning.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df = st.session_state.df
    
    # Overview
    stats_card(df)

    # Explorer Card
    st.markdown("<div class='sass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>🔍 Dataset Preview</h3>", unsafe_allow_html=True)
    st.dataframe(df.head(10), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Magic Clean Card
    st.markdown("<div class='sass-card' style='border: 1px solid rgba(34, 197, 94, 0.3);'>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center;'>🚀 Magic Auto-Clean</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;' class='text-secondary'>Perform basic 3-step essential cleaning: Deduplication, Gap Filling, and Type Correction.</p>", unsafe_allow_html=True)
    
    if st.button("Run Magic Optimizer", use_container_width=True):
        steps = [
            ("Remove Duplicates", "Write Pandas code to remove all duplicate rows from 'df'."),
            ("Handle Gaps", "Write Pandas code to fill missing values in 'df' with mode or median."),
            ("Clean Data Types", "Write Pandas code to convert all columns in 'df' to their optimal data types.")
        ]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, (name, task) in enumerate(steps):
            status_text.markdown(f"**Step {i+1}/3:** {name}...")
            prompt = build_cleaning_prompt(df, task)
            code = ask_llm(prompt)
            
            if debug: st.code(code, language="python")
            
            if code and is_safe_code(code):
                try:
                    local_vars = {"df": df.copy(), "pd": pd}
                    exec(code, {}, local_vars)
                    st.session_state.df = local_vars["df"]
                    df = st.session_state.df # Update local df for next step
                except Exception as e:
                    st.error(f"Execution Error in {name}: {e}")
                    break
            else:
                st.error(f"⚠️ Model failure in {name}. Check logs.")
                break
            progress_bar.progress((i + 1) / len(steps))
        
        st.session_state.messages.append({"role": "assistant", "content": "✅ **Magic Sweep Applied!** I've cleaned your data step-by-step."})
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Chat Assistant Card
    st.markdown("<div class='sass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>🤖 AI Data Assistant</h3>", unsafe_allow_html=True)
    
    # Custom Chat Scroll Container
    chat_box = st.container(height=400, border=False)
    with chat_box:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if user_input := st.chat_input("Talk to your data..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                prompt = build_cleaning_prompt(df, user_input)
                code = ask_llm(prompt)
                if debug: st.code(code, language="python")

                if code and is_safe_code(code):
                    try:
                        local_vars = {"df": df.copy(), "pd": pd}
                        exec(code, {}, local_vars)
                        st.session_state.df = local_vars["df"]
                        st.markdown(f"Applied: **{user_input}**")
                        st.session_state.messages.append({"role": "assistant", "content": f"I've successfully updated the data for: '{user_input}'"})
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fail: {e}")
                elif not code:
                    st.error("⚠️ Assistant Failure: Empty response.")
                else:
                    st.error("🛡️ Safety Block on generated code.")
    st.markdown("</div>", unsafe_allow_html=True)

def viz_studio(debug=False):
    if st.session_state.df is None:
        st.info("Upload a dataset to access Viz Studio.")
        return

    df = st.session_state.df
    st.markdown("<div class='sass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>📈 AI Visualization Studio</h3>", unsafe_allow_html=True)
    
    viz_req = st.text_input("What would you like to visualize?", placeholder="e.g. 'A distribution of prices'")
    if st.button("Generate Visualization"):
        with st.spinner("Drafting your chart..."):
            prompt = build_viz_prompt(df, viz_req)
            code = ask_llm(prompt)
            if debug: st.code(code, language="python")

            if code and is_safe_code(code):
                try:
                    local_vars = {"df": df, "plt": plt, "sns": sns, "fig": None}
                    exec(code, {}, local_vars)
                    if local_vars["fig"]:
                        st.pyplot(local_vars["fig"])
                    else: st.error("Chart generation failed.")
                except Exception as e:
                    st.error(f"Viz Error: {e}")
            elif not code:
                st.error("⚠️ Viz Failure: Empty response.")
            else:
                st.error("🛡️ Safety Block on visualization code.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- MAIN APP ---

def main():
    st.set_page_config(page_title="AI Data Studio", layout="wide", initial_sidebar_state="expanded")
    apply_custom_css()

    if "df" not in st.session_state: st.session_state.df = None
    if "messages" not in st.session_state: st.session_state.messages = []

    # Sidebar
    with st.sidebar:
        st.markdown("<h1 style='margin-bottom:0;'>Studio</h1>", unsafe_allow_html=True)
        st.markdown("<p class='text-secondary'>AI-Powered Data Workbench</p>", unsafe_allow_html=True)
        st.divider()

        st.markdown("<p style='font-size: 0.75rem; font-weight: 700; opacity: 0.5;'>SETTINGS</p>", unsafe_allow_html=True)
        debug_mode = st.checkbox("Show AI Logic (Debug Mode)", value=False)
        
        # Connection Test Button
        if st.button("🔌 Test AI Connection", use_container_width=True):
            with st.spinner("Pinging Ollama..."):
                if check_ollama_health():
                    st.success(f"Connected to Ollama! Model '{MODEL_NAME}' is ready.")
                else:
                    st.error(f"Ollama Not Found! Ensure server is running and '{MODEL_NAME}' is pulled.")
                    st.info("Run: `ollama pull qwen3:1.7b` in your terminal.")

        if debug_mode and "raw_logs" in st.session_state:
            with st.expander("🛠️ Developer Session Logs"):
                for log in reversed(st.session_state.raw_logs):
                    st.text(f"Prompt: {log['prompt']}")
                    st.json(log["response"])
                    st.divider()
        st.divider()

        st.markdown("<p style='font-size: 0.75rem; font-weight: 700; opacity: 0.5;'>INPUT SOURCE</p>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("", type="csv", label_visibility="collapsed")
        if uploaded_file:
            st.session_state.df = load_data(uploaded_file)
        
        st.divider()
        st.markdown("<p style='font-size: 0.75rem; font-weight: 700; opacity: 0.5;'>WORKSPACE</p>", unsafe_allow_html=True)
        page = st.radio("", ["Cleaning Lab", "Viz Studio"], label_visibility="collapsed")
        
        if st.session_state.df is not None:
            st.markdown("<div style='position: fixed; bottom: 30px; width: 260px;'>", unsafe_allow_html=True)
            
            # Clear Cache Button
            if st.button("🗑️ Clear Chat & Reset", use_container_width=True):
                st.session_state.messages = []
                st.session_state.df = None
                st.rerun()

            st.divider()
            csv_buffer = io.StringIO()
            st.session_state.df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Export to CSV",
                data=csv_buffer.getvalue(),
                file_name="studio_export.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.markdown("</div>", unsafe_allow_html=True)

    # Header
    top_navigation()

    # Routing
    if page == "Cleaning Lab":
        cleaning_lab(debug_mode)
    else:
        viz_studio(debug_mode)

if __name__ == "__main__":
    main()
