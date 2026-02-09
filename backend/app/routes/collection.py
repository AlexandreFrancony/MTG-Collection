"""Collection management endpoints - PostgreSQL storage"""
import re
from flask import Blueprint, jsonify, request
from app.db import get_cursor
from app.services.scryfall import get_card_by_name

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


def parse_decklist(text):
    """
    Parse a decklist text into a list of (quantity, card_name) tuples.
    Supports formats:
        - "4x Lightning Bolt"
        - "4 Lightning Bolt"
        - "Lightning Bolt" (defaults to 1)
    Ignores empty lines and lines starting with # or //
    """
    lines = text.strip().split('\n')
    cards = []

    # Pattern: optional quantity (with optional 'x'), then card name
    pattern = re.compile(r'^(\d+)x?\s+(.+)$', re.IGNORECASE)

    for line in lines:
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith('#') or line.startswith('//'):
            continue

        # Skip sideboard markers
        if line.lower() in ['sideboard', 'sideboard:', 'sb:', 'maindeck', 'maindeck:', 'md:']:
            continue

        match = pattern.match(line)
        if match:
            quantity = int(match.group(1))
            card_name = match.group(2).strip()
        else:
            # No quantity specified, default to 1
            quantity = 1
            card_name = line

        if card_name:
            cards.append((quantity, card_name))

    return cards


@collection_bp.route('/import', methods=['POST'])
def import_decklist():
    """
    Import a decklist into the collection.
    Expects JSON body with 'decklist' field containing the decklist text.
    Format: "<quantity>x <card name>" or "<quantity> <card name>" per line.

    Returns:
        - added: list of successfully added cards
        - failed: list of cards that couldn't be found
        - updated: list of cards whose quantity was updated (already in collection)
    """
    data = request.json

    if not data or 'decklist' not in data:
        return jsonify({'error': 'Request body must contain "decklist" field'}), 400

    decklist_text = data['decklist']
    if not decklist_text or not decklist_text.strip():
        return jsonify({'error': 'Decklist cannot be empty'}), 400

    # Parse the decklist
    parsed_cards = parse_decklist(decklist_text)

    if not parsed_cards:
        return jsonify({'error': 'No valid cards found in decklist'}), 400

    added = []
    updated = []
    failed = []

    with get_cursor() as cursor:
        for quantity, card_name in parsed_cards:
            # Look up the card on Scryfall
            card_data = get_card_by_name(card_name)

            if not card_data:
                failed.append({
                    'name': card_name,
                    'quantity': quantity,
                    'reason': 'Card not found on Scryfall'
                })
                continue

            # Check if card already exists in collection
            cursor.execute(
                "SELECT * FROM collection WHERE scryfall_id = %s AND foil = %s",
                (card_data['scryfall_id'], False)
            )
            existing = cursor.fetchone()

            if existing:
                # Update quantity
                new_quantity = existing['quantity'] + quantity
                cursor.execute(
                    "UPDATE collection SET quantity = %s WHERE id = %s RETURNING *",
                    (new_quantity, existing['id'])
                )
                result = dict(cursor.fetchone())
                if result.get('price_usd'):
                    result['price_usd'] = float(result['price_usd'])
                updated.append({
                    'card': result,
                    'added_quantity': quantity,
                    'previous_quantity': existing['quantity']
                })
            else:
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
                    card_data['scryfall_id'],
                    card_data['name'],
                    card_data.get('set_code'),
                    card_data.get('set_name'),
                    card_data.get('collector_number'),
                    card_data.get('rarity'),
                    card_data.get('mana_cost'),
                    card_data.get('type_line'),
                    card_data.get('image_uri'),
                    card_data.get('price'),
                    quantity,
                    False,  # foil
                    'NM',   # condition
                    None    # notes
                ))
                result = dict(cursor.fetchone())
                if result.get('price_usd'):
                    result['price_usd'] = float(result['price_usd'])
                added.append(result)

    return jsonify({
        'added': added,
        'updated': updated,
        'failed': failed,
        'summary': {
            'total_lines': len(parsed_cards),
            'added_count': len(added),
            'updated_count': len(updated),
            'failed_count': len(failed)
        }
    })
