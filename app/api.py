import os
import webview
import requests
from collections import Counter
import traceback

from app.deck_parser import parse_ydk_file, parse_ydke_url, OmegaFormatDecoder
from app.card_service import fetch_card_details, get_deck_stats


class DeckViewerAPI:
    """API class that will be exposed to JavaScript"""

    def __init__(self):
        self.deck = None
        self.card_details_cache = {}

    def load_ydke_url(self, ydke_url):
        """Load a deck from a YDKE URL"""
        try:
            typed_deck = parse_ydke_url(ydke_url)
            self.deck = {
                "main": typed_deck.main.tolist(),
                "extra": typed_deck.extra.tolist(),
                "side": typed_deck.side.tolist()
            }
            return {"status": "success", "message": "YDKE URL loaded successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def load_ydk_file(self, file_path):
        """Load a deck from a YDK file"""
        try:
            if not os.path.exists(file_path):
                return {"status": "error", "message": f"File not found: {file_path}"}

            self.deck = parse_ydk_file(file_path)

            # Validate deck structure
            if not self.deck["main"] and not self.deck["extra"] and not self.deck["side"]:
                return {"status": "error", "message": "No valid cards found in the deck file."}

            deck_summary = f"Loaded {len(self.deck['main'])} main deck cards, "
            deck_summary += f"{len(self.deck['extra'])} extra deck cards, and "
            deck_summary += f"{len(self.deck['side'])} side deck cards."

            return {"status": "success", "message": deck_summary}
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Error loading YDK file: {error_details}")
            return {"status": "error", "message": f"Error loading deck file: {str(e)}"}

    def load_omega_format(self, encoded_data):
        """Load a deck from Omega format text"""
        try:
            decoder = OmegaFormatDecoder()
            self.deck = decoder.decode(encoded_data)
            return {"status": "success", "message": "Omega format decoded successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_deck_info(self):
        """Get detailed information about the loaded deck"""
        if not self.deck:
            return {"status": "error", "message": "No deck loaded"}

        # Verify deck structure
        if not isinstance(self.deck, dict) or any(key not in self.deck for key in ["main", "extra", "side"]):
            return {"status": "error", "message": "Invalid deck structure"}

        result = {"status": "success"}
        processed_deck = {"main": [], "extra": [], "side": []}

        # Process each section
        for section in ["main", "extra", "side"]:
            cards = []
            card_counts = Counter(self.deck[section])

            for card_id, count in card_counts.items():
                card_detail = self.get_card_details(card_id)
                card_detail["count"] = count
                card_detail["id"] = card_id  # Ensure ID is included
                cards.append(card_detail)

            processed_deck[section] = cards

        # Add the processed deck to the result
        result["deck"] = processed_deck

        # Calculate stats that match what JavaScript expects
        stats = {
            "main_deck": len(self.deck["main"]),
            "extra_deck": len(self.deck["extra"]),
            "side_deck": len(self.deck["side"])
        }

        # Get detailed stats
        try:
            detailed_stats = get_deck_stats(self.deck, self.get_card_details)
            # Combine basic stats with detailed stats
            stats.update(detailed_stats)
        except Exception as e:
            print(f"Error generating detailed deck stats: {e}")
            # We already have the basic stats

        result["stats"] = stats
        return result

    def get_card_details(self, card_id):
        """Get card details from cache or from API"""
        # Check cache first
        if card_id in self.card_details_cache:
            return self.card_details_cache[card_id]

        # Fetch and cache card details
        card_details = fetch_card_details(card_id)
        self.card_details_cache[card_id] = card_details
        return card_details

    def open_file_dialog(self):
        """Open a file dialog to select a YDK file"""
        try:
            result = webview.windows[0].create_file_dialog(webview.OPEN_DIALOG,
                                                           file_types=('YDK Files (*.ydk)', 'All files (*.*)'))
            if result and len(result) > 0:
                return result[0]
            return None
        except Exception as e:
            print(f"Error opening file dialog: {e}")
            return None