import streamlit as st
import pandas as pd
from pathlib import Path
from agent_core import LLMClient, review_application

# --- Page Config ---
st.set_page_config(
    page_title="Loan Review Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom plain background (light gray) ---
page_style = """
<style>
[data-testid="stAppViewContainer"] {
    background-color: #f5f7fa;
}
[data-testid="stHeader"] {
    background: rgba(0,0,0,0,0);
}
</style>
"""
st.markdown(page_style, unsafe_allow_html=True)

# --- Paths ---
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
APPS_CSV = DATA_DIR / "loan_applications.csv"
WATCHLIST_CSV = DATA_DIR / "kyc_watchlist.csv"

# --- Data Loader ---
@st.cache_data
def load_data():
    apps = pd.read_csv(APPS_CSV)
    watch = set(pd.read_csv(WATCHLIST_CSV)["nic"].tolist())
    return apps, watch

apps, watch = load_data()

# --- Title ---
st.title("🏦 Loan Application Review Assistant")
st.caption("AI-powered loan review with policy checks & transparent explanations.")

# --- Sidebar Controls ---
with st.sidebar:
    st.header("⚙️ Settings")
    st.dataframe(apps[["application_id", "full_name", "credit_score"]], height=200, use_container_width=True)
    app_id = st.selectbox("Select Application ID", apps["application_id"].tolist())
    model = st.text_input("Ollama model", value="tinyllama")
    use_retrieval = st.checkbox("Use policy retrieval (RAG)", value=True)
    run_btn = st.button("🚀 Run Review")

# --- Main Content ---
if run_btn:
    row = apps[apps["application_id"] == app_id].squeeze().to_dict()
    llm = LLMClient(model=model)

    policy_path = Path(__file__).resolve().parents[1] / "docs" / "policies" / "policy.md"
    result = review_application(
        row,
        watch,
        llm,
        use_retrieval=use_retrieval,
        policy_path=str(policy_path)
    )

    # --- Decision Summary ---
    st.subheader("✅ Decision Summary")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Recommended Action", result["recommended_action"])
    with c2:
        st.metric("Risk Score", f"{result['risk_score']*100:.1f}%")
    with c3:
        st.metric("Applicant ID", result["application_id"])

    # --- Policy Checks Table (colored) ---
    st.subheader("🔍 Policy Checks")
    checks_df = pd.DataFrame(result["checks"].items(), columns=["Check", "Status"])
    st.dataframe(
        checks_df.style.applymap(
            lambda v: "background-color: #d4edda;" if v=="PASS"
            else "background-color: #fff3cd;" if v=="WARN"
            else "background-color: #f8d7da;"
        ),
        use_container_width=True
    )

    # --- Explanations ---
    st.subheader("🧠 Decision Explanations")
    tab1, tab2 = st.tabs(["⚙️ Rule-based", "🧠 LLM"])
    with tab1:
        for r in result["reasons"]:
            st.markdown(f"- {r}")
    with tab2:
        st.markdown(
            f"""
            <div style="background-color:#ffffff; padding:20px; border-radius:12px;
                        box-shadow:0 4px 10px rgba(0,0,0,0.1); margin-top:10px;">
                <p style="font-size:16px; line-height:1.5;">{result['explanation']}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --- Download Decision Report ---
    st.download_button(
        "📥 Download Decision Report",
        data=result["explanation"],
        file_name=f"{app_id}_decision.txt",
        mime="text/plain"
    )
