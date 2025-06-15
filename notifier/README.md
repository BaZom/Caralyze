# Notifier Module

The notifier module handles sending car listing notifications via Telegram. This module was migrated from WhatsApp to Telegram for better reliability and API access.

## Overview

- **telegram.py**: Main Telegram notification module using Telegram Bot API
- Sends car listings with rich HTML formatting
- Supports test mode for development and corporate networks
- Handles errors gracefully with informative messages

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a chat with BotFather and send `/newbot`
3. Follow the prompts to create your bot:
   - Choose a name for your bot (e.g., "VroomSniffer Car Scraper")
   - Choose a username (must end with "bot", e.g., "vroomsniffer_car_bot")
4. Save the bot token that BotFather gives you

### 2. Get Your Chat ID

1. Send a message to your bot (just say "hello" or anything)
2. Open this URL in your browser (replace `YOUR_BOT_TOKEN` with your actual token):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
3. Find your chat ID in the response JSON (look for `"chat":{"id":12345678}`)

### 3. Configure Environment Variables

Create or update your `.env` file in the project root:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Optional: Test mode (set to true to simulate without sending real messages)
TELEGRAM_TEST_MODE=false
```

## Usage

### Direct Import

```python
from notifier.telegram import send_telegram_message, format_car_listing_message

# Send a simple message
success = send_telegram_message("Hello from VroomSniffer! 🚗")

# Send a formatted car listing
listing = {
    "Title": "BMW X5 xDrive50i",
    "Price": "28.300 €",
    "Location": "Hamburg",
    "URL": "https://example.com/listing"
}
formatted_message = format_car_listing_message(listing)
success = send_telegram_message(formatted_message)
```

### Via CLI

```bash
# First scrape some listings
python cli/main.py run "https://www.example-marketplace.com/s-autos/bmw/k0c216"

# List available listings
python cli/main.py list

# Send a specific listing by index
python cli/main.py send 1
```

## Features

### Message Formatting

The module supports rich HTML formatting for better readability:

- **Bold text** for car titles
- **Emojis** for visual appeal (🚗 💰 📍 🔗)
- **Clickable links** to view full listings
- **Structured layout** with clear sections

Example formatted message:
```
🚗 New Car Listing

BMW X5 xDrive50i
💰 28.300 €
📍 Hamburg

🔗 View Listing
```

### Test Mode

For development or corporate networks that block Telegram:

```env
TELEGRAM_TEST_MODE=true
```

When enabled, messages are printed to console instead of sent to Telegram:

```
[TEST MODE] Would send Telegram message to +4917660353704:
[TEST MODE] Message: BMW X5 xDrive50i...
[+] Telegram message sent successfully (test mode)
```

### Error Handling

The module handles various error scenarios:

- **Missing configuration**: Clear instructions for setup
- **Network issues**: Detailed error messages for troubleshooting
- **API errors**: Telegram-specific error descriptions
- **SSL/Certificate issues**: Graceful fallback and guidance

## API Reference

### `send_telegram_message(text)`

Sends a message via Telegram Bot API.

**Parameters:**
- `text` (str): Message text to send

**Returns:**
- `bool`: True if message sent successfully, False otherwise

**Features:**
- HTML parsing enabled for rich formatting
- Automatic error handling and logging
- Test mode support

### `format_car_listing_message(listing)`

Formats a car listing dictionary into a rich Telegram message.

**Parameters:**
- `listing` (dict): Car listing data with keys:
  - `Title`: Car title/description
  - `Price`: Car price
  - `Location`: Car location
  - `URL`: Link to full listing

**Returns:**
- `str`: Formatted HTML message ready for Telegram

## Testing

### Test the Module Directly

```bash
cd notifier
python telegram.py
```

### Test with Custom Message

```python
python -c "from notifier.telegram import send_telegram_message; send_telegram_message('Test message! 🚗')"
```

### Test with Real Listing Data

```python
python -c "
import json
from notifier.telegram import format_car_listing_message, send_telegram_message

# Load a listing from scraped data
with open('storage/latest_results.json', 'r', encoding='utf-8') as f:
    listings = json.load(f)

# Send formatted message
formatted_msg = format_car_listing_message(listings[0])
send_telegram_message(formatted_msg)
"
```

## Troubleshooting

### Common Issues

1. **"TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured"**
   - Check your `.env` file exists and has correct values
   - Ensure no extra spaces around the values

2. **"SSL: CERTIFICATE_VERIFY_FAILED"**
   - Corporate network blocking Telegram
   - Enable test mode: `TELEGRAM_TEST_MODE=true`

3. **"Telegram API error: Forbidden"**
   - Bot hasn't been started by the user
   - Send a message to your bot first

4. **"Chat not found"**
   - Incorrect chat ID
   - Get chat ID again using the getUpdates method

### Network Restrictions

If your network blocks Telegram (common in corporate environments):

1. **Enable test mode** for development:
   ```env
   TELEGRAM_TEST_MODE=true
   ```

2. **Test from personal network** for production use

3. **Check firewall logs** for specific blocking rules

## Migration from WhatsApp

This module replaced the previous WhatsApp integration for several reasons:

- **Better API reliability**: Telegram Bot API is more stable
- **No phone number required**: Works with bot tokens
- **Rich formatting support**: HTML formatting for better messages
- **Lower rate limits**: More generous message quotas
- **Corporate-friendly**: Better support in enterprise environments

## Examples

### Basic Car Notification

```python
from notifier.telegram import send_telegram_message

# Simple notification
message = """🚗 New BMW Found!

BMW X5 xDrive50i
💰 28.300 €
📍 Hamburg

Check it out: https://example.com/listing"""

success = send_telegram_message(message)
if success:
    print("Notification sent!")
```

### Bulk Notifications

```python
from notifier.telegram import format_car_listing_message, send_telegram_message
import json
import time

# Load multiple listings
with open('storage/latest_results.json', 'r', encoding='utf-8') as f:
    listings = json.load(f)

# Send first 3 listings
for i, listing in enumerate(listings[:3]):
    formatted_msg = format_car_listing_message(listing)
    success = send_telegram_message(formatted_msg)
    print(f"Listing {i+1}: {'✅' if success else '❌'}")
    time.sleep(1)  # Rate limiting
```

## Configuration Examples

### Development Setup
```env
TELEGRAM_BOT_TOKEN=123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=987654321
TELEGRAM_TEST_MODE=true
```

### Production Setup
```env
TELEGRAM_BOT_TOKEN=123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=987654321
TELEGRAM_TEST_MODE=false
```

---

*For more information about the VroomSniffer car scraper project, see the main README.md*
