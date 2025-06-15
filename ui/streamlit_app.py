import streamlit as st
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from local modules
sys.path.append(str(Path(__file__).parent.parent))

# Import page modules
from ui.pages.home import show_home_page
from ui.pages.scraper import show_scraper_page
from ui.pages.data_storage import show_data_storage_page
from ui.pages.playground import show_playground_page

def main():
    """Main multi-page Streamlit application."""
    st.set_page_config(
        page_title="VroomSniffer - Car Monitor", 
        page_icon="🚗", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
      # VroomSniffer Color Scheme CSS
    clean_css = """
    <style>
    /* VroomSniffer Color Palette:
    - Midnight Blue: #123C5A (primary)
    - Vibrant Orange: #F57C00 (accent/CTA)
    - Euro Green: #4CAF50 (success/deals)
    - Ice Blue: #D7E9F7 (backgrounds)
    - Graphite Gray: #333333 (text)
    - Soft Gray: #F4F4F4 (light backgrounds)
    */
    
    /* Hide Streamlit's default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Hide Streamlit's automatic navigation links */
    [data-testid="stSidebarNavLink"] {
        display: none !important;
    }
    
    /* Background and main styling */
    .stApp {
        background-color: #F4F4F4;
    }
    
    .main .block-container {
        background-color: white;
        padding: 2rem;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(18, 60, 90, 0.15);
        margin: 1rem auto;
        border: 1px solid #D7E9F7;
    }    /* Sidebar styling - Darker background */
    [data-testid="stSidebar"] {
        background-color: #123C5A !important;
    }
    
    [data-testid="stSidebar"] > div {
        background-color: #123C5A !important;
    }
    
    /* Sidebar text colors */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
      [data-testid="stSidebar"] .stMarkdown p {
        color: #D7E9F7 !important;
    }
    
    [data-testid="stSidebar"] .stCaption {
        color: #D7E9F7 !important;
        opacity: 0.8;
    }
      /* Sidebar buttons - White background for inactive buttons */
    [data-testid="stSidebar"] .stButton > button {
        background-color: #ffffff !important;
        color: #123C5A !important;
        border: 1px solid #D7E9F7 !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #D7E9F7 !important;
        border-color: #123C5A !important;
        color: #123C5A !important;
    }
    
    /* Active button styling - Orange for active buttons */
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #F57C00 !important;
        color: #ffffff !important;
        border-color: #F57C00 !important;
    }
    
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background-color: #E06500 !important;
        border-color: #E06500 !important;
    }
      /* Main content button styling */
    .stButton > button {
        border-radius: 6px;
        border: 1px solid #123C5A;
        background-color: white !important;
        color: #333333 !important;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: #D7E9F7 !important;
        border-color: #123C5A !important;
        color: #123C5A !important;
    }
      .stButton > button[kind="primary"] {
        background-color: white !important;
        color: #F57C00 !important;
        border-color: #F57C00 !important;
        font-weight: 600 !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #D7E9F7 !important;
        border-color: #F57C00 !important;
        color: #F57C00 !important;
    }
    
    /* Text input styling */
    .stTextInput > div > div > input {
        border-radius: 6px;
        border: 1px solid #D7E9F7;
        background-color: white;
        color: #333333;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #123C5A;
        box-shadow: 0 0 0 1px #123C5A;
    }
    
    /* Metrics styling */
    [data-testid="metric-container"] {
        background-color: #D7E9F7 !important;
        border: 1px solid #123C5A !important;
        border-radius: 6px !important;
        padding: 1rem !important;
    }
    
    /* Success/Info/Warning/Error styling */
    .stSuccess {
        background-color: #E8F5E8 !important;
        border-left: 4px solid #4CAF50 !important;
        color: #333333 !important;
    }
    
    .stInfo {
        background-color: #D7E9F7 !important;
        border-left: 4px solid #123C5A !important;
        color: #333333 !important;
    }
    
    .stWarning {
        background-color: #FFF3E0 !important;
        border-left: 4px solid #F57C00 !important;
        color: #333333 !important;
    }
    
    .stError {
        background-color: #FFEBEE !important;
        border-left: 4px solid #F44336 !important;
        color: #333333 !important;
    }    /* Metrics styling - no boxes, just text */
    [data-testid="metric-container"] {
        background-color: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 0.5rem !important;
        box-shadow: none !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #333333 !important;
    }
    
    /* Divider */
    hr {
        border-color: #D7E9F7;
    }
    
    /* Divider */
    hr {
        border-color: #e0e0e0;
    }
    </style>
    """
    st.markdown(clean_css, unsafe_allow_html=True)
      # Setup paths - use the same storage directory as scraper and CLI
    root_dir = Path(__file__).parent.parent
    storage_dir = root_dir / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    all_old_path = storage_dir / "all_old_results.json"
    latest_new_path = storage_dir / "latest_new_results.json"
    
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Home"
      # Sidebar navigation
    with st.sidebar:
        # Add VroomSniffer logo
        try:
            st.image("ui/resources/logo6.png", width=200)
        except:
            # Fallback if logo not found
            st.title("VroomSniffer")
        
        st.divider()
        
        # Navigation buttons
        if st.button("🏠 Home", key="nav_home", use_container_width=True, 
                    type="primary" if st.session_state.current_page == "🏠 Home" else "secondary"):
            st.session_state.current_page = "🏠 Home"
            st.rerun()
            
        if st.button("🔍 Scraper", key="nav_scraper", use_container_width=True, 
                    type="primary" if st.session_state.current_page == "🔍 Scraper" else "secondary"):
            st.session_state.current_page = "🔍 Scraper"
            st.rerun()
            
        if st.button("📊 Data Storage", key="nav_data", use_container_width=True, 
                    type="primary" if st.session_state.current_page == "📊 Data Storage" else "secondary"):
            st.session_state.current_page = "📊 Data Storage"
            st.rerun()
            
        if st.button("🎮 Playground", key="nav_playground", use_container_width=True, 
                    type="primary" if st.session_state.current_page == "🎮 Playground" else "secondary"):
            st.session_state.current_page = "🎮 Playground"
            st.rerun()
        
        st.divider()
        st.caption("VroomSniffer v1.0")
    
    # Page routing
    if st.session_state.current_page == "🏠 Home":
        show_home_page(all_old_path, latest_new_path)
    elif st.session_state.current_page == "🔍 Scraper":
        show_scraper_page(all_old_path, latest_new_path, root_dir)
    elif st.session_state.current_page == "📊 Data Storage":
        show_data_storage_page(all_old_path, latest_new_path)
    elif st.session_state.current_page == "🎮 Playground":
        show_playground_page(all_old_path, latest_new_path, root_dir)

if __name__ == "__main__":
    main()
