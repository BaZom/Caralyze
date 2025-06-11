import requests

import re

from selenium import webdriver

from selenium.webdriver.firefox.service import Service as FirefoxService

from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import TimeoutException

import time

import datetime

import logging


# --- Telegram Bot Configuration ---

TELEGRAM_BOT_TOKEN =  # your bot token

TELEGRAM_CHAT_ID = "-1002705250898"  # your numeric Chat ID


# --- WebDriver Path ---

webdriver_path = r"C:\Users\warda\Documents\WebDriver\geckodriver.exe"


# --- Kleinanzeigen Configuration ---

search_urls = [

    "https://www.kleinanzeigen.de/s-autos/anbieter:privat/anzeige:angebote/preis::9500/bmw-x1/k0c216+autos.ez_i:2009%2C2012+autos.km_i:%2C150000+autos.schaden_s:nein+autos.shift_s:automatik",  # URL 1

    "https://www.kleinanzeigen.de/s-autos/anbieter:privat/anzeige:angebote/preis::11500/bmw-x1/k0c216+autos.ez_i:2012%2C2015+autos.km_i:%2C150000+autos.schaden_s:nein+autos.shift_s:automatik", # URL 2

    "https://www.kleinanzeigen.de/s-autos/anbieter:privat/anzeige:angebote/preis::16000/bmw-x1/k0c216+autos.ez_i:2015%2C2019+autos.km_i:%2C150000+autos.schaden_s:nein+autos.shift_s:automatik", # URL 3

    "https://www.kleinanzeigen.de/s-autos/anbieter:privat/anzeige:angebote/preis::13500/bmw-x1/k0c216+autos.ez_i:2015%2C2019+autos.km_i:%2C150000+autos.schaden_s:nein+autos.shift_s:manuell",   # URL 4

    "https://www.kleinanzeigen.de/s-autos/anbieter:privat/anzeige:angebote/preis::19500/bmw-x1/k0c216+autos.ez_i:2019%2C2022+autos.km_i:%2C150000+autos.schaden_s:nein+autos.shift_s:automatik", # URL 5

    "https://www.kleinanzeigen.de/s-autos/anbieter:privat/anzeige:angebote/preis::6500/golf/k0c216+autos.ez_i:2008%2C2012+autos.km_i:%2C150000+autos.shift_s:automatik+autos.typ_s:limousine",     # URL 6

    "https://www.kleinanzeigen.de/s-autos/anbieter:privat/anzeige:angebote/preis::6000/golf/k0c216+autos.ez_i:2012%2C2017+autos.km_i:%2C140000+autos.schaden_s:nein+autos.shift_s:manuell+autos.typ_s:limousine",   # URL 7

    "https://www.kleinanzeigen.de/s-autos/anbieter:privat/anzeige:angebote/preis::9500/golf/k0c216+autos.ez_i:2012%2C2017+autos.km_i:%2C140000+autos.schaden_s:nein+autos.shift_s:automatik+autos.typ_s:limousine", # URL 8

    "https://www.kleinanzeigen.de/s-autos/anbieter:privat/anzeige:angebote/preis::10000/golf/k0c216+autos.ez_i:2017%2C2020+autos.km_i:%2C140000+autos.schaden_s:nein+autos.shift_s:manuell+autos.typ_s:limousine", # URL 9

    "https://www.kleinanzeigen.de/s-autos/anbieter:privat/anzeige:angebote/preis::13500/golf/k0c216+autos.ez_i:2017%2C2020+autos.km_i:%2C140000+autos.schaden_s:nein+autos.shift_s:automatik+autos.typ_s:limousine",# URL 10

    "https://www.kleinanzeigen.de/s-autos/anbieter:privat/anzeige:angebote/preis::17000/golf/k0c216+autos.ez_i:2020%2C+autos.km_i:%2C100000+autos.schaden_s:nein+autos.shift_s:automatik+autos.typ_s:limousine",      # URL 11

    "https://www.kleinanzeigen.de/s-autos/anbieter:privat/preis:1000:10000/bmw-116/k0c216+autos.ez_i:2012%2C2015+autos.km_i:%2C150000+autos.schaden_s:nein+autos.shift_s:automatik", # URL 12

    "https://www.kleinanzeigen.de/s-autos/anbieter:privat/preis:1000:7000/bmw-116/k0c216+autos.ez_i:2012%2C2015+autos.km_i:%2C150000+autos.schaden_s:nein", # URL 13

    "https://www.kleinanzeigen.de/s-autos/anbieter:privat/preis:1000:14000/audi-a3/k0c216+autos.ez_i:2014%2C2018+autos.km_i:%2C150000+autos.power_i:131%2C+autos.schaden_s:nein+autos.shift_s:automatik", # URL 14

    "https://www.kleinanzeigen.de/s-autos/preis:1000:15500/audi-a3/k0c216+autos.ez_i:2018%2C+autos.km_i:%2C150000+autos.power_i:131%2C+autos.schaden_s:nein+autos.shift_s:automatik",  # URL 15

    "https://www.kleinanzeigen.de/s-autos/anbieter:privat/preis:1000:15500/seat-arona/k0c216+autos.ez_i:2019%2C+autos.km_i:%2C100000+autos.schaden_s:nein+autos.shift_s:automatik",  # URL 16

    "https://www.kleinanzeigen.de/s-autos/anbieter:privat/preis:1000:22000/audi-a5/k0c216+autos.ez_i:2018%2C+autos.km_i:%2C150000+autos.schaden_s:nein+autos.shift_s:automatik",  # URL 17

    "https://www.kleinanzeigen.de/s-autos/anbieter:privat/preis:1000:16500/audi-a4/k0c216+autos.ez_i:2017%2C+autos.km_i:%2C150000+autos.schaden_s:nein+autos.shift_s:automatik"  # URL 18


]


SEEN_ADS_FILE = "seen_ads_master_list.txt"

seen_ads_links = set()

check_interval_seconds = 45 * 60

pause_between_urls_seconds = 60


def get_driver():

    logging.info(f"Attempting to use GeckoDriver from: {webdriver_path}")

    service = FirefoxService(executable_path=webdriver_path)

    driver = webdriver.Firefox(service=service)

    return driver


def load_seen_ads(file_path):

    try:

        with open(file_path, 'r') as f:

            return {line.strip() for line in f if line.strip()}

    except FileNotFoundError:

        logging.info(f"Seen ads file ('{file_path}') not found. Starting with an empty set.")

        return set()


def save_ad_link(file_path, ad_link):

    try:

        with open(file_path, 'a') as f:

            f.write(ad_link + '\n')

    except IOError as e:

        logging.error(f"Could not write to seen ads file '{file_path}': {e}")


def send_telegram_message(bot_token, chat_id, message_text):

    if not bot_token or not chat_id:

        logging.error("Telegram Bot Token or Chat ID is missing. Skipping message.")

        return False

    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {'chat_id': chat_id, 'text': message_text, 'parse_mode': 'MarkdownV2'}

    while True:

        try:

            response = requests.post(send_url, data=payload, timeout=20)

            if response.status_code == 200:

                logging.info("Telegram message sent successfully!")

                return True

            elif response.status_code == 429:

                response_json = response.json()

                description = response_json.get("description", "")

                retry_after_match = re.search(r'retry after (\d+)', description)

                if retry_after_match:

                    retry_seconds = int(retry_after_match.group(1))

                    logging.warning(f"Rate limited by Telegram. Waiting for {retry_seconds} seconds before retrying.")

                    time.sleep(retry_seconds + 1)

                else:

                    logging.warning("Rate limited by Telegram, but no 'retry after' time found. Waiting 30 seconds.")

                    time.sleep(30)

            else:

                logging.error(f"Error sending Telegram message: HTTP {response.status_code} {response.reason}")

                logging.error(f"Response: {response.text}")

                return False

        except requests.exceptions.RequestException as e:

            logging.error(f"A network or request-level error occurred: {e}. Retrying in 60 seconds.")

            time.sleep(60)


# <<< THIS IS THE UPDATED FUNCTION >>>

def fetch_ads_from_url(driver, url_to_check):

    newly_found_ads_for_this_url = []

    logging.info(f"Navigating to Kleinanzeigen search: {url_to_check[:100]}...")

    driver.get(url_to_check)

    try:

        link_element_selector = 'article.aditem[data-adid] h2.text-module-begin > a'

        logging.info(f"Waiting for link elements with selector: '{link_element_selector}'")

        WebDriverWait(driver, 20).until(

            EC.presence_of_all_elements_located((By.CSS_SELECTOR, link_element_selector))

        )

        link_elements = driver.find_elements(By.CSS_SELECTOR, link_element_selector)

        logging.info(f"Found {len(link_elements)} ad link elements on the page for this URL.")

        for link_element in link_elements:

            try:

                ad_link_relative = link_element.get_attribute('href')

                ad_title = link_element.text.strip()

                ad_link_absolute = ad_link_relative

                if ad_link_relative and not ad_link_relative.startswith('http'):

                    ad_link_absolute = "https://www.kleinanzeigen.de" + ad_link_relative

                if ad_link_absolute and ad_link_absolute not in seen_ads_links:

                    seen_ads_links.add(ad_link_absolute)

                    save_ad_link(SEEN_ADS_FILE, ad_link_absolute)

                    newly_found_ads_for_this_url.append({'title': ad_title, 'link': ad_link_absolute})

                    logging.info(f"  NEW Ad (to be sent): {ad_title} - {ad_link_absolute}")

            except Exception as e_inner:

                logging.error(f"Error processing one ad link item: {e_inner}")

                continue

    except TimeoutException:

        logging.warning(f"Timed out waiting for ad links on {url_to_check[:70]}... The page might have no results.")

    except Exception as e_outer:

        logging.error(f"An unexpected error occurred fetching ads from {url_to_check[:70]}...: {e_outer}")

    return newly_found_ads_for_this_url


def escape_markdown_v2(text):

    escape_chars = r'_*[]()~`>#+-=|{}.!'

    text = text.replace('\\', '\\\\')

    for char in escape_chars:

        text = text.replace(char, f'\\{char}')

    return text


def main():

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("scraper_master.log"), logging.StreamHandler()])

    driver = None

    try:

        logging.info("--- Kleinanzeigen Notifier Script Starting ---")

        global seen_ads_links

        seen_ads_links = load_seen_ads(SEEN_ADS_FILE)

        logging.info(f"Loaded {len(seen_ads_links)} previously seen ad links.")

        logging.info("Testing Telegram connection...")

        send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, "Kleinanzeigen Notifier script started\\! ✅")

        driver = get_driver()

        while True:

            current_time = datetime.datetime.now()

            # I am assuming you have the version of the code that runs 24/7.

            # If you still have the old time check here, remove it.

            logging.info(f"--- Starting new search cycle at {current_time.strftime('%Y-%m-%d %H:%M:%S')} ---")

            all_new_ads_this_cycle = []

            for i, search_url_item in enumerate(search_urls):

                logging.info(f"\n--- Checking URL {i+1}/{len(search_urls)}: {search_url_item[:100]}... ---")

                new_ads_from_this_url = fetch_ads_from_url(driver, search_url_item)

                if new_ads_from_this_url:

                    all_new_ads_this_cycle.extend(new_ads_from_this_url)

                if i < len(search_urls) - 1:

                    logging.info(f"Waiting for {pause_between_urls_seconds} seconds before checking the next URL...")

                    time.sleep(pause_between_urls_seconds)

            search_completion_time = datetime.datetime.now().strftime("%H:%M:%S")

            if all_new_ads_this_cycle:

                num_new_ads = len(all_new_ads_this_cycle)

                logging.info(f">>> CYCLE COMPLETE: Found {num_new_ads} TOTAL NEW ads to notify! <<<")

                raw_summary_text = f"🔍 Search cycle completed at {search_completion_time}. Found {num_new_ads} new ad(s). Sending them now..."

                summary_message = escape_markdown_v2(raw_summary_text)

                send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, summary_message)

                time.sleep(2)

                for ad_index, ad in enumerate(all_new_ads_this_cycle):

                    logging.info(f"Sending ad {ad_index + 1}/{num_new_ads} to Telegram...")

                    escaped_title = escape_markdown_v2(ad['title'])

                    safe_link_for_markdown = ad['link'].replace('(', '%28').replace(')', '%29')

                    message = f"🚗 *New Ad Found\\!*\n\n*Title:* {escaped_title}\n*Link:* [View Ad]({safe_link_for_markdown})"

                    send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)

                logging.info("-" * 20)

            else:

                logging.info("CYCLE COMPLETE: No new ads found across all searches this time.")

                raw_no_new_ads_text = f"✅ Search cycle completed at {search_completion_time}. No new ads found."

                no_new_ads_message = escape_markdown_v2(raw_no_new_ads_text)

                send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, no_new_ads_message)

            logging.info(f"--- Cycle finished. Waiting for {check_interval_seconds / 60:.0f} minutes before next cycle... ---")

            time.sleep(check_interval_seconds)

    except KeyboardInterrupt:

        logging.info("\nScript interrupted by user. Exiting.")

    except Exception as e_main:

        logging.critical(f"A critical error occurred in the main loop: {e_main}", exc_info=True)

        try:

            error_message_text = f"Kleinanzeigen script encountered a critical error: {str(e_main)}"

            escaped_error_message = escape_markdown_v2(error_message_text)[:4000]

            send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, escaped_error_message)

        except Exception as e_notify_fail:

            logging.error(f"Could not send critical error notification via Telegram: {e_notify_fail}")

    finally:

        if driver:

            logging.info("Closing the browser.")

            driver.quit()

        logging.info("--- Kleinanzeigen Notifier script stopped. ---")


if __name__ == "__main__":

    main()

