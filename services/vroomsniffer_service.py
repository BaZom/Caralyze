"""
VroomSniffer Caching Service - URL-based caching system for car listings.
Handles scraping, URL-based caching, and cache management operations.
This is the main interface between UI and caching logic.
"""
import sys
import json
import time
import re
import subprocess
from datetime import datetime
from pathlib import Path

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))

# === URL-BASED CACHING SYSTEM ===

def load_cache(cache_path):
    """Load cached listings as URL-indexed dictionary"""
    if Path(cache_path).exists():
        try:
            # Check if file is empty first
            if Path(cache_path).stat().st_size == 0:
                return {}
                
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Handle both old filter-based format and new URL-based format
                if isinstance(data, dict) and data:
                    first_key = next(iter(data.keys()))
                    if first_key.startswith('http'):
                        return data  # Already URL-based
                    # Convert old format to URL-based
                    url_cache = {}
                    for filter_listings in data.values():
                        if isinstance(filter_listings, list):
                            for listing in filter_listings:
                                if listing.get("URL"):
                                    url_cache[listing["URL"]] = listing
                    return url_cache
                elif isinstance(data, list):
                    # Handle list format (legacy)
                    url_cache = {}
                    for listing in data:
                        if listing.get("URL"):
                            url_cache[listing["URL"]] = listing
                    return url_cache
                return {}
        except (json.JSONDecodeError, Exception):
            # If file is corrupted or empty, return empty dict
            return {}
    return {}

def save_cache(cache_dict, cache_path):
    """Save URL-indexed cache dictionary"""
    Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache_dict, f, ensure_ascii=False, indent=2)

def is_listing_cached(url, cache_path):
    """Check if a listing URL exists in cache"""
    cache = load_cache(cache_path)
    return url in cache

def add_listing_to_cache(listing, cache_path):
    """Add a single listing to cache"""
    url = listing.get("URL")
    if not url:
        return False
    
    cache = load_cache(cache_path)
    cache[url] = listing
    save_cache(cache, cache_path)
    return True

def remove_listing_from_cache(url, cache_path):
    """Remove a listing from cache by URL"""
    cache = load_cache(cache_path)
    if url in cache:
        del cache[url]
        save_cache(cache, cache_path)
        return True
    return False

def get_cached_listing(url, cache_path):
    """Get a specific listing from cache by URL"""
    cache = load_cache(cache_path)
    return cache.get(url)

def get_all_cached_listings(cache_path):
    """Get all cached listings as a list"""
    cache = load_cache(cache_path)
    return list(cache.values())

def clear_cache(cache_path):
    """Clear all cached listings"""
    save_cache({}, cache_path)
    return True

def get_cache_stats(cache_path):
    """Get cache statistics"""
    try:
        cache = load_cache(cache_path)
        
        # Calculate file size if cache file exists
        file_size = 0
        if Path(cache_path).exists():
            file_size = Path(cache_path).stat().st_size
        
        return {
            "total_listings": len(cache),
            "urls": list(cache.keys()),
            "cache_size": file_size,
            "cache_size_mb": round(file_size / (1024 * 1024), 2) if file_size > 0 else 0
        }
    except Exception as e:
        # Return default stats if anything goes wrong
        return {
            "total_listings": 0,
            "urls": [],
            "cache_size": 0,
            "cache_size_mb": 0
        }

def run_scraper_and_load_results(filters, build_search_url_ui, root_dir):
    """
    Run the marketplace scraper engine as a subprocess with the given filters and load results from the output JSON file.
    Returns a list of listings.
    """
    import subprocess
    listings_data = []
    try:
        if filters and filters.get("custom_url"):
            url = filters["custom_url"]
            print(f"[DEBUG] Using custom URL: {url}")
        else:
            url = build_search_url_ui(filters)
            print(f"[DEBUG] Generated URL from filters: {url}")
            print(f"[DEBUG] Filters used: {filters}")
        
        args = [sys.executable, str(Path(root_dir) / "scraper" / "engine.py"), "--url", url]
        result = subprocess.run(
            args,
            cwd=root_dir, capture_output=True, text=True
        )
        if result.returncode == 0:
            json_path = Path(root_dir) / "storage" / "latest_results.json"
            if json_path.exists():
                with open(json_path, "r", encoding="utf-8") as f:
                    listings_data = json.load(f)
                    if not listings_data:
                        print(f"[INFO] No listings found for search URL: {url}")
            else:
                print(f"[WARNING] Scraper completed but no results file found")
                listings_data = []
        else:
            print(f"[WARNING] Scraper failed: {result.stderr}")
            print(f"[WARNING] Search URL was: {url}")
            # Don't raise error, return empty list to continue with cached data
            listings_data = []
    except Exception as e:
        print(f"[WARNING] Scraping error: {str(e)}")
        print(f"[WARNING] Search URL was: {url if 'url' in locals() else 'Unknown'}")
        # Don't raise error, return empty list to continue with cached data
        listings_data = []
    return listings_data

def get_listings_for_filter(filters, all_old_path, latest_new_path, build_search_url_ui, root_dir):
    """
    Get all listings and new listings by running the scraper and comparing with cached listings.
    Now uses URL-based caching instead of filter-based.
    
    Args:
        filters: Dictionary containing search filters (or custom_url)
        all_old_path: Path to the JSON file storing all previously seen listings
        latest_new_path: Path to the JSON file storing latest new listings
        build_search_url_ui: Function to build search URL from filters
        root_dir: Root directory of the project
        
    Returns:
        Tuple of (all_listings, new_listings)
    """
    # Run scraper to get fresh listings
    listings_data = run_scraper_and_load_results(filters, build_search_url_ui, root_dir)
    
    # Load existing cached listings (URL-based)
    cached_listings = load_cache(all_old_path)
    
    # Identify new listings by URL
    new_listings = []
    all_listings = []
    
    for listing in listings_data:
        url = listing.get("URL")
        if not url:
            continue  # Skip listings without URL
            
        if url not in cached_listings:
            # This is a new listing
            new_listings.append(listing)
            cached_listings[url] = listing
        
        all_listings.append(listing)
    
    # Save updated cache
    save_cache(cached_listings, all_old_path)
    
    # Save new listings for this run
    new_listings_dict = {listing["URL"]: listing for listing in new_listings if listing.get("URL")}
    save_cache(new_listings_dict, latest_new_path)
    
    return all_listings, new_listings

def extract_prices(listings):
    """Extract prices from listings for statistics"""
    prices = []
    for item in listings:
        price_str = item.get("Price", "").replace(".", "").replace(",", "").replace("€", "").strip()
        match = re.search(r"\d+", price_str)
        if match:
            prices.append(int(match.group()))
    return prices

# === END OF CACHING SERVICE FUNCTIONS ===

def remove_listings_by_ids(listing_urls, cache_path):
    """Remove multiple listings from cache by their URLs"""
    cache = load_cache(cache_path)
    removed_count = 0
    
    for url in listing_urls:
        if url in cache:
            del cache[url]
            removed_count += 1
    
    save_cache(cache, cache_path)
    return removed_count

def clear_all_caches(root_dir=None):
    """
    Clear all cache files and remove old listings.
    
    Args:
        root_dir: Root directory of the project (optional, defaults to current working directory)
        
    Returns:
        dict: Summary of what was cleared
    """
    if root_dir is None:
        root_dir = Path.cwd()
    else:
        root_dir = Path(root_dir)
    
    cleared_files = []
    errors = []      # List of cache files to clear
    cache_files = [
        "storage/all_old_results.json",
        "storage/latest_new_results.json",
        "storage/latest_results.json"
    ]
    
    for cache_file in cache_files:
        file_path = root_dir / cache_file
        try:
            if file_path.exists():
                # Clear the file by writing empty dict or list
                if "latest_results.json" in cache_file:
                    # This is scraped results, write empty list
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump([], f, ensure_ascii=False, indent=2)
                else:
                    # This is cache file, write empty dict
                    save_cache({}, str(file_path))
                cleared_files.append(str(file_path))
        except Exception as e:
            errors.append(f"Error clearing {file_path}: {str(e)}")
    
    return {
        "cleared_files": cleared_files,
        "errors": errors,
        "total_cleared": len(cleared_files),
        "message": f"Successfully cleared {len(cleared_files)} cache files"
    }

def get_listings_by_search_criteria(cache_path, search_term=None, min_price=None, max_price=None):
    """
    Search cached listings by criteria
    
    Args:
        cache_path: Path to cache file
        search_term: Search in title/location (optional)
        min_price: Minimum price filter (optional) 
        max_price: Maximum price filter (optional)
        
    Returns:
        list: Filtered listings
    """
    cache = load_cache(cache_path)
    listings = list(cache.values())
    
    if not listings:
        return []
    
    filtered = listings
    
    # Filter by search term
    if search_term:
        search_term = search_term.lower()
        filtered = [l for l in filtered if 
                   search_term in l.get("Title", "").lower() or 
                   search_term in l.get("Location", "").lower()]
      # Filter by price range
    if min_price is not None or max_price is not None:
        price_filtered = []
        for listing in filtered:
            price_str = listing.get("Price", "").replace(".", "").replace(",", "").replace("€", "").strip()
            match = re.search(r"\d+", price_str)
            if match:
                price = int(match.group())
                if min_price is not None and price < min_price:
                    continue
                if max_price is not None and price > max_price:
                    continue
                price_filtered.append(listing)
        filtered = price_filtered
    
    return filtered

def show_statistics(listings_data):
    """Calculate statistics for listings (average price, count, price list)."""
    prices = extract_prices(listings_data)
    avg_price = int(sum(prices) / len(prices)) if prices else 0
    return avg_price, len(listings_data), prices

def manual_send_listings(listings, send_telegram_message, format_car_listing_message, parse_mode="HTML", retry_on_network_error=True):
    """Send listings to Telegram, retrying once on network error. Returns (success_count, failed_list)."""
    success_count = 0
    failed = []
    for i, listing in enumerate(listings):
        formatted_msg = format_car_listing_message(listing)
        success, error = send_telegram_message(formatted_msg, parse_mode=parse_mode)
        # Retry once if network error
        if not success and error and ("ConnectionResetError" in error or "Connection aborted" in error) and retry_on_network_error:
            time.sleep(2)
            success, error = send_telegram_message(formatted_msg, parse_mode=parse_mode)
        if success:
            success_count += 1
        else:
            failed.append({
                'index': i+1,
                'title': listing.get('Title', 'Unknown'),
                'error': error
            })
        if i < len(listings) - 1:
            time.sleep(1.5)  # Rate limiting
    return success_count, failed
