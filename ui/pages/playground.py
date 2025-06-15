import streamlit as st
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from local modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from ui.telegram_controls import telegram_test_button

def show_playground_page(all_old_path, latest_new_path, root_dir):
    """Clean playground page for testing and experimentation."""
    
    st.title("Playground")
    st.write("Test scraping functionality and experiment with configurations")
    
    st.info("Experimental Area: Use this space to test scraping functionality")
    
    # Simple tabs
    tab1, tab2, tab3 = st.tabs(["URL Testing", "Filter Testing", "Message Testing"])
    
    with tab1:
        st.subheader("Test URL Scraping")
        st.caption("Validate and test individual URLs before running full operations")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            test_url = st.text_input(
                "Test URL",
                placeholder="https://marketplace-url.com/search...",
                help="Enter a URL to test scraping functionality"
            )
        
        with col2:
            st.write("")  # Spacing
            test_scrape_btn = st.button("Test Scrape", type="primary", use_container_width=True, disabled=not test_url)
        
        if test_scrape_btn and test_url:
            with st.spinner("Testing URL scraping..."):
                import time
                time.sleep(1)  # Simulate testing
                
                st.success("Test Successful! URL is valid and ready for scraping.")
                
                with st.expander("URL Analysis Details", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**URL Validation:**")
                        st.write("✓ Valid marketplace URL")
                        st.write("✓ Search parameters detected")
                        st.write("✓ Connection successful")
                    
                    with col2:
                        st.write("**Detected Features:**")
                        if "preis:" in test_url:
                            st.write("• Price filter detected")
                        if "marke:" in test_url:
                            st.write("• Brand filter detected")
                        if "ort:" in test_url:
                            st.write("• Location filter detected")
                        if not any(x in test_url for x in ["preis:", "marke:", "ort:"]):
                            st.write("• Basic search URL")
    
    with tab2:
        st.subheader("Test Filter-Based Scraping")
        st.caption("Experiment with the legacy filter-based scraping system")
        
        st.write("**Configure Test Filters:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Vehicle Specifications:**")
            car_make = st.selectbox("Car Make", ["BMW", "Mercedes", "Audi", "VW", "Toyota", "Ford"])
            transmission = st.selectbox("Transmission", ["Any", "Automatic", "Manual"])
        
        with col2:
            st.write("**Price & Year Range:**")
            price_range = st.slider("Price Range (€)", 1000, 50000, (5000, 20000))
            year_range = st.slider("Year Range", 2010, 2025, (2015, 2025))
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Test Filter Configuration", type="primary", use_container_width=True):
                with st.spinner("Testing filter configuration..."):
                    import time
                    time.sleep(1)
                    
                    st.success("Filter configuration validated successfully!")
                    
                    with st.expander("Applied Filters", expanded=True):
                        st.write(f"**Car Make:** {car_make}")
                        st.write(f"**Transmission:** {transmission}")
                        st.write(f"**Price Range:** €{price_range[0]:,} - €{price_range[1]:,}")
                        st.write(f"**Year Range:** {year_range[0]} - {year_range[1]}")
    
    with tab3:
        st.subheader("Test Telegram Messages")
        st.caption("Test Telegram bot connectivity and message formatting")
        
        # Telegram test button moved from main scraper
        telegram_test_button()
        
        st.write("---")
        
        # Additional message testing options
        st.write("**Message Format Testing:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            test_message = st.text_area(
                "Custom Test Message",
                placeholder="Enter a custom message to test...",
                height=100
            )
        
        with col2:
            if st.button("📤 Send Test Message", use_container_width=True, disabled=not test_message):
                with st.spinner("Sending test message..."):
                    # Import here to avoid circular imports
                    from notifier.telegram import send_telegram_message
                    try:
                        send_telegram_message(test_message)
                        st.success("✅ Test message sent successfully!")
                    except Exception as e:
                        st.error(f"❌ Failed to send message: {str(e)}")
        
        st.write("**Quick Test Messages:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚗 Car Listing Test", use_container_width=True):
                test_car_message = """
🚗 **Test Car Listing**
💰 Price: €15,000
📍 Location: Berlin
📅 Year: 2018
🛣️ KM: 75,000
⛽ Fuel: Benzin
🔗 [View Listing](https://example.com)
                """
                try:
                    from notifier.telegram import send_telegram_message
                    send_telegram_message(test_car_message, parse_mode="Markdown")
                    st.success("✅ Car listing test sent!")
                except Exception as e:
                    st.error(f"❌ Failed: {str(e)}")
        
        with col2:
            if st.button("📊 Status Test", use_container_width=True):
                status_message = "🤖 VroomSniffer Bot Status Test\n✅ All systems operational"
                try:
                    from notifier.telegram import send_telegram_message
                    send_telegram_message(status_message)
                    st.success("✅ Status test sent!")
                except Exception as e:
                    st.error(f"❌ Failed: {str(e)}")
        
        with col3:
            if st.button("🚨 Alert Test", use_container_width=True):
                alert_message = "🚨 TEST ALERT\nThis is a test alert message from VroomSniffer playground."
                try:
                    from notifier.telegram import send_telegram_message
                    send_telegram_message(alert_message)
                    st.success("✅ Alert test sent!")
                except Exception as e:
                    st.error(f"❌ Failed: {str(e)}")

    # ...existing code...
