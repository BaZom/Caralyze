import streamlit as st
import sys
import json
import time
from pathlib import Path

# Add the parent directory to the path so we can import from local modules
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import services via the provider pattern
from providers.services_provider import (
    get_storage_service,
    get_url_pool_service,
    get_scraper_service,
    get_notification_service,
    get_scheduler_service
)

# Import UI components
from ui.components.sound_effects import play_sound
from ui.components.ui_components import display_scrape_results
from ui.components.metrics import display_metrics_row
from ui.components.state_management import initialize_scraper_state
from ui.components.styles import get_main_styles
from ui.components.telegram_controls import send_listings_to_telegram
from ui.components.url_management import display_url_management
from ui.components.scraper_controls import display_scraper_controls, display_scraper_progress

# Initialize services via the provider
storage_service = get_storage_service()
notification_service = get_notification_service()
scraper_service = get_scraper_service()
url_pool_service = get_url_pool_service()
scheduler_service = get_scheduler_service()

def _show_system_status():
    """Display simplified system status."""
    st.subheader("System Status")
    
    # Get minimal data
    try:
        import os
        
        # Get cache stats from session state paths
        all_old_path = st.session_state.get('all_old_path')
        latest_new_path = st.session_state.get('latest_new_path')
        
        total_listings = 0
        recent_additions = 0
        
        if all_old_path and os.path.exists(all_old_path):
            stats = storage_service.get_cache_stats(all_old_path)
            total_listings = stats.get('total_listings', 0)
        
        if latest_new_path and os.path.exists(latest_new_path):
            recent_data = storage_service.load_cache(latest_new_path)
            recent_additions = len(recent_data) if recent_data else 0
            
    except Exception:
        total_listings = 0
        recent_additions = 0

    # Simplified metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Listings", total_listings)
    with col2:
        st.metric("Recent New", recent_additions)
    with col3:
        st.metric("Runs", scheduler_service.get_total_runs())
        
    # Simple status message
    status = "Active" if scheduler_service.is_scraping_active() else "Stopped"
    st.caption(f"Status: {status} | URLs: {len(st.session_state.url_pool)}")

def show_scraper_page(all_old_path, latest_new_path, root_dir):
    """Multi-URL scraper with clean interface."""
    
    # Store paths in session state for status function
    st.session_state.all_old_path = all_old_path
    st.session_state.latest_new_path = latest_new_path
    
    # Apply centralized styles from components
    st.markdown(get_main_styles(), unsafe_allow_html=True)
    
    # Use the state management component for consistent initialization
    initialize_scraper_state(url_pool_service)
    
    # Additional state specific to this page
    if 'scraping_active' not in st.session_state:
        st.session_state.scraping_active = scheduler_service.is_scraping_active()
        
    # Synchronize session state with scheduler service
    if 'scheduler_initialized' not in st.session_state:
        # This is the first time loading - get default values from scheduler
        st.session_state.scheduler_initialized = True
    elif 'total_runs' in st.session_state:
        # This is a reload - set scheduler state from session
        scheduler_service.set_total_runs(st.session_state.total_runs)
      # Let scheduler handle next URL selection
    if scheduler_service.is_scraping_active() and st.session_state.url_pool:
        if not scheduler_service.is_next_url_selected() or scheduler_service.get_next_url_index() >= len(st.session_state.url_pool):
            # Use random or sequential selection based on user preference
            random_selection = st.session_state.get('random_url_selection', True)
            scheduler_service.select_next_url_index(
                url_count=len(st.session_state.url_pool),
                random_selection=random_selection,
                current_run=scheduler_service.get_total_runs()
            )
    
    # System Status
    _show_system_status()
    
    st.divider()
    
    # URL Management using component
    url_pool_modified = display_url_management(url_pool_service, scheduler_service)
    if url_pool_modified:
        st.rerun()  # Refresh the UI if URLs were modified
    
    st.divider()
    
    # Controls using component
    controls_changed = display_scraper_controls(scheduler_service)
    if controls_changed:
        st.rerun()  # Refresh the UI if controls were changed
    
    # Active Scraping Logic
    if scheduler_service.is_scraping_active() and st.session_state.url_pool:
        if scheduler_service.is_time_to_scrape():
            current_time = time.time()
            
            # Use pre-selected URL from scheduler
            next_url_index = scheduler_service.get_next_url_index()
            if next_url_index < len(st.session_state.url_pool):
                current_url_index = next_url_index
            else:
                current_url_index = 0
            
            current_url = st.session_state.url_pool[current_url_index]
            
            # Create status containers for progress updates
            scrape_status = st.empty()
            scrape_progress_bar = st.empty()
            message_status = st.empty()
            result_status = st.empty()
            
            # Get URL description if available
            url_description = ""
            url_data = url_pool_service.get_url_data()
            if current_url in url_data:
                url_description = url_data[current_url].get('description', '')
                
            # Scraping phase
            scrape_header = f"URL #{current_url_index + 1} of {len(st.session_state.url_pool)}: {current_url[:50]}..."
            if url_description:
                scrape_header = f"{url_description} - {scrape_header}"
                
            scrape_status.info(f"🔍 Scraping {scrape_header}")
            scrape_progress_bar.progress(0, text="Starting scraper engine...")
            filters = {"custom_url": current_url}
            
            try:
                # Update progress to show initialization
                scrape_progress_bar.progress(0.2, text="🔄 Initializing scraper...")
                # Define progress callback
                def scraper_progress_callback(step, message, progress_value):
                    scrape_progress_bar.progress(progress_value, text=f"🔍 {message}")
                
                # Use our ScraperService instance from the module level
                results = scraper_service.get_listings_for_filter(
                    filters,
                    url_pool_service.build_search_url_from_custom,
                    all_old_path, 
                    latest_new_path,
                    root_dir,
                    progress_callback=scraper_progress_callback
                )
                
                all_listings, new_listings = results
                
                # Simplified status updates
                if all_listings:
                    source_info = f"URL #{current_url_index + 1}"
                    if url_description:
                        source_info = f"{url_description}"
                    
                    scrape_status.success(f"Found {len(all_listings)} listings ({len(new_listings)} new)")
                    scrape_progress_bar.progress(1.0)
                else:
                    scrape_status.warning(f"No listings found")
                    scrape_progress_bar.progress(1.0)
                
                # Play sound when new listings are found
                if new_listings:
                    play_sound("Sniff1.wav")
                
                st.session_state.latest_results = {
                    'all_listings': all_listings,
                    'new_listings': new_listings,
                    'timestamp': current_time,
                    'url': current_url,
                    'url_index': current_url_index,
                    'url_description': url_description
                }
                
                # Auto-send if enabled (simplified)
                if st.session_state.auto_send_active and new_listings:
                    # Update status
                    message_status.info(f"Sending {len(new_listings)} notifications...")
                    
                    # Add source URL information for notifications
                    for listing in new_listings:
                        if 'source_url' not in listing:
                            listing['source_url'] = current_url
                            
                    # Create message progress bar
                    message_progress = st.empty()
                    
                    # Send notifications
                    success_count = send_listings_to_telegram(
                        notification_service, 
                        new_listings, 
                        progress_container=message_progress,
                        source_description=url_description
                    )
                    
                    if success_count > 0:
                        message_status.success(f"Sent {success_count} notifications")
                    else:
                        message_status.error(f"Failed to send")
                        
                # Simple results display
                if all_listings:
                    with result_status.container():
                        # Add collapsible section for listings
                        with st.expander("See results"):
                            display_scrape_results({
                                'all_listings': all_listings,
                                'new_listings': new_listings
                            })
                
                # Update counters using scheduler service
                total_runs = scheduler_service.record_scrape()
                st.session_state.total_runs = total_runs  # Keep UI in sync
                
                # Pre-select next URL using scheduler service with user's selection mode
                random_selection = st.session_state.get('random_url_selection', True)
                scheduler_service.select_next_url_index(
                    url_count=len(st.session_state.url_pool),
                    random_selection=random_selection,
                    current_run=total_runs
                )
                
            except Exception as e:
                scrape_status.error(f"❌ Scraping failed: {str(e)}")
                st.session_state.last_scrape_time = current_time

    # Display active scraper status and timer
    if scheduler_service.is_scraping_active():
        # Create a dedicated container for the timer progress
        timer_container = st.container()
        with timer_container:
            display_scraper_progress(scheduler_service)
        
        # Auto-refresh if scraping is active
        time.sleep(1)  # Reduced refresh time for more responsive UI
        st.rerun()
