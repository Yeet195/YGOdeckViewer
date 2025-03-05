import requests
from collections import Counter
import time

# Cache API responses to avoid rate limiting
card_api_cache = {}


def fetch_card_details(card_id):
    """Fetch card details from YGOProDeck API"""

    if card_id in card_api_cache:
        return card_api_cache[card_id]

    try:
        api_url = f"https://db.ygoprodeck.com/api/v7/cardinfo.php?id={card_id}"
        response = requests.get(api_url)

        if response.status_code == 200:
            data = response.json()

            if 'data' in data and len(data['data']) > 0:
                card_data = data['data'][0]

                image_url = None
                if 'card_images' in card_data and len(card_data['card_images']) > 0:
                    if 'image_url_cropped' in card_data['card_images'][0]:
                        image_url = card_data['card_images'][0]['image_url_cropped']
                    elif 'image_url' in card_data['card_images'][0]:
                        image_url = card_data['card_images'][0]['image_url']

                # Create a simplified card object
                card = {
                    'name': card_data.get('name', 'Unknown'),
                    'type': card_data.get('type', 'Unknown'),
                    'desc': card_data.get('desc', ''),
                    'image_url': image_url
                }

                # Add monster-specific attributes if applicable
                if 'Monster' in card_data.get('type', ''):
                    card['atk'] = card_data.get('atk', 0)
                    card['def'] = card_data.get('def', 0) if 'def' in card_data else None
                    card['level'] = card_data.get('level', None) or card_data.get('rank', None) or card_data.get(
                        'linkval', None)
                    card['attribute'] = card_data.get('attribute', '')
                    card['race'] = card_data.get('race', '')

                # Cache the result
                card_api_cache[card_id] = card
                return card

        # Return a placeholder if API fails or card not found
        return {
            'name': f'Card #{card_id}',
            'type': 'Unknown',
            'desc': 'Card data not available',
            'image_url': None
        }

    except Exception as e:
        print(f"Error fetching card {card_id}: {e}")
        # Return a placeholder for error
        return {
            'name': f'Card #{card_id}',
            'type': 'Error',
            'desc': f'Failed to fetch card data: {str(e)}',
            'image_url': None
        }


def get_deck_stats(deck, get_card_details_func):
    """Generate statistics for a deck"""
    stats = {}

    # Count card types, attributes, etc.
    card_types = Counter()
    attributes = Counter()
    monster_types = Counter()
    levels = Counter()

    # Process each section
    for section in ["main", "extra", "side"]:
        for card_id in deck[section]:
            # Get card details
            card = get_card_details_func(card_id)

            # Count card type
            if card.get('type'):
                card_types[card['type']] += 1

            # Count other stats for monsters
            if 'Monster' in card.get('type', ''):
                if card.get('attribute'):
                    attributes[card['attribute']] += 1

                if card.get('race'):
                    monster_types[card['race']] += 1

                if card.get('level'):
                    levels[card['level']] += 1

    # Add stats to the result
    if card_types:
        stats['card_types'] = dict(card_types)

    if attributes:
        stats['attributes'] = dict(attributes)

    if monster_types:
        stats['monster_types'] = dict(monster_types)

    if levels:
        stats['levels'] = dict(levels)

    return stats