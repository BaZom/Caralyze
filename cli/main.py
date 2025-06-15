# CLI Tool
# --------
# Run this file with commands to interact with the scraper's JSON storage and notifications.
#
# USAGE EXAMPLES:
# ===============
#
# 1. Run the scraper with a marketplace URL:
#    python cli/main.py run "https://marketplace-url.com/search-cars"
#
# 2. List the latest scraped listings:
#    python cli/main.py list
#
# 3. Search for specific cars in the listings:
#    python cli/main.py search "bmw"
#    python cli/main.py search "giulietta"
#    python cli/main.py search "automatic"
#
# 4. Send a listing via Telegram (use index from 'list' command):
#    python cli/main.py send 3
#
# WORKFLOW:
# =========
# 1. First, run the scraper to get fresh data:
#    python cli/main.py run "<your-marketplace-search-url>"
#
# 2. Browse the results:
#    python cli/main.py list
#
# 3. Search for specific terms:
#    python cli/main.py search "your-keyword"
#
# 4. Share interesting listings:
#    python cli/main.py send <listing-index>
#
# DATA STORAGE:
# =============
# - Latest scraping results: storage/latest_results.json
# - Historical data: storage/all_old_results.json
# - New listings only: storage/latest_new_results.json
#
# NOTES:
# ======
# - The 'run' command will overwrite previous results in latest_results.json
# - Use the Streamlit UI for more advanced filtering and monitoring
# - Telegram functionality requires proper configuration in notifier/

import argparse
import sys
import subprocess
import json
import time
from pathlib import Path

# Add the parent directory to the path so we can import from project modules
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from notifier.telegram import send_telegram_message, format_car_listing_message

# CLI-specific data paths - using centralized storage directory
STORAGE_DIR = Path(__file__).parent.parent / "storage"
LATEST_RESULTS_PATH = STORAGE_DIR / "latest_results.json"
ALL_RESULTS_PATH = STORAGE_DIR / "all_old_results.json"
NEW_RESULTS_PATH = STORAGE_DIR / "latest_new_results.json"

# Create storage directory if it doesn't exist
STORAGE_DIR.mkdir(exist_ok=True)

def _check_listings_exist():
    """Helper function to check if listings exist and print error if not"""
    listings = load_json_data(LATEST_RESULTS_PATH)
    if not listings:
        print("[!] No listings found. Run 'python cli/main.py run <url>' first.")
        return False
    return True

def load_json_data(path):
    """Load data from JSON file"""
    if Path(path).exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json_data(data, path):
    """Save data to JSON file"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def list_listings():
    """List the latest scraped listings from JSON file"""
    if not _check_listings_exist():
        return
    
    listings = load_json_data(LATEST_RESULTS_PATH)
    print(f"[*] Found {len(listings)} listings:")
    for i, listing in enumerate(listings[:10], 1):  # Show only first 10
        title = listing.get("Title", "Unknown")[:50]
        price = listing.get("Price", "Unknown")
        location = listing.get("Location", "Unknown")
        print(f"[{i}] {title} | {price} | {location}")

def search_listings(keyword):
    """Search listings by keyword in title"""
    if not _check_listings_exist():
        return
    
    listings = load_json_data(LATEST_RESULTS_PATH)
    
    keyword = keyword.lower()
    matches = []
    for i, listing in enumerate(listings, 1):
        title = listing.get("Title", "").lower()
        if keyword in title:
            matches.append((i, listing))
    
    if matches:
        print(f"[*] Found {len(matches)} matches for '{keyword}':")
        for i, listing in matches[:10]:  # Show only first 10 matches
            title = listing.get("Title", "Unknown")[:50]
            price = listing.get("Price", "Unknown")
            print(f"[{i}] {title} | {price}")
    else:
        print(f"[!] No listings found matching '{keyword}'")

def send_listing(listing_index):
    """Send a listing via Telegram by index"""
    if not _check_listings_exist():
        return
    
    listings = load_json_data(LATEST_RESULTS_PATH)
    if 1 <= listing_index <= len(listings):
        listing = listings[listing_index - 1]
        
        # Use formatted message for better presentation
        formatted_msg = format_car_listing_message(listing)
        success = send_telegram_message(formatted_msg)
        
        if success:
            print(f"[+] Listing {listing_index} sent via Telegram")
        else:
            print(f"[!] Failed to send listing {listing_index} via Telegram")
    else:
        print(f"[!] Listing index {listing_index} not found. Use 'list' command to see available listings.")

def send_top_listings(count=5):
    """Send top N listings via Telegram"""
    if not _check_listings_exist():
        return
    
    listings = load_json_data(LATEST_RESULTS_PATH)
    
    actual_count = min(count, len(listings))
    print(f"[*] Sending top {actual_count} listings via Telegram...")
    
    success_count = 0
    for i, listing in enumerate(listings[:actual_count]):
        formatted_msg = format_car_listing_message(listing)
        success = send_telegram_message(formatted_msg)
        
        if success:
            print(f"[+] Listing {i+1}/{actual_count} sent successfully")
            success_count += 1
        else:
            print(f"[!] Failed to send listing {i+1}")
          # Rate limiting - wait between messages
        if i < actual_count - 1:
            time.sleep(2)  # 2 second delay between messages
    
    print(f"[+] Bulk notification complete! {success_count}/{actual_count} messages sent successfully.")

def notify_new_findings(search_keyword=""):
    """Send notification about new findings with optional search filter"""
    if not _check_listings_exist():
        return
    
    listings = load_json_data(LATEST_RESULTS_PATH)
    
    # Filter by keyword if provided
    filtered_listings = listings
    if search_keyword:
        filtered_listings = [
            listing for listing in listings 
            if search_keyword.lower() in listing.get("Title", "").lower()
        ]
        if not filtered_listings:
            print(f"[!] No listings found matching '{search_keyword}'")
            return
    
    # Send summary message
    if search_keyword:
        summary_msg = f"🔍 <b>Search Results for '{search_keyword}'</b>\n\n"
    else:
        summary_msg = f"🚗 <b>Latest Car Scraping Results</b>\n\n"
    
    summary_msg += f"📊 Found {len(filtered_listings)} listings\n"
    
    if filtered_listings:
        # Add top 3 titles as preview
        summary_msg += "\n<b>Top Listings:</b>\n"
        for i, listing in enumerate(filtered_listings[:3]):
            title = listing.get("Title", "Unknown")[:50] + "..." if len(listing.get("Title", "")) > 50 else listing.get("Title", "Unknown")
            price = listing.get("Price", "Unknown")
            summary_msg += f"{i+1}. {title} - {price}\n"
    
    summary_msg += f"\n💡 Use CLI to explore: 'python cli/main.py list'"
    
    success = send_telegram_message(summary_msg)
    if success:
        print(f"[+] Summary notification sent for {len(filtered_listings)} listings")
    else:
        print(f"[!] Failed to send summary notification")

def copy_scraper_results():
    """Copy results from the main scraper to CLI data directory"""
    # Original scraper output paths
    original_latest = project_root / "scraper" / "latest_results.json"
    
    if original_latest.exists():
        listings = load_json_data(str(original_latest))
        save_json_data(listings, LATEST_RESULTS_PATH)
        return True
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="VroomSniffer Car Scraper CLI - Interact with JSON-based listing data",        epilog="""
EXAMPLES:
  %(prog)s run "https://www.example-marketplace.com/s-autos/bmw/k0c216"
  %(prog)s list
  %(prog)s search "bmw x5"  
  %(prog)s send 3

For more advanced features, use the Streamlit UI:
  streamlit run ui/streamlit_app.py
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser(
        "list", 
        help="List latest scraped listings from JSON",
        description="Display the most recent car listings from the last scraping run. Shows first 10 listings with title, price, and location."
    )

    # Search command  
    search_parser = subparsers.add_parser(
        "search", 
        help="Search listings by keyword",
        description="Search through the latest listings for cars matching a keyword in the title."
    )
    search_parser.add_argument(
        "keyword", 
        type=str, 
        help="Keyword to search for in listing titles (e.g., 'bmw', 'automatic', 'diesel')"
    )    # Send command
    send_parser = subparsers.add_parser(
        "send", 
        help="Send a listing via Telegram",
        description="Send a specific car listing via Telegram. Use 'list' command first to see available indices."
    )
    send_parser.add_argument(
        "index", 
        type=int, 
        help="Index of the listing to send (use 'list' command to see indices, starting from 1)"
    )

    # Send-top command
    send_top_parser = subparsers.add_parser(
        "send-top", 
        help="Send top N listings via Telegram",
        description="Send multiple top listings via Telegram with formatting. Includes rate limiting between messages."
    )
    send_top_parser.add_argument(
        "count", 
        type=int, 
        nargs='?', 
        default=5,
        help="Number of top listings to send (default: 5)"
    )

    # Notify command
    notify_parser = subparsers.add_parser(
        "notify", 
        help="Send summary notification about findings",
        description="Send a summary notification about all findings or filtered by keyword."
    )
    notify_parser.add_argument(
        "keyword", 
        type=str, 
        nargs='?', 
        default="",
        help="Optional keyword to filter listings before notification"
    )    # Run command
    run_parser = subparsers.add_parser(
        "run", 
        help="Run the scraper engine with a direct marketplace URL",
        description="Execute the car scraper with a specific marketplace search URL. Results will be saved to storage/latest_results.json"
    )
    run_parser.add_argument(
        "url", 
        type=str, 
        help="Direct marketplace search URL (e.g., 'https://www.example-marketplace.com/s-autos/bmw/k0c216')"
    )
    run_parser.add_argument(
        "--notify", 
        action="store_true", 
        help="Send Telegram notifications for top listings after scraping"
    )
    run_parser.add_argument(
        "--notify-count", 
        type=int, 
        default=5,
        help="Number of top listings to notify via Telegram (default: 5)"
    )    # Version command
    version_parser = subparsers.add_parser(
        "version", 
        help="Show version information",
        description="Display version and system information for the VroomSniffer car scraper."
    )

    args = parser.parse_args()

    if args.command == "list":
        list_listings()
    elif args.command == "search":
        search_listings(args.keyword)
    elif args.command == "send":
        send_listing(args.index)
    elif args.command == "send-top":
        send_top_listings(args.count)
    elif args.command == "notify":
        notify_new_findings(args.keyword)
    elif args.command == "version":
        print("🚗 VroomSniffer Car Scraper v2.0.0 (Refactored)")
    elif args.command == "run":
        # Run the Playwright scraper engine with the given URL
        scraper_path = project_root / "scraper" / "engine.py"
        
        # Prepare scraper arguments
        scraper_args = [sys.executable, str(scraper_path), "--url", args.url]
        if args.notify:
            scraper_args.extend(["--notify", "--notify-count", str(args.notify_count)])
        
        result = subprocess.run(scraper_args)
        if result.returncode == 0:
            # Copy results to CLI data directory
            if copy_scraper_results():
                print(f"[+] Scraper run complete. Results saved to {LATEST_RESULTS_PATH}")
            else:
                print("[!] Scraper completed but no results file found.")
        else:
            print("[!] Scraper run failed.")
    else:
        parser.print_help()
