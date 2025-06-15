import streamlit as st
from notifier.telegram import send_telegram_message, format_car_listing_message
from services.vroomsniffer_service import manual_send_listings

def manual_send_listings_ui(listings):
    """Clean UI for sending listings manually to Telegram."""
    if not listings:
        st.warning("No listings to send")
        return
    
    with st.spinner(f"Sending {len(listings)} listings to Telegram..."):
        success_count, failed = manual_send_listings(
            listings,
            send_telegram_message=send_telegram_message,
            format_car_listing_message=format_car_listing_message,
            parse_mode="HTML",
            retry_on_network_error=True
        )
        
        if success_count > 0:
            st.success(f"Successfully sent {success_count} out of {len(listings)} listings!")
            st.balloons()  # Keep the celebration effect
        
        if failed:
            st.error(f"Failed to send {len(failed)} listings. See details below.")
            with st.expander("Error Details", expanded=False):
                for f in failed:
                    st.markdown(f"**Listing #{f['index']}:** {f['title']}")
                    st.code(f["error"], language="text")
        
        elif success_count == 0:
            st.error("Failed to send any listings. Check your Telegram configuration.")

def telegram_test_button():
    """Clean Telegram test button."""
    if st.button("Test Connection", use_container_width=True, 
                help="Test your Telegram bot connection"):
        with st.spinner("Testing connection..."):
            import time
            time.sleep(0.5)
            
            success, error = send_telegram_message("Test from VroomSniffer! Connection successful!", parse_mode="HTML")
            
            if success:
                st.success("Connected! Telegram bot is working perfectly.")
            else:
                st.error(f"Connection failed: {error}")
