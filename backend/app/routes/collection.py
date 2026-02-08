"""Collection management endpoints - PostgreSQL storage"""
from flask import Blueprint, jsonify, request
from app.db import get_cursor

collection_bp = Blueprint('collection', __name__)


@collection_bp.route('/', methods=['GET'])
def get_collection():
    """Get the entire collection with optional filters"""
    search = request.args.get('search', '').lower()
    set_code = request.args.get('set', '')

    with get_cursor() as cursor:
        query = "SELECT * FROM collection WHERE 1=1"
        params = []

        if search:
            query += " AND LOWER(card_name) LIKE %s"
            params.append(f"%{search}%")

        if set_code:
            query += " AND set_code = %s"
            params.append(set_code)

        query += " ORDER BY added_at DESC"

        cursor.execute(query, params)
        cards = cursor.fetchall()

        # Convert to list of dicts and handle Decimal types
        cards = [dict(c) for c in cards]
        for card in cards:
            if card.get('price_usd'):
                card['price_usd'] = float(card['price_usd'])

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
    data = request.json

    if not data:
        return jsonify({'error': 'Request body required'}), 400

    required = ['scryfall_id', 'name']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    with get_cursor() as cursor:
        # Check if card already exists (same scryfall_id and foil status)
        cursor.execute(
            "SELECT * FROM collection WHERE scryfall_id = %s AND foil = %s",
            (data['scryfall_id'], data.get('foil', False))
        )
        existing = cursor.fetchone()

        if existing:
            # Update quantity
            new_quantity = existing['quantity'] + data.get('quantity', 1)
            cursor.execute(
                "UPDATE collection SET quantity = %s WHERE id = %s RETURNING *",
                (new_quantity, existing['id'])
            )
            updated = dict(cursor.fetchone())
            if updated.get('price_usd'):
                updated['price_usd'] = float(updated['price_usd'])
            return jsonify(updated)

        # Insert new card
        cursor.execute("""
            INSERT INTO collection (
                scryfall_id, card_name, set_code, set_name, collector_number,
                rarity, mana_cost, type_line, image_url, price_usd,
                quantity, foil, condition, notes
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING *
        """, (
            data['scryfall_id'],
            data['name'],
            data.get('set_code'),
            data.get('set_name'),
            data.get('collector_number'),
            data.get('rarity'),
            data.get('mana_cost'),
            data.get('type_line'),
            data.get('image_uri'),
            data.get('price'),
            data.get('quantity', 1),
            data.get('foil', False),
            data.get('condition', 'NM'),
            data.get('notes')
        ))

        card = dict(cursor.fetchone())
        if card.get('price_usd'):
            card['price_usd'] = float(card['price_usd'])

        return jsonify(card), 201


@collection_bp.route('/<int:card_id>', methods=['DELETE'])
def remove_card(card_id):
    """Remove a card from the collection"""
    with get_cursor() as cursor:
        cursor.execute("DELETE FROM collection WHERE id = %s", (card_id,))

        if cursor.rowcount == 0:
            return jsonify({'error': 'Card not found'}), 404

        return jsonify({'success': True})


@collection_bp.route('/<int:card_id>', methods=['PATCH'])
def update_card(card_id):
    """Update card details (quantity, condition, notes, foil)"""
    data = request.json

    if not data:
        return jsonify({'error': 'Request body required'}), 400

    with get_cursor() as cursor:
        # Get current card
        cursor.execute("SELECT * FROM collection WHERE id = %s", (card_id,))
        card = cursor.fetchone()

        if not card:
            return jsonify({'error': 'Card not found'}), 404

        # Build update query
        allowed_fields = ['quantity', 'condition', 'notes', 'foil']
        updates = []
        params = []

        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = %s")
                params.append(data[field])

        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400

        # Check if quantity would be 0 or less
        new_quantity = data.get('quantity', card['quantity'])
        if new_quantity <= 0:
            cursor.execute("DELETE FROM collection WHERE id = %s", (card_id,))
            return jsonify({'success': True, 'removed': True})

        params.append(card_id)
        query = f"UPDATE collection SET {', '.join(updates)} WHERE id = %s RETURNING *"

        cursor.execute(query, params)
        updated = dict(cursor.fetchone())
        if updated.get('price_usd'):
            updated['price_usd'] = float(updated['price_usd'])

        return jsonify(updated)


@collection_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get collection statistics"""
    with get_cursor() as cursor:
        # Get totals
        cursor.execute("""
            SELECT
                COUNT(*) as unique_cards,
                COALESCE(SUM(quantity), 0) as total_cards,
                COALESCE(SUM(price_usd * quantity), 0) as total_value
            FROM collection
        """)
        totals = cursor.fetchone()

        if totals['unique_cards'] == 0:
            return jsonify({
                'unique_cards': 0,
                'total_cards': 0,
                'total_value': 0,
                'by_set': [],
                'by_rarity': [],
                'most_valuable': []
            })

        # Cards by set
        cursor.execute("""
            SELECT set_code, set_name, COUNT(*) as cards, SUM(quantity) as total
            FROM collection
            GROUP BY set_code, set_name
            ORDER BY total DESC
            LIMIT 10
        """)
        by_set = [dict(r) for r in cursor.fetchall()]

        # Cards by rarity
        cursor.execute("""
            SELECT rarity, COUNT(*) as cards, SUM(quantity) as total
            FROM collection
            GROUP BY rarity
            ORDER BY total DESC
        """)
        by_rarity = [dict(r) for r in cursor.fetchall()]

        # Most valuable cards
        cursor.execute("""
            SELECT * FROM collection
            WHERE price_usd IS NOT NULL AND price_usd > 0
            ORDER BY price_usd DESC
            LIMIT 10
        """)
        most_valuable = [dict(r) for r in cursor.fetchall()]
        for card in most_valuable:
            if card.get('price_usd'):
                card['price_usd'] = float(card['price_usd'])

        return jsonify({
            'unique_cards': int(totals['unique_cards']),
            'total_cards': int(totals['total_cards']),
            'total_value': float(totals['total_value']),
            'by_set': by_set,
            'by_rarity': by_rarity,
            'most_valuable': most_valuable
        })
