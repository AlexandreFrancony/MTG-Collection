"""OCR service for reading card names from images"""
import cv2
import numpy as np

# Tesseract will be imported only when needed (might not be installed)
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Warning: pytesseract not available. OCR features disabled.")


def preprocess_image_for_ocr(image):
    """
    Preprocess image to improve OCR accuracy
    - Convert to grayscale
    - Apply thresholding
    - Denoise
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Apply bilateral filter to reduce noise while keeping edges sharp
    denoised = cv2.bilateralFilter(gray, 11, 17, 17)

    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    return thresh


def extract_title_region(image):
    """
    Extract the title region from a Magic card image
    The title is typically in the top ~15% of the card
    """
    height, width = image.shape[:2]

    # Title region: top 8-18% of card, with some margin on sides
    y_start = int(height * 0.06)
    y_end = int(height * 0.16)
    x_start = int(width * 0.08)
    x_end = int(width * 0.92)

    title_region = image[y_start:y_end, x_start:x_end]
    return title_region


def extract_card_name_from_image(image_path):
    """
    Extract the card name from an image of a Magic card
    Returns the detected card name or None
    """
    if not TESSERACT_AVAILABLE:
        return None

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        return None

    # Extract title region
    title_region = extract_title_region(image)

    # Preprocess for OCR
    processed = preprocess_image_for_ocr(title_region)

    # Scale up for better OCR (Tesseract works better with larger text)
    scale_factor = 3
    scaled = cv2.resize(
        processed, None,
        fx=scale_factor, fy=scale_factor,
        interpolation=cv2.INTER_CUBIC
    )

    # Run OCR
    try:
        # Configure Tesseract for single line of text
        config = '--psm 7 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ,\'-"'
        text = pytesseract.image_to_string(scaled, config=config)

        # Clean up the result
        card_name = text.strip()

        # Remove common OCR artifacts
        card_name = card_name.replace('|', 'l')
        card_name = card_name.replace('0', 'O')
        card_name = card_name.replace('1', 'l')

        # Remove any lines after the first (might pick up mana cost symbols)
        card_name = card_name.split('\n')[0].strip()

        return card_name if card_name else None

    except Exception as e:
        print(f"OCR error: {e}")
        return None


def detect_binder_grid(image):
    """
    Detect a 3x3 grid of cards in a binder page image
    Returns list of 9 cropped card images (or None for empty slots)
    """
    height, width = image.shape[:2]

    # Assume standard 3x3 binder layout
    # Each cell is roughly 1/3 of the image
    cell_width = width // 3
    cell_height = height // 3

    cards = []
    for row in range(3):
        for col in range(3):
            x_start = col * cell_width
            y_start = row * cell_height
            x_end = x_start + cell_width
            y_end = y_start + cell_height

            # Add some padding to avoid cutting into adjacent cards
            padding = 10
            x_start = min(x_start + padding, width)
            y_start = min(y_start + padding, height)
            x_end = max(x_end - padding, 0)
            y_end = max(y_end - padding, 0)

            cell = image[y_start:y_end, x_start:x_end]
            cards.append(cell)

    return cards


def is_empty_slot(image):
    """
    Check if a binder slot appears to be empty
    Based on color variance - empty slots tend to be uniform color
    """
    if image is None or image.size == 0:
        return True

    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Check variance - low variance suggests empty/uniform slot
    variance = np.var(gray)
    return variance < 500  # Threshold determined experimentally


def extract_cards_from_binder_page(image_path):
    """
    Extract and identify all cards from a binder page image
    Returns list of 9 card names (None for empty/unreadable slots)
    """
    if not TESSERACT_AVAILABLE:
        return [None] * 9

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        return [None] * 9

    # Detect grid and extract individual cards
    card_images = detect_binder_grid(image)

    card_names = []
    for card_img in card_images:
        if is_empty_slot(card_img):
            card_names.append(None)
            continue

        # Extract title region from this card
        title_region = extract_title_region(card_img)
        processed = preprocess_image_for_ocr(title_region)

        # Scale up
        scale_factor = 3
        scaled = cv2.resize(
            processed, None,
            fx=scale_factor, fy=scale_factor,
            interpolation=cv2.INTER_CUBIC
        )

        try:
            config = '--psm 7'
            text = pytesseract.image_to_string(scaled, config=config)
            card_name = text.strip().split('\n')[0].strip()
            card_names.append(card_name if card_name else None)
        except Exception:
            card_names.append(None)

    return card_names
