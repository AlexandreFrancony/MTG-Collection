"""Collection management endpoints"""
from flask import Blueprint, jsonify, request
from ..db import get_cursor

collection_bp = Blueprint('collection', __name__)


@collection_bp.route('/', methods=['GET'])
def get_collection():
    """Get the entire collection with optional filters"""
    try:
        # Get query parameters for filtering
        search = request.args.get('search', '')
        set_code = request.args.get('set', '')

        with get_cursor() as cursor:
            query = """
                SELECT id, scryfall_id, card_name, set_code, set_name,
                       collector_number, rarity, mana_cost, type_line,
                       image_url, price_usd, quantity, foil, condition, notes,
                       added_at
                FROM collection
                WHERE 1=1
            """
            params = []

            if search:
                query += " AND card_name ILIKE %s"
                params.append(f'%{search}%')

            if set_code:
                query += " AND set_code = %s"
                params.append(set_code)

            query += " ORDER BY card_name ASC"

            cursor.execute(query, params)
            cards = cursor.fetchall()

            # Calculate totals
            total_cards = sum(c['quantity'] for c in cards)
            total_value = sum(
                (c['price_usd'] or 0) * c['quantity']
                for c in cards
            )

        return jsonify({
            'cards': [dict(c) for c in cards],
            'unique_cards': len(cards),
            'total_cards': total_cards,
            'total_value': float(total_value)
        })

    except Exception as e:
        print(f"Error fetching collection: {e}")
        return jsonify({'error': 'Failed to fetch collection'}), 500


@collection_bp.route('/', methods=['POST'])
def add_card():
    """
    Add a card to the collection
    Body: { scryfall_id, name, set_code, collector_number, quantity?, foil?, ... }
    """
    data = request.json

    if not data:
        return jsonify({'error': 'Request body required'}), 400

    required = ['scryfall_id', 'name']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    try:
        with get_cursor() as cursor:
            # Check if card already exists (same scryfall_id and foil status)
            cursor.execute(
                """SELECT id, quantity FROM collection
                   WHERE scryfall_id = %s AND foil = %s""",
                [data['scryfall_id'], data.get('foil', False)]
            )
            existing = cursor.fetchone()

            if existing:
                # Update quantity
                new_quantity = existing['quantity'] + data.get('quantity', 1)
                cursor.execute(
                    "UPDATE collection SET quantity = %s WHERE id = %s RETURNING *",
                    [new_quantity, existing['id']]
                )
                card = cursor.fetchone()
                return jsonify(dict(card))

            # Insert new card
            cursor.execute(
                """INSERT INTO collection
                   (scryfall_id, card_name, set_code, set_name, collector_number,
                    rarity, mana_cost, type_line, image_url, price_usd,
                    quantity, foil, condition, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *""",
                [
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
                ]
            )
            card = cursor.fetchone()

        return jsonify(dict(card)), 201

    except Exception as e:
        print(f"Error adding card: {e}")
        return jsonify({'error': 'Failed to add card'}), 500


@collection_bp.route('/<int:card_id>', methods=['DELETE'])
def remove_card(card_id):
    """Remove a card from the collection"""
    try:
        with get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM collection WHERE id = %s RETURNING id",
                [card_id]
            )
            deleted = cursor.fetchone()

            if not deleted:
                return jsonify({'error': 'Card not found'}), 404

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error removing card: {e}")
        return jsonify({'error': 'Failed to remove card'}), 500


@collection_bp.route('/<int:card_id>', methods=['PATCH'])
def update_card(card_id):
    """Update card details (quantity, condition, notes, foil)"""
    data = request.json

    if not data:
        return jsonify({'error': 'Request body required'}), 400

    try:
        # Build dynamic update query
        allowed_fields = ['quantity', 'condition', 'notes', 'foil']
        updates = []
        values = []

        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = %s")
                values.append(data[field])

        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400

        values.append(card_id)

        with get_cursor() as cursor:
            query = f"""
                UPDATE collection
                SET {', '.join(updates)}
                WHERE id = %s
                RETURNING *
            """
            cursor.execute(query, values)
            card = cursor.fetchone()

            if not card:
                return jsonify({'error': 'Card not found'}), 404

            # If quantity is 0 or less, delete the card
            if card['quantity'] <= 0:
                cursor.execute(
                    "DELETE FROM collection WHERE id = %s",
                    [card_id]
                )
                return jsonify({'success': True, 'removed': True})

        return jsonify(dict(card))

    except Exception as e:
        print(f"Error updating card: {e}")
        return jsonify({'error': 'Failed to update card'}), 500


@collection_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get collection statistics"""
    try:
        with get_cursor() as cursor:
            # Total cards and value
            cursor.execute("""
                SELECT
                    COUNT(*) as unique_cards,
                    SUM(quantity) as total_cards,
                    SUM(price_usd * quantity) as total_value
                FROM collection
            """)
            totals = cursor.fetchone()

            # Cards by set
            cursor.execute("""
                SELECT set_code, set_name, COUNT(*) as cards, SUM(quantity) as total
                FROM collection
                GROUP BY set_code, set_name
                ORDER BY total DESC
                LIMIT 10
            """)
            by_set = cursor.fetchall()

            # Cards by rarity
            cursor.execute("""
                SELECT rarity, COUNT(*) as cards, SUM(quantity) as total
                FROM collection
                GROUP BY rarity
                ORDER BY total DESC
            """)
            by_rarity = cursor.fetchall()

            # Most valuable cards
            cursor.execute("""
                SELECT card_name, set_code, price_usd, quantity, foil
                FROM collection
                WHERE price_usd IS NOT NULL
                ORDER BY price_usd DESC
                LIMIT 10
            """)
            most_valuable = cursor.fetchall()

        return jsonify({
            'unique_cards': totals['unique_cards'] or 0,
            'total_cards': totals['total_cards'] or 0,
            'total_value': float(totals['total_value'] or 0),
            'by_set': [dict(s) for s in by_set],
            'by_rarity': [dict(r) for r in by_rarity],
            'most_valuable': [dict(c) for c in most_valuable]
        })

    except Exception as e:
        print(f"Error fetching stats: {e}")
        return jsonify({'error': 'Failed to fetch stats'}), 500
