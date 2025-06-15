import streamlit as st
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from local modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from services.vroomsniffer_service import get_cache_stats, load_cache

def show_home_page(all_old_path, latest_new_path):
    """Clean home page with simple design and clear navigation."""    
    st.title("VroomSniffer - Car Monitoring System")
    st.write("Monitor car listings with scraping, data management, and notifications")
    
    # Simple metrics
    try:
        stats = get_cache_stats(all_old_path)
        recent_listings = load_cache(latest_new_path) if latest_new_path else {}
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Listings", stats["total_listings"])
        with col2:
            st.metric("Recent Additions", len(recent_listings) if recent_listings else 0)
        with col3:
            cache_size_mb = stats.get('cache_size_mb', 0)
            if cache_size_mb > 0:
                st.metric("Cache Size", f"{cache_size_mb} MB")
            else:
                st.metric("Cache Size", "< 0.01 MB")
        
        with col4:
            # Show cache age instead of duplicate recent activity
            import os
            if all_old_path and os.path.exists(all_old_path):
                import time
                modified_time = os.path.getmtime(all_old_path)
                hours_ago = int((time.time() - modified_time) / 3600)
                if hours_ago == 0:
                    st.metric("Last Updated", "< 1 hour ago")
                elif hours_ago < 24:
                    st.metric("Last Updated", f"{hours_ago}h ago")
                else:
                    days_ago = hours_ago // 24
                    st.metric("Last Updated", f"{days_ago}d ago")
            else:
                st.metric("Last Updated", "Never")
        
        # Simple status message
        if stats["total_listings"] == 0:
            st.info("Getting Started: Use the Scraper to start collecting car listings!")
        else:
            st.success(f"You have {stats['total_listings']} cached listings ready to explore!")
            
    except Exception as e:
        st.error(f"Error loading stats: {str(e)}")
    
    st.divider()    # Simple navigation cards
    st.subheader("Quick Navigation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Car Scraper")
        st.write("Search & monitor car listings")
        st.write("• Manual scraping with URL inputs")
        st.write("• Real-time monitoring capabilities")
        st.write("• Telegram notifications")
        
        if st.button("Go to Scraper", type="primary", use_container_width=True):
            st.session_state.current_page = "🔍 Scraper"
            st.rerun()
    
    with col2:
        st.subheader("Data Storage")
        st.write("Analyze & manage your data")
        st.write("• Browse and search cached listings")
        st.write("• Advanced filtering and insights")
        st.write("• Cache management tools")
        
        if st.button("Go to Data Storage", type="primary", use_container_width=True):
            st.session_state.current_page = "📊 Data Storage"
            st.rerun()
    
    # Second row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Playground")
        st.write("Testing & experimentation")
        st.write("• Test scraping functionality")
        st.write("• Send test messages")
        st.write("• Debug and troubleshoot")
        
        if st.button("Go to Playground", type="secondary", use_container_width=True):
            st.session_state.current_page = "🎮 Playground"
            st.rerun()
    
    with col2:
        st.subheader("System Status")
        if stats.get("total_listings", 0) > 0:
            st.write("Your current data:")
            st.write(f"• {stats['total_listings']} total listings cached")
            if recent_listings:
                st.write(f"• {len(recent_listings)} recent additions")
            else:
                st.write("• No recent additions")
        else:
            st.write("Getting started:")
            st.write("1. Go to Scraper page")
            st.write("2. Enter a car listing URL")
            st.write("3. Start scraping listings")
            st.write("4. Analyze results in Data Storage")
