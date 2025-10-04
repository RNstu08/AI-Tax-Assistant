from __future__ import annotations

import streamlit as st

# --- Core App Modules ---
from app.knowledge.ingest import build_index
from app.memory.store import ProfileStore

# --- UI Component Render Functions ---
from app.ui.components.actions_panel import render_actions_panel
from app.ui.components.audit_panel import render_audit_panel
from app.ui.components.chat_panel import render_chat_panel
from app.ui.components.maintenance_panel import render_maintenance_panel
from app.ui.components.profile_panel import render_profile_panel
from app.ui.components.receipts_panel import render_receipts_panel
from app.ui.components.rules_panel import render_rules_panel
from app.ui.components.settings_panel import render_settings_panel
from app.ui.components.summary_panel import render_summary_panel
from app.ui.components.trace_panel import render_trace_panel

# --- UI Helper Functions ---


def _inject_custom_css():
    """Injects custom CSS for a polished, interactive UI with a 'moving bar' active tab style."""
    st.markdown(
        """
        <style>
            .main .block-container { background-color: #FFFFFF; padding-top: 2rem; }
            [data-testid="stSidebar"] { background-color: #1E1F26; }
            "[data-testid=\"stSidebar\"] h1, [data-testid=\"stSidebar\"] h2,
              .stMarkdown { color: #FAFAFA; }"
            ".sidebar-card { background-color: #262730; border: 1px solid #31333F; "
            "border-radius: 10px; padding: 1rem; margin-top: 1rem; }"

            /* --- Tab Styling for Vertical List --- */
            .sidebar-card button[data-baseweb="tab"] {
                background-color: transparent;
                border-radius: 8px;
                color: #a1a1a1;
                font-weight: 600;
                transition: all 0.2s;
                padding: 10px;
                margin-bottom: 5px;
                border-left: 3px solid transparent; /* Reserve space for the active bar */
            }
            .sidebar-card button[data-baseweb="tab"]:hover {
                background-color: #31333F;
                color: #FFFFFF;
            }
            /* --- NEW: "Moving Bar" Style for Active Tab --- */
            .sidebar-card button[data-baseweb="tab"][aria-selected="true"] {
                background-color: transparent; /* Remove background highlight */
                color: #0d6efd; /* Highlight text color */
                border-left: 3px solid #0d6efd; /* Add the 'moving bar' */
            }
        </style>""",
        unsafe_allow_html=True,
    )


def _sidebar_card_header(text: str, icon: str):
    """Creates a styled header for the card inside the sidebar."""
    header_html = (
        f'<div style="display: flex; align-items: center; border-bottom: 1px solid #31333F; '
        f'padding-bottom: 12px;"><span style="font-size: 1.5em; margin-right: 12px; '
        f'color: #0d6efd;">{icon}</span><h2 style="margin: 0; font-size: 1.25em;">'
        f"{text}</h2></div>"
    )
    return header_html


def _setup_sidebar():
    """Configures the sidebar with a single, continuous list of styled tabs."""
    with st.sidebar:

        st.markdown(
            """
            <div class='sidebar-card' style='text-align:center;'>
                <p style='color:#0d6efd; font-size:14px; font-family:sans-serif;
                        margin-bottom:0px;'>
                    <b>DE Tax Assistant</b>
                </p>
                <p style='color:#0d6efd; font-size:14px; font-family:sans-serif;
                        margin-bottom:0px;'>
                    <b>Welcome! Use tools below to review and manage your tax data</b>
                </p>
                ...
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(_sidebar_card_header("Assistant Tools", "🛠️"), unsafe_allow_html=True)

        all_tabs = [
            "Actions",
            "Summary",
            "Profile",
            "Receipts",
            "Trace",
            "Audit",
            "Rules",
            "Settings",
            "Maintenance",
        ]

        tabs = st.tabs(all_tabs)

        with tabs[0]:
            render_actions_panel(st.session_state.get("last_result"))
        with tabs[1]:
            render_summary_panel(st.session_state.get("last_result"))
        with tabs[2]:
            render_profile_panel(st.session_state.get("last_result"))
        with tabs[3]:
            render_receipts_panel(st.session_state.get("last_result"))
        with tabs[4]:
            render_trace_panel(st.session_state.get("last_result"))
        with tabs[5]:
            render_audit_panel(st.session_state.get("last_result"))
        with tabs[6]:
            render_rules_panel(st.session_state.get("last_result"))
        with tabs[7]:
            render_settings_panel(st.session_state.get("last_result"))
        with tabs[8]:
            render_maintenance_panel(st.session_state.get("last_result"))

        st.markdown("</div>", unsafe_allow_html=True)


# --- Core App Logic (remains the same) ---
@st.cache_resource
def startup() -> None:
    build_index()


@st.cache_resource
def get_store() -> ProfileStore:
    return ProfileStore(sqlite_path=".data/profile.db")


def main() -> None:
    st.set_page_config(
        page_title="DE Tax Assistant", layout="wide", initial_sidebar_state="expanded"
    )
    _inject_custom_css()
    _setup_sidebar()
    startup()
    if "last_result" not in st.session_state:
        st.session_state["last_result"] = None
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    st.set_page_config(page_title="DE Tax Assistant (MVP)", layout="wide")
    st.title("DE Tax Assistant (MVP)")
    st.markdown(
        "<div style='font-size:1em; margin-bottom:0.5em; margin-top:-0.5em;'>"
        "💬 Chat with Tax AI</div>",
        unsafe_allow_html=True,
    )
    render_chat_panel()


if __name__ == "__main__":
    main()
