"""
Cache management UI components for Streamlit
"""
import streamlit as st
import pandas as pd
from pathlib import Path
from services.vroomsniffer_service import (
    get_all_cached_listings,
    remove_listings_by_ids,
    clear_cache,
    get_cache_stats,
    get_listings_by_search_criteria,
    clear_all_caches
)

def display_cache_management(cache_path):
    """Display cache management interface"""
    st.subheader("🗂️ Cache Management")
    
    # Get cache statistics
    stats = get_cache_stats(cache_path)
    
    # Top row: Stats and Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.metric("Total Cached Listings", stats["total_listings"])
        cache_size_mb = stats.get('cache_size_mb', 0)
        if cache_size_mb > 0:
            st.caption(f"Cache size: {cache_size_mb} MB")
        else:
            # Calculate size properly if not returned
            cache_size_bytes = stats.get('cache_size', 0)
            if cache_size_bytes > 0:
                cache_size_mb = round(cache_size_bytes / (1024 * 1024), 2)
                st.caption(f"Cache size: {cache_size_mb} MB")
            else:
                st.caption("Cache size: < 0.01 MB")
    
    with col2:
        if st.button("🔄 Refresh", type="secondary", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear All", type="secondary", use_container_width=True):
            if st.session_state.get('confirm_clear_cache', False):
                result = clear_all_caches()
                st.success(result["message"])
                st.session_state.confirm_clear_cache = False
                # Clear any cached session state data
                for key in list(st.session_state.keys()):
                    if 'cache' in key.lower():
                        del st.session_state[key]
                st.rerun()
            else:
                st.session_state.confirm_clear_cache = True
                st.warning("⚠️ Click again to confirm clearing all caches")
    
    if stats["total_listings"] == 0:
        st.info("No cached listings found.")
        return
    
    # Search and filter options
    st.subheader("🔍 Search & Filter Cached Listings")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input("Search in Title/Location", placeholder="e.g., BMW, Berlin")
    with col2:
        min_price = st.number_input("Min Price (€)", min_value=0, value=None, step=1000)
    with col3:
        max_price = st.number_input("Max Price (€)", min_value=0, value=None, step=1000)
    
    # Get filtered listings
    filtered_listings = get_listings_by_search_criteria(
        cache_path, 
        search_term=search_term if search_term else None,
        min_price=min_price,
        max_price=max_price
    )
    
    if not filtered_listings:
        st.info("No listings match your search criteria.")
        return
    
    st.subheader(f"📋 Cached Listings ({len(filtered_listings)} found)")
    
    # Create a dataframe for display
    listings_data = []
    for listing in filtered_listings:
        listings_data.append({
            "Select": False,
            "Title": listing.get("Title", "N/A")[:50] + "..." if len(listing.get("Title", "")) > 50 else listing.get("Title", "N/A"),
            "Price": listing.get("Price", "N/A"),
            "Location": listing.get("Location", "N/A"),
            "Posted": listing.get("Posted", "N/A"),
            "URL": listing.get("URL", "N/A")
        })
    
    if not listings_data:
        st.info("No listings to display.")
        return
    
    # Display listings with selection
    df = pd.DataFrame(listings_data)
    
    # Use data editor for selection
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="fixed",
        disabled=["Title", "Price", "Location", "Posted", "URL"],
        column_config={
            "Select": st.column_config.CheckboxColumn(
                "Select",
                help="Select listings to remove",
                default=False,
            ),
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Price": st.column_config.TextColumn("Price", width="small"),
            "Location": st.column_config.TextColumn("Location", width="medium"),
            "Posted": st.column_config.TextColumn("Posted", width="small"),
            "URL": st.column_config.LinkColumn("URL", width="small")
        },
        hide_index=True,
    )
    
    # Remove selected listings
    selected_urls = []
    for idx, row in edited_df.iterrows():
        if row["Select"]:
            selected_urls.append(row["URL"])
    
    if selected_urls:
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button(f"🗑️ Remove {len(selected_urls)} Selected", type="primary"):
                removed_count = remove_listings_by_ids(selected_urls, cache_path)
                st.success(f"✅ Removed {removed_count} listings from cache")
                # Clear cache-related session state
                for key in list(st.session_state.keys()):
                    if 'cache' in key.lower():
                        del st.session_state[key]
                st.rerun()
        with col2:
            st.write(f"Selected {len(selected_urls)} listings for removal")

def display_cache_summary(cache_path):
    """Display a compact cache summary"""
    stats = get_cache_stats(cache_path)
    
    if stats["total_listings"] > 0:
        st.sidebar.success(f"📊 Cache: {stats['total_listings']} listings")
        
        # Quick actions in sidebar
        if st.sidebar.button("🗂️ Manage Cache"):
            st.session_state.show_cache_management = True
            
        if st.sidebar.button("🗑️ Quick Clear"):
            if st.sidebar.button("⚠️ Confirm Clear", type="secondary"):
                clear_cache(cache_path)
                st.sidebar.success("Cache cleared!")
                st.rerun()
    else:
        st.sidebar.info("📊 Cache: Empty")
