"""Collection management endpoints - In-memory storage for development"""
from flask import Blueprint, jsonify, request
from datetime import datetime

collection_bp = Blueprint('collection', __name__)

# In-memory storage (will be replaced with DB in production)
_collection = []
_next_id = 1


@collection_bp.route('/', methods=['GET'])
def get_collection():
    """Get the entire collection with optional filters"""
    search = request.args.get('search', '').lower()
    set_code = request.args.get('set', '')

    cards = _collection

    if search:
        cards = [c for c in cards if search in c['card_name'].lower()]

    if set_code:
        cards = [c for c in cards if c.get('set_code') == set_code]

    # Calculate totals
    total_cards = sum(c['quantity'] for c in cards)
    total_value = sum((c.get('price_usd') or 0) * c['quantity'] for c in cards)

    return jsonify({
        'cards': cards,
        'unique_cards': len(cards),
        'total_cards': total_cards,
        'total_value': float(total_value)
    })


@collection_bp.route('/', methods=['POST'])
def add_card():
    """Add a card to the collection"""
    global _next_id

    data = request.json

    if not data:
        return jsonify({'error': 'Request body required'}), 400

    required = ['scryfall_id', 'name']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    # Check if card already exists
    existing = next(
        (c for c in _collection
         if c['scryfall_id'] == data['scryfall_id'] and c.get('foil') == data.get('foil', False)),
        None
    )

    if existing:
        existing['quantity'] += data.get('quantity', 1)
        return jsonify(existing)

    # Add new card
    card = {
        'id': _next_id,
        'scryfall_id': data['scryfall_id'],
        'card_name': data['name'],
        'set_code': data.get('set_code'),
        'set_name': data.get('set_name'),
        'collector_number': data.get('collector_number'),
        'rarity': data.get('rarity'),
        'mana_cost': data.get('mana_cost'),
        'type_line': data.get('type_line'),
        'image_url': data.get('image_uri'),
        'price_usd': data.get('price'),
        'quantity': data.get('quantity', 1),
        'foil': data.get('foil', False),
        'condition': data.get('condition', 'NM'),
        'notes': data.get('notes'),
        'added_at': datetime.now().isoformat()
    }
    _next_id += 1
    _collection.append(card)

    return jsonify(card), 201


@collection_bp.route('/<int:card_id>', methods=['DELETE'])
def remove_card(card_id):
    """Remove a card from the collection"""
    global _collection

    original_len = len(_collection)
    _collection = [c for c in _collection if c['id'] != card_id]

    if len(_collection) == original_len:
        return jsonify({'error': 'Card not found'}), 404

    return jsonify({'success': True})


@collection_bp.route('/<int:card_id>', methods=['PATCH'])
def update_card(card_id):
    """Update card details (quantity, condition, notes, foil)"""
    data = request.json

    if not data:
        return jsonify({'error': 'Request body required'}), 400

    card = next((c for c in _collection if c['id'] == card_id), None)

    if not card:
        return jsonify({'error': 'Card not found'}), 404

    # Update allowed fields
    allowed_fields = ['quantity', 'condition', 'notes', 'foil']
    for field in allowed_fields:
        if field in data:
            card[field] = data[field]

    # If quantity is 0 or less, remove the card
    if card.get('quantity', 1) <= 0:
        _collection.remove(card)
        return jsonify({'success': True, 'removed': True})

    return jsonify(card)


@collection_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get collection statistics"""
    if not _collection:
        return jsonify({
            'unique_cards': 0,
            'total_cards': 0,
            'total_value': 0,
            'by_set': [],
            'by_rarity': [],
            'most_valuable': []
        })

    # Calculate totals
    unique_cards = len(_collection)
    total_cards = sum(c['quantity'] for c in _collection)
    total_value = sum((c.get('price_usd') or 0) * c['quantity'] for c in _collection)

    # Cards by set
    sets = {}
    for c in _collection:
        key = c.get('set_code') or 'unknown'
        if key not in sets:
            sets[key] = {'set_code': key, 'set_name': c.get('set_name'), 'cards': 0, 'total': 0}
        sets[key]['cards'] += 1
        sets[key]['total'] += c['quantity']
    by_set = sorted(sets.values(), key=lambda x: x['total'], reverse=True)[:10]

    # Cards by rarity
    rarities = {}
    for c in _collection:
        key = c.get('rarity') or 'unknown'
        if key not in rarities:
            rarities[key] = {'rarity': key, 'cards': 0, 'total': 0}
        rarities[key]['cards'] += 1
        rarities[key]['total'] += c['quantity']
    by_rarity = sorted(rarities.values(), key=lambda x: x['total'], reverse=True)

    # Most valuable cards
    most_valuable = sorted(
        [c for c in _collection if c.get('price_usd')],
        key=lambda x: x.get('price_usd', 0),
        reverse=True
    )[:10]

    return jsonify({
        'unique_cards': unique_cards,
        'total_cards': total_cards,
        'total_value': float(total_value),
        'by_set': by_set,
        'by_rarity': by_rarity,
        'most_valuable': most_valuable
    })
