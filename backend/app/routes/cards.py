"""Card search endpoints - proxies to Scryfall API"""
from flask import Blueprint, jsonify, request
from app.services.scryfall import search_cards, get_card_by_name

cards_bp = Blueprint('cards', __name__)


@cards_bp.route('/search', methods=['GET'])
def search():
    """
    Search for cards by name
    Query params:
        q: search query (card name)
    """
    query = request.args.get('q', '').strip()

    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400

    if len(query) < 2:
        return jsonify({'error': 'Query must be at least 2 characters'}), 400

    results = search_cards(query)
    return jsonify(results)


@cards_bp.route('/named', methods=['GET'])
def get_by_name():
    """
    Get a card by exact or fuzzy name
    Query params:
        name: card name (fuzzy match)
    """
    name = request.args.get('name', '').strip()

    if not name:
        return jsonify({'error': 'Query parameter "name" is required'}), 400

    card = get_card_by_name(name)

    if card is None:
        return jsonify({'error': f'Card not found: {name}'}), 404

    return jsonify(card)
