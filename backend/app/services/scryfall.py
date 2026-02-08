"""Scryfall API client"""
import time
import requests
from functools import lru_cache

SCRYFALL_BASE_URL = 'https://api.scryfall.com'

# Rate limiting: max 10 requests per second
_last_request_time = 0
_min_request_interval = 0.1  # 100ms between requests


def _rate_limit():
    """Ensure we don't exceed Scryfall's rate limit"""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _min_request_interval:
        time.sleep(_min_request_interval - elapsed)
    _last_request_time = time.time()


def _format_card(card_data):
    """Extract relevant fields from Scryfall card data"""
    if not card_data:
        return None

    # Get image URI (prefer normal size, fallback to small)
    image_uris = card_data.get('image_uris', {})
    if not image_uris and 'card_faces' in card_data:
        # Double-faced cards have images in card_faces
        image_uris = card_data['card_faces'][0].get('image_uris', {})

    image_uri = image_uris.get('normal') or image_uris.get('small') or image_uris.get('large')

    # Get price (USD)
    prices = card_data.get('prices', {})
    price = None
    if prices.get('usd'):
        price = float(prices['usd'])
    elif prices.get('usd_foil'):
        price = float(prices['usd_foil'])

    return {
        'scryfall_id': card_data.get('id'),
        'name': card_data.get('name'),
        'set_code': card_data.get('set'),
        'set_name': card_data.get('set_name'),
        'collector_number': card_data.get('collector_number'),
        'rarity': card_data.get('rarity'),
        'mana_cost': card_data.get('mana_cost'),
        'type_line': card_data.get('type_line'),
        'oracle_text': card_data.get('oracle_text'),
        'image_uri': image_uri,
        'price': price,
        'price_foil': float(prices['usd_foil']) if prices.get('usd_foil') else None,
        'scryfall_uri': card_data.get('scryfall_uri'),
    }


def search_cards(query, limit=20):
    """
    Search for cards by name
    Returns list of formatted card objects
    """
    _rate_limit()

    try:
        response = requests.get(
            f'{SCRYFALL_BASE_URL}/cards/search',
            params={
                'q': f'name:{query}',
                'order': 'name',
                'unique': 'cards',
            },
            timeout=10
        )

        if response.status_code == 404:
            return {'cards': [], 'total': 0}

        response.raise_for_status()
        data = response.json()

        cards = [_format_card(c) for c in data.get('data', [])[:limit]]

        return {
            'cards': cards,
            'total': data.get('total_cards', len(cards))
        }

    except requests.RequestException as e:
        print(f'Scryfall search error: {e}')
        return {'cards': [], 'total': 0, 'error': str(e)}


@lru_cache(maxsize=1000)
def get_card_by_name(name):
    """
    Get a card by fuzzy name match
    Returns formatted card object or None
    Cached to reduce API calls
    """
    _rate_limit()

    try:
        response = requests.get(
            f'{SCRYFALL_BASE_URL}/cards/named',
            params={'fuzzy': name},
            timeout=10
        )

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return _format_card(response.json())

    except requests.RequestException as e:
        print(f'Scryfall get card error: {e}')
        return None


def get_card_by_id(scryfall_id):
    """Get a card by its Scryfall ID"""
    _rate_limit()

    try:
        response = requests.get(
            f'{SCRYFALL_BASE_URL}/cards/{scryfall_id}',
            timeout=10
        )

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return _format_card(response.json())

    except requests.RequestException as e:
        print(f'Scryfall get card by ID error: {e}')
        return None
