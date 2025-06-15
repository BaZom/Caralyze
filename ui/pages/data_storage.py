import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# Add the parent directory to the path so we can import from local modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from services.vroomsniffer_service import (
    get_cache_stats, 
    get_all_cached_listings, 
    get_listings_by_search_criteria,
    remove_listings_by_ids,
    clear_all_caches,
    show_statistics,
    manual_send_listings
)
from notifier.telegram import send_telegram_message, format_car_listing_message

def show_data_storage_page(all_old_path, latest_new_path):
    """Clean data storage page for managing cached listings."""
    
    st.title("Data Storage & Insights")
    st.write("Search, analyze, and manage your collected car listing data")
    
    # Check if we have data
    stats = get_cache_stats(all_old_path)
    if stats["total_listings"] == 0:
        st.warning("No cached data found")
        st.info("Use the Scraper page to collect some car listings first!")
        
        if st.button("Go to Scraper", type="primary"):
            st.session_state.current_page = "🔍 Scraper"
            st.rerun()
        return
    
    # Simple cache overview
    st.subheader("Cache Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    cache_size_mb = stats.get('cache_size_mb', 0)
    if cache_size_mb == 0:
        cache_size_bytes = stats.get('cache_size', 0)
        cache_size_mb = round(cache_size_bytes / (1024 * 1024), 2) if cache_size_bytes > 0 else 0
    
    filtered_count = len(st.session_state.get('current_filtered_listings', []))
    
    with col1:
        st.metric("Total Cached", stats["total_listings"])
    with col2:
        st.metric("Cache Size", f"{cache_size_mb} MB" if cache_size_mb > 0 else "< 0.01 MB")
    with col3:
        if 'current_filtered_listings' in st.session_state:
            st.metric("Filtered Results", filtered_count)
        else:
            st.metric("Filtered Results", "All")
    
    with col4:
        # Cache management button
        if st.button("🗑️ Clear All Cache", type="secondary"):
            if st.session_state.get('confirm_clear_all', False):
                result = clear_all_caches()
                st.success(result["message"])
                st.session_state.confirm_clear_all = False
                st.rerun()
            else:
                st.session_state.confirm_clear_all = True
                st.warning("⚠️ Click again to confirm")
    
    st.divider()
    
    # Main tabs
    tab1, tab2 = st.tabs(["🔍 Search & Browse", "📊 Insights & Analytics"])
    
    with tab1:
        # Search and filter interface
        st.subheader("🔍 Search & Filter Listings")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            search_term = st.text_input("Search Title/Location", placeholder="e.g., BMW, Berlin")
        with col2:
            min_price = st.number_input("Min Price (€)", min_value=0, value=None, step=1000)
        with col3:
            max_price = st.number_input("Max Price (€)", min_value=0, value=None, step=1000)
        with col4:
            if st.button("🔍 Apply Filters", type="primary"):
                # Apply filters and update session state
                filtered_listings = get_listings_by_search_criteria(
                    all_old_path, 
                    search_term=search_term if search_term else None,
                    min_price=min_price,
                    max_price=max_price
                )
                st.session_state.current_filtered_listings = filtered_listings
                st.rerun()
        
        # Clear filters button
        if 'current_filtered_listings' in st.session_state:
            if st.button("🔄 Clear Filters", type="secondary"):
                del st.session_state.current_filtered_listings
                st.rerun()
        
        # Display filtered results
        if 'current_filtered_listings' in st.session_state:
            filtered_listings = st.session_state.current_filtered_listings
        else:
            # Show all listings by default
            filtered_listings = get_all_cached_listings(all_old_path)
        
        if filtered_listings:
            st.info(f"📋 Showing {len(filtered_listings)} listings")
            
            # Create DataFrame for display
            listings_data = []
            for listing in filtered_listings:
                listings_data.append({
                    "Select": False,
                    "Title": listing.get("Title", "N/A")[:60] + "..." if len(listing.get("Title", "")) > 60 else listing.get("Title", "N/A"),
                    "Price": listing.get("Price", "N/A"),
                    "Location": listing.get("Location", "N/A"),
                    "Posted": listing.get("Posted", "N/A"),
                    "URL": listing.get("URL", "N/A")
                })
            
            df = pd.DataFrame(listings_data)
            
            # Interactive table
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="fixed",
                disabled=["Title", "Price", "Location", "Posted", "URL"],
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select listings for actions",
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
            
            # Handle selected items
            selected_urls = []
            selected_listings = []
            for idx, row in edited_df.iterrows():
                if row["Select"]:
                    selected_urls.append(row["URL"])
                    for listing in filtered_listings:
                        if listing.get("URL") == row["URL"]:
                            selected_listings.append(listing)
                            break
            
            # Action buttons for selected items
            if selected_urls:
                st.subheader(f"🎯 Actions for {len(selected_urls)} selected listings")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button(f"🗑️ Remove Selected", type="secondary"):
                        removed_count = remove_listings_by_ids(selected_urls, all_old_path)
                        st.success(f"✅ Removed {removed_count} listings from cache")
                        # Clear filtered listings to refresh
                        if 'current_filtered_listings' in st.session_state:
                            del st.session_state.current_filtered_listings
                        st.rerun()
                
                with col2:
                    if st.button(f"📤 Send to Telegram", type="primary"):
                        with st.spinner(f"Sending {len(selected_listings)} listings..."):
                            try:
                                success_count, failed = manual_send_listings(
                                    selected_listings,
                                    send_telegram_message=send_telegram_message,
                                    format_car_listing_message=format_car_listing_message,
                                    parse_mode="HTML",
                                    retry_on_network_error=True
                                )
                                if success_count > 0:
                                    st.success(f"✅ Sent {success_count}/{len(selected_listings)} listings!")
                                if failed:
                                    st.error(f"❌ Failed to send {len(failed)} listings!")
                            except Exception as e:
                                st.error(f"❌ Failed to send messages: {str(e)}")
                
                with col3:
                    if st.button(f"📊 Analyze Selected", type="secondary"):
                        # Store selected listings for analysis
                        st.session_state.analysis_listings = selected_listings
                        st.success(f"✅ {len(selected_listings)} listings ready for analysis")
                        st.info("👉 Check the 'Insights & Analytics' tab")
                
                with col4:
                    st.info(f"Selected: {len(selected_urls)} listings")
        else:
            st.info("No listings match your search criteria.")
    
    with tab2:
        # Analytics and insights
        st.subheader("📊 Data Insights & Analytics")
        
        # Determine which listings to analyze
        if 'analysis_listings' in st.session_state and st.session_state.analysis_listings:
            analysis_listings = st.session_state.analysis_listings
            st.info(f"📊 Analytics based on {len(analysis_listings)} selected listings")
            
            if st.button("🔄 Reset to All Listings"):
                del st.session_state.analysis_listings
                st.rerun()
                
        elif 'current_filtered_listings' in st.session_state and st.session_state.current_filtered_listings:
            analysis_listings = st.session_state.current_filtered_listings
            st.info(f"📊 Analytics based on {len(analysis_listings)} filtered results")
        else:
            analysis_listings = get_all_cached_listings(all_old_path)
            st.info(f"📊 Analytics based on all {len(analysis_listings)} cached listings")
        
        if analysis_listings:
            # Show detailed statistics
            avg_price, total_count, prices = show_statistics(analysis_listings)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Average Price", f"€{avg_price:,}" if avg_price > 0 else "N/A")
            with col2:
                st.metric("Price Range", f"€{min(prices):,} - €{max(prices):,}" if prices else "N/A")
            with col3:
                st.metric("Data Points", f"{total_count:,}")
            with col4:
                median_price = sorted(prices)[len(prices)//2] if prices else 0
                st.metric("Median Price", f"€{median_price:,}" if median_price > 0 else "N/A")
            
            # Price distribution chart
            if prices:
                st.subheader("💰 Price Distribution")
                df_prices = pd.DataFrame({"Price": prices})
                
                # Create bins for better visualization
                bins = 20
                hist_data = pd.cut(df_prices["Price"], bins=bins, include_lowest=True)
                hist_counts = hist_data.value_counts().sort_index()
                
                # Convert to chart-friendly format
                chart_data = pd.DataFrame({
                    'Price Range': [f"€{int(interval.left):,}-€{int(interval.right):,}" for interval in hist_counts.index],
                    'Count': hist_counts.values
                })
                
                st.bar_chart(chart_data.set_index('Price Range'))
            
            # Additional insights
            st.subheader("🔍 Additional Insights")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Location analysis
                locations = {}
                for listing in analysis_listings:
                    location = listing.get("Location", "Unknown")
                    locations[location] = locations.get(location, 0) + 1
                
                if locations:
                    st.write("**Top Locations:**")
                    sorted_locations = sorted(locations.items(), key=lambda x: x[1], reverse=True)[:10]
                    for location, count in sorted_locations:
                        st.write(f"• {location}: {count} listings")
            
            with col2:
                # Price categories
                if prices:
                    low_price = len([p for p in prices if p < 10000])
                    mid_price = len([p for p in prices if 10000 <= p < 25000])
                    high_price = len([p for p in prices if p >= 25000])
                    
                    st.write("**Price Categories:**")
                    st.write(f"• Budget (< €10k): {low_price} listings")
                    st.write(f"• Mid-range (€10k-€25k): {mid_price} listings")
                    st.write(f"• Premium (> €25k): {high_price} listings")
        else:
            st.info("No data available for analytics")
