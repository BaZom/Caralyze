import streamlit as st
import sys
import json
import time
import base64
import random
from pathlib import Path

# Add the parent directory to the path so we can import from local modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from services.vroomsniffer_service import get_listings_for_filter, manual_send_listings
from notifier.telegram import send_telegram_message, format_car_listing_message

def play_sound(sound_file):
    """Play a sound effect using Streamlit's audio component."""
    try:        # Check if sound effects are enabled
        if not st.session_state.get('sound_effects_enabled', True):
            return
            
        sound_path = Path(__file__).parent.parent / "resources" / "sounds" / sound_file
        if sound_path.exists():
            with open(sound_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
              # Use hidden HTML audio for background sound effects
            audio_base64 = base64.b64encode(audio_bytes).decode()
            audio_format = "audio/wav" if sound_file.endswith('.wav') else "audio/mpeg"
            
            # Multiple HTML approaches for better browser compatibility
            audio_html = f"""
            <script>
                // Try multiple methods to play audio
                try {{
                    // Method 1: Create and play audio element
                    var audio = new Audio('data:{audio_format};base64,{audio_base64}');
                    audio.volume = 0.5;
                    audio.play().catch(function(e) {{
                        console.log('Audio play failed:', e);
                    }});
                }} catch(e) {{
                    console.log('Audio creation failed:', e);
                }}
            </script>
            <audio controls autoplay style="display:none;">
                <source src="data:{audio_format};base64,{audio_base64}" type="{audio_format}">
            </audio>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
              # Add delay to let sound complete before continuing
            import time
            time.sleep(2.5)  # Allow 2.5 seconds for sound to play completely
            
    except Exception as e:
        # Show error in debug mode
        if st.session_state.get('debug_mode', False):
            st.error(f"Sound playback error: {e}")
        pass

def build_search_url_from_custom(custom_url):
    """Validate and return custom URL only if it's a proper HTTP/HTTPS URL."""
    if custom_url and custom_url.strip():
        url = custom_url.strip()
        # Basic URL validation
        if url.startswith(('http://', 'https://')) and '.' in url:
            return url
    return ""

def _show_system_status():
    """Display system status with clean metrics layout matching home page."""
    st.subheader("📊 System Status")
    
    # Get actual data
    try:
        from services.vroomsniffer_service import get_cache_stats, load_cache
        import os
        
        # Get cache stats from session state paths
        all_old_path = st.session_state.get('all_old_path')
        latest_new_path = st.session_state.get('latest_new_path')
        
        total_listings = 0
        recent_additions = 0
        cache_size_mb = 0
        
        if all_old_path and os.path.exists(all_old_path):
            stats = get_cache_stats(all_old_path)
            total_listings = stats.get('total_listings', 0)
            cache_size_mb = stats.get('cache_size_mb', 0)
        
        if latest_new_path and os.path.exists(latest_new_path):
            recent_data = load_cache(latest_new_path)
            recent_additions = len(recent_data) if recent_data else 0
            
    except Exception:
        total_listings = 0
        recent_additions = 0
        cache_size_mb = 0
      # Clean metrics layout (same as home page)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Listings", total_listings)
    with col2:
        st.metric("Recent Additions", recent_additions)
    with col3:
        if cache_size_mb > 0:
            st.metric("Cache Size", f"{cache_size_mb} MB")
        else:
            st.metric("Cache Size", "< 0.01 MB")
    with col4:
        st.metric("Total Runs", st.session_state.get('total_runs', 0))
    
    # Status message
    status_text = "🟢 ACTIVE" if st.session_state.scraping_active else "🔴 STOPPED"
    scraper_info = f"Scraper: {status_text} | URLs: {len(st.session_state.url_pool)} | Runs: {st.session_state.total_runs}"
    
    if st.session_state.scraping_active:
        st.info(f"🚀 {scraper_info}")
    else:
        st.warning(f"⏸️ {scraper_info}")

def _display_url_pool():
    """Display current URL pool."""
    if st.session_state.url_pool:
        st.subheader(f"🔗 URL Pool ({len(st.session_state.url_pool)} URLs)")
        
        for i, url in enumerate(st.session_state.url_pool):
            if (st.session_state.scraping_active and 
                hasattr(st.session_state, 'next_url_index') and 
                i == st.session_state.next_url_index):
                st.markdown(f'<div class="next-url">🎯 NEXT: {url}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="url-item">{i+1}. {url}</div>', unsafe_allow_html=True)
    else:
        st.info("No URLs in pool. Add URLs to start scraping.")

def _display_scrape_results(results):
    """Display scraping results."""
    if not results:
        return
        
    # Only show results once per scrape
    result_timestamp = results.get('timestamp', 0)
    if 'last_displayed_result' not in st.session_state:
        st.session_state.last_displayed_result = 0
    
    if result_timestamp <= st.session_state.last_displayed_result:
        return
    
    st.session_state.last_displayed_result = result_timestamp
    
    st.subheader("📊 Results")
    
    with st.container():
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        
        new_listings = results.get('new_listings', [])
        scraped_url = results.get('url', '')
        url_num = results.get('url_index', 0) + 1
        
        st.write(f"**🔗 URL #{url_num}:** {scraped_url}")
        
        if new_listings:
            st.write(f"**✅ Result:** {len(new_listings)} new listings found")
        else:
            st.write(f"**🔍 Result:** No new listings found")
        
        st.markdown('</div>', unsafe_allow_html=True)

def _send_listings_to_telegram(listings):
    """Send listings to Telegram."""
    try:
        success_count, failed = manual_send_listings(
            listings,
            send_telegram_message=send_telegram_message,
            format_car_listing_message=format_car_listing_message,
            parse_mode="HTML",
            retry_on_network_error=True
        )
        
        if success_count > 0:
            st.success(f"Sent {success_count}/{len(listings)} listings to Telegram")
        
        if failed:
            st.error(f"Failed to send {len(failed)} listings")
            
    except Exception as e:
        st.error(f"Telegram sending failed: {str(e)}")

def get_url_storage_path():
    """Get the path for URL storage file"""
    return Path(__file__).parent.parent.parent / "storage" / "saved_urls.json"

def load_saved_urls():
    """Load saved URLs from storage"""
    try:
        url_file = get_url_storage_path()
        if url_file.exists():
            with open(url_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('urls', [])
    except Exception as e:
        pass
    return []

def save_urls_to_storage(urls):
    """Save URLs to storage file"""
    try:
        url_file = get_url_storage_path()
        url_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'urls': urls,
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(url_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        return False

def add_url_to_storage(url):
    """Add a single URL to storage"""
    saved_urls = load_saved_urls()
    if url not in saved_urls:
        saved_urls.append(url)
        return save_urls_to_storage(saved_urls)
    return True

def remove_url_from_storage(url):
    """Remove a URL from storage"""
    saved_urls = load_saved_urls()
    if url in saved_urls:
        saved_urls.remove(url)
        return save_urls_to_storage(saved_urls)
    return True

def clear_url_storage():
    """Clear all URLs from storage"""
    try:
        return save_urls_to_storage([])
    except Exception:
        return False

def show_scraper_page(all_old_path, latest_new_path, root_dir):
    """Multi-URL scraper with clean interface."""
    
    # Store paths in session state for status function
    st.session_state.all_old_path = all_old_path
    st.session_state.latest_new_path = latest_new_path
    
    # VroomSniffer color scheme styling
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}    /* Simple text styling - no boxes */
    
    .status-card {
        background-color: white;
        border: 1px solid #D7E9F7;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 1px 3px rgba(18, 60, 90, 0.1);
    }
    
    .url-item {
        background-color: #F4F4F4;
        border: 1px solid #D7E9F7;
        border-radius: 6px;
        padding: 0.8rem;
        margin: 0.3rem 0;
        font-family: monospace;
        font-size: 0.9em;
        color: #333333;
    }
    
    .next-url {
        background-color: #D7E9F7;
        border: 2px solid #F57C00;
        border-radius: 6px;
        padding: 0.8rem;
        margin: 0.3rem 0;
        font-weight: bold;
        font-family: monospace;
        font-size: 0.9em;
        color: #123C5A;
    }
    
    .stButton > button {
        height: 2.5rem !important;
        font-size: 0.9rem !important;
        padding: 0.5rem 1rem !important;
        min-width: 120px !important;
        margin: 0.2rem 0 !important;
        border-radius: 6px !important;
        border: 1px solid #123C5A !important;
        background-color: white !important;
        color: #333333 !important;
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
    
    /* Divider styling */
    hr {
        border: none;
        border-top: 1px solid #e0e0e0;
        margin: 1.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)    # Initialize session state
    if 'url_pool' not in st.session_state:
        st.session_state.url_pool = []
        # Load saved URLs on first initialization
        saved_urls = load_saved_urls()
        st.session_state.url_pool.extend(saved_urls)
    if 'scraping_active' not in st.session_state:
        st.session_state.scraping_active = False
    if 'auto_send_active' not in st.session_state:
        st.session_state.auto_send_active = False
    if 'interval_seconds' not in st.session_state:
        st.session_state.interval_seconds = 60
    if 'last_scrape_time' not in st.session_state:
        st.session_state.last_scrape_time = 0
    if 'current_url_index' not in st.session_state:
        st.session_state.current_url_index = 0
    if 'next_url_index' not in st.session_state:
        st.session_state.next_url_index = 0
    if 'total_runs' not in st.session_state:
        st.session_state.total_runs = 0
    if 'latest_results' not in st.session_state:
        st.session_state.latest_results = {}
    if 'sound_effects_enabled' not in st.session_state:
        st.session_state.sound_effects_enabled = False

    # Pre-select next URL when scraping starts
    if st.session_state.scraping_active and st.session_state.url_pool:
        if ('next_url_selected' not in st.session_state or 
            st.session_state.next_url_index >= len(st.session_state.url_pool)):
            if len(st.session_state.url_pool) > 1:
                st.session_state.next_url_index = random.randint(0, len(st.session_state.url_pool) - 1)
            else:
                st.session_state.next_url_index = 0
            st.session_state.next_url_selected = True    # System Status
    _show_system_status()
    
    st.divider()      # URL Management
    st.subheader("🔧 URL Management")
    
    # Load saved URLs on first load
    if 'saved_urls_loaded' not in st.session_state:
        saved_urls = load_saved_urls()
        st.session_state.url_pool.extend([url for url in saved_urls if url not in st.session_state.url_pool])
        st.session_state.saved_urls_loaded = True
    
    # URL input
    new_url = st.text_input("Enter search URL:", placeholder="https://marketplace-url.com/search...")
      # URL management buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Add URL", type="primary", use_container_width=True):
            built_url = build_search_url_from_custom(new_url)
            if built_url and built_url not in st.session_state.url_pool:
                st.session_state.url_pool.append(built_url)
                add_url_to_storage(built_url)
                st.success("✅ URL added!")
            elif built_url in st.session_state.url_pool:
                st.warning("⚠️ URL already exists")
            else:
                st.error("❌ Invalid URL (must start with http:// or https://)")
    
    with col2:
        if st.button("Load Saved URLs", use_container_width=True):
            saved_urls = load_saved_urls()
            if not saved_urls:
                st.info("📭 No URLs found in storage")
            else:
                added_count = 0
                for url in saved_urls:
                    # Validate saved URLs before adding
                    if url.startswith(('http://', 'https://')) and url not in st.session_state.url_pool:
                        st.session_state.url_pool.append(url)
                        added_count += 1
                if added_count > 0:
                    st.success(f"✅ Loaded {added_count} URLs!")
                else:
                    st.info("ℹ️ No new URLs to load")
    
    with col3:
        if st.button("Clear Pool", use_container_width=True):
            st.session_state.url_pool = []
            st.session_state.scraping_active = False
            st.success("✅ Pool cleared!")
    
    with col4:
        if st.button("Clear Storage", use_container_width=True):
            if clear_url_storage():
                st.success("✅ Storage cleared!")
            else:
                st.error("❌ Failed to clear storage")
    
    # Display current URL pool with remove functionality
    if st.session_state.url_pool:
        st.subheader(f"📋 Current URL Pool ({len(st.session_state.url_pool)} URLs)")
        
        for i, url in enumerate(st.session_state.url_pool):
            col1, col2 = st.columns([4, 1])
            with col1:
                # Show URL with truncation for long URLs
                display_url = url if len(url) <= 60 else f"{url[:60]}..."
                
                # Highlight the next URL to be scraped
                if (st.session_state.scraping_active and 
                    hasattr(st.session_state, 'next_url_index') and 
                    i == st.session_state.next_url_index):
                    st.markdown(f'<div class="next-url">🎯 NEXT: {i+1}. {display_url}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="url-item">{i+1}. {display_url}</div>', unsafe_allow_html=True)
            with col2:
                if st.button("🗑️", key=f"remove_{i}", help="Remove from pool"):
                    st.session_state.url_pool.pop(i)
                    st.rerun()
    else:
        st.info("📭 No URLs in pool. Add some URLs to get started!")
    
    st.divider()
      # Controls
    st.subheader("⚙️ Controls")    # Adjacent buttons for Start/Stop and Auto-send toggle
    col1, col2, col3 = st.columns([1.5, 2, 1.5])
    
    with col1:
        if not st.session_state.scraping_active:
            if st.button("▶️ Start", type="primary", use_container_width=True):
                if st.session_state.url_pool:
                    st.session_state.scraping_active = True
                    st.session_state.last_scrape_time = 0
                      # Pre-select first URL
                    if len(st.session_state.url_pool) > 1:
                        st.session_state.next_url_index = random.randint(0, len(st.session_state.url_pool) - 1)
                    else:
                        st.session_state.next_url_index = 0
                    st.session_state.next_url_selected = True
                    
                    st.success("🚀 Started!")
                    play_sound("Vroom 1.mp3")  # Play start sound effect
                    st.rerun()
                else:
                    st.error("Add URLs first")
        else:
            if st.button("⏹️ Stop", use_container_width=True):
                st.session_state.scraping_active = False
                st.success("⏹️ Stopped!")
                st.rerun()
    
    with col2:
        st.session_state.auto_send_active = st.checkbox("📤 Auto-send to Telegram", value=st.session_state.auto_send_active)
        st.session_state.sound_effects_enabled = st.checkbox(
            "🔊 Sound Effects", 
            value=st.session_state.sound_effects_enabled,
            help="Enable/disable sound effects for scraping events"
        )
    
    with col3:
        st.session_state.interval_seconds = st.number_input(
            "Interval (sec):", 
            min_value=30, 
            max_value=3600, 
            value=st.session_state.interval_seconds,
            step=30
        )

    # Active Scraping Logic
    if st.session_state.scraping_active and st.session_state.url_pool:
        if time.time() - st.session_state.last_scrape_time >= st.session_state.interval_seconds:
            current_time = time.time()
            
            # Use pre-selected URL
            if hasattr(st.session_state, 'next_url_index') and st.session_state.next_url_index < len(st.session_state.url_pool):
                current_url_index = st.session_state.next_url_index
            else:
                current_url_index = 0
            
            current_url = st.session_state.url_pool[current_url_index]
            
            with st.spinner(f"🔍 Scraping URL #{current_url_index + 1}..."):
                try:
                    filters = {"custom_url": current_url}
                    
                    results = get_listings_for_filter(
                        filters,
                        all_old_path, 
                        latest_new_path,
                        build_search_url_from_custom,
                        root_dir                    )
                    
                    all_listings, new_listings = results
                    
                    # Play sound immediately when new listings are found
                    if new_listings:
                        play_sound("Sniff1.wav")
                    
                    st.session_state.latest_results = {
                        'all_listings': all_listings,
                        'new_listings': new_listings,
                        'timestamp': current_time,
                        'url': current_url,
                        'url_index': current_url_index
                    }
                    
                    # Auto-send if enabled
                    if st.session_state.auto_send_active and new_listings:
                        _send_listings_to_telegram(new_listings)
                    
                    # Update counters
                    st.session_state.total_runs += 1
                    st.session_state.last_scrape_time = current_time
                    st.session_state.current_url_index = current_url_index
                      # Pre-select next URL
                    if len(st.session_state.url_pool) > 1:
                        st.session_state.next_url_index = random.randint(0, len(st.session_state.url_pool) - 1)
                    else:
                        st.session_state.next_url_index = 0
                    st.session_state.next_url_selected = True
                    
                    # Show results
                    if new_listings:
                        st.success(f"✅ Found {len(new_listings)} new listings!")
                    else:
                        st.info("🔍 No new listings found")
                    
                except Exception as e:
                    st.error(f"❌ Scraping failed: {str(e)}")
                    st.session_state.last_scrape_time = current_time

    # Show Results Section
    if st.session_state.latest_results:
        st.divider()

    # Display Results
    _display_scrape_results(st.session_state.latest_results)
    
    # Progress Display
    if st.session_state.scraping_active:
        time_until_next = st.session_state.interval_seconds - (time.time() - st.session_state.last_scrape_time)
        if time_until_next > 0:
            progress = 1.0 - (time_until_next / st.session_state.interval_seconds)
            progress_container = st.empty()
            progress_container.progress(progress, text=f"⏰ Next scrape in {int(time_until_next)} seconds")
        else:
            ready_container = st.empty()
            ready_container.progress(1.0, text="🔍 Ready to scrape...")
        
        # Auto-refresh
        time.sleep(2)
        st.rerun()
    else:
        st.empty()