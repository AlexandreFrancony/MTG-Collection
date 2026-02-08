"""Card scanning/OCR endpoints"""
import os
import tempfile
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename
from app.services.ocr import extract_card_name_from_image, extract_cards_from_binder_page
from app.services.scryfall import get_card_by_name

scan_bp = Blueprint('scan', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@scan_bp.route('/single', methods=['POST'])
def scan_single_card():
    """
    Scan a single card image and identify it
    Expects: multipart/form-data with 'image' file
    Returns: identified card data from Scryfall
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    # Save to temp file for processing
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # Extract card name using OCR
        card_name = extract_card_name_from_image(tmp_path)

        if not card_name:
            return jsonify({
                'success': False,
                'error': 'Could not read card name from image',
                'suggestion': 'Try a clearer photo with good lighting'
            }), 200

        # Look up card on Scryfall
        card = get_card_by_name(card_name)

        if not card:
            return jsonify({
                'success': False,
                'error': f'Card not found: {card_name}',
                'detected_name': card_name,
                'suggestion': 'The OCR might have misread the name'
            }), 200

        return jsonify({
            'success': True,
            'detected_name': card_name,
            'card': card
        })

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@scan_bp.route('/binder', methods=['POST'])
def scan_binder_page():
    """
    Scan a binder page (3x3 grid) and identify all cards
    Expects: multipart/form-data with 'image' file
    Returns: array of identified cards
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    # Save to temp file for processing
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # Extract card names from binder page
        card_names = extract_cards_from_binder_page(tmp_path)

        results = []
        for i, name in enumerate(card_names):
            if name:
                card = get_card_by_name(name)
                results.append({
                    'position': i + 1,  # 1-9 for 3x3 grid
                    'detected_name': name,
                    'card': card,
                    'success': card is not None
                })
            else:
                results.append({
                    'position': i + 1,
                    'detected_name': None,
                    'card': None,
                    'success': False,
                    'error': 'Empty slot or unreadable'
                })

        successful = sum(1 for r in results if r['success'])

        return jsonify({
            'success': successful > 0,
            'total_slots': len(results),
            'identified': successful,
            'cards': results
        })

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
