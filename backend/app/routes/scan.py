"""Card scanning endpoints using Google Cloud Vision"""
import os
import tempfile
import cv2
import numpy as np
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename
from app.services.vision import extract_all_text_vision, VISION_AVAILABLE
from app.services.scryfall import get_card_by_name

scan_bp = Blueprint('scan', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def split_binder_image(image_path, rows=3, cols=3):
    """
    Split a binder page image into individual card cells.
    Returns a list of temporary file paths for each cell.
    """
    img = cv2.imread(image_path)
    if img is None:
        return []

    height, width = img.shape[:2]
    cell_height = height // rows
    cell_width = width // cols

    cell_paths = []

    for row in range(rows):
        for col in range(cols):
            # Calculate cell boundaries
            y1 = row * cell_height
            y2 = (row + 1) * cell_height
            x1 = col * cell_width
            x2 = (col + 1) * cell_width

            # Extract cell
            cell = img[y1:y2, x1:x2]

            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                cv2.imwrite(tmp.name, cell)
                cell_paths.append(tmp.name)

    return cell_paths


@scan_bp.route('/single', methods=['POST'])
def scan_single_card():
    """
    Scan a single card image and identify it using Google Cloud Vision.
    Expects: multipart/form-data with 'image' file
    Returns: identified card data from Scryfall
    """
    if not VISION_AVAILABLE:
        return jsonify({
            'error': 'Google Cloud Vision not configured. Check server logs.',
            'success': False
        }), 503

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
        # Extract card name using Google Cloud Vision
        card_name, ocr_text = extract_all_text_vision(tmp_path)

        if not card_name:
            return jsonify({
                'success': False,
                'card': None,
                'ocr_text': ocr_text[:100] if ocr_text else None,
                'error': 'Could not read card name from image',
                'suggestion': 'Try a clearer photo with good lighting'
            }), 200

        # Look up card on Scryfall
        card = get_card_by_name(card_name)

        if not card:
            return jsonify({
                'success': False,
                'card': None,
                'ocr_text': card_name,
                'error': f'Card not found: {card_name}',
                'suggestion': 'The card name might have been misread'
            }), 200

        return jsonify({
            'success': True,
            'ocr_text': card_name,
            'card': card
        })

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@scan_bp.route('/binder', methods=['POST'])
def scan_binder_page():
    """
    Scan a binder page (3x3 grid) and identify all cards.
    Splits the image into 9 cells and scans each individually.

    Expects: multipart/form-data with 'image' file
    Returns: array of 9 card slots with identification results
    """
    if not VISION_AVAILABLE:
        return jsonify({
            'error': 'Google Cloud Vision not configured. Check server logs.',
            'success': False
        }), 503

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

    cell_paths = []

    try:
        # Split image into 9 cells (3x3 grid)
        cell_paths = split_binder_image(tmp_path, rows=3, cols=3)

        if len(cell_paths) != 9:
            return jsonify({
                'success': False,
                'error': 'Failed to split binder image into grid',
                'cards': [None] * 9
            }), 200

        results = []

        # Scan each cell
        for i, cell_path in enumerate(cell_paths):
            card_name, ocr_text = extract_all_text_vision(cell_path)

            if card_name:
                card = get_card_by_name(card_name)
                if card:
                    results.append({
                        'position': i,
                        'success': True,
                        'card': card,
                        'ocr_text': card_name
                    })
                else:
                    results.append({
                        'position': i,
                        'success': False,
                        'card': None,
                        'ocr_text': card_name,
                        'error': f'Card not found: {card_name}'
                    })
            else:
                results.append({
                    'position': i,
                    'success': False,
                    'card': None,
                    'ocr_text': ocr_text[:50] if ocr_text else None,
                    'error': 'Empty slot or unreadable'
                })

        successful = sum(1 for r in results if r['success'])

        return jsonify({
            'success': successful > 0,
            'total_slots': 9,
            'identified': successful,
            'cards': results
        })

    finally:
        # Clean up temp files
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        for cell_path in cell_paths:
            if os.path.exists(cell_path):
                os.unlink(cell_path)


@scan_bp.route('/status', methods=['GET'])
def scan_status():
    """Check if scanning is available"""
    return jsonify({
        'vision_available': VISION_AVAILABLE,
        'service': 'Google Cloud Vision' if VISION_AVAILABLE else 'Not configured'
    })
