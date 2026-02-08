"""Google Cloud Vision API service for card recognition"""
import os
import re
from google.cloud import vision

# Set credentials path
CREDENTIALS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                 'google-credentials.json')

# Initialize the client only if credentials exist
VISION_AVAILABLE = False
vision_client = None

if os.path.exists(CREDENTIALS_PATH):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_PATH
    try:
        vision_client = vision.ImageAnnotatorClient()
        VISION_AVAILABLE = True
        print(f"Google Cloud Vision initialized with credentials from: {CREDENTIALS_PATH}")
    except Exception as e:
        print(f"Failed to initialize Google Cloud Vision: {e}")
else:
    print(f"Google credentials not found at: {CREDENTIALS_PATH}")
    print("Google Cloud Vision features disabled.")


def clean_card_name(text):
    """
    Clean up detected text to extract a valid MTG card name.
    Card names are typically in the title bar at the top of the card.
    """
    if not text:
        return None

    # Split into lines and get the first meaningful line
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    if not lines:
        return None

    # Card name is usually the first line of detected text
    # when the card is properly oriented
    candidate = lines[0]

    # Remove common OCR artifacts and MTG-specific noise
    # Remove mana symbols that might be detected as text
    candidate = re.sub(r'\{[WUBRG0-9X/]+\}', '', candidate)

    # Remove leading/trailing punctuation and symbols
    candidate = candidate.strip('.,;:!?[]{}()"\'-_=+<>*@#$%^&/')

    # Keep only letters, spaces, hyphens, apostrophes, and commas
    # MTG card names can have these characters
    candidate = re.sub(r'[^a-zA-Z\s\-\',]', '', candidate)

    # Clean up multiple spaces
    candidate = re.sub(r'\s+', ' ', candidate).strip()

    # Must have at least 3 letters to be a valid card name
    letter_count = sum(1 for c in candidate if c.isalpha())
    if letter_count < 3:
        return None

    # Reasonable length check (longest MTG card name is ~30 chars)
    if len(candidate) > 50:
        candidate = candidate[:50]

    return candidate if candidate else None


def extract_card_name_vision(image_path):
    """
    Use Google Cloud Vision to extract the card name from an image.

    Args:
        image_path: Path to the image file

    Returns:
        Detected card name or None
    """
    if not VISION_AVAILABLE:
        print("Google Cloud Vision not available")
        return None

    try:
        # Load the image
        with open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        # Use TEXT_DETECTION for better accuracy on card text
        response = vision_client.text_detection(image=image)

        if response.error.message:
            print(f"Vision API error: {response.error.message}")
            return None

        texts = response.text_annotations

        if not texts:
            print("No text detected in image")
            return None

        # The first annotation contains all detected text
        full_text = texts[0].description
        print(f"Vision detected text:\n{full_text[:200]}...")

        # Try to extract the card name from the detected text
        card_name = clean_card_name(full_text)
        print(f"Cleaned card name: {card_name}")

        return card_name

    except Exception as e:
        print(f"Vision API error: {e}")
        return None


def extract_card_name_vision_from_bytes(image_bytes):
    """
    Use Google Cloud Vision to extract the card name from image bytes.

    Args:
        image_bytes: Raw image bytes

    Returns:
        Detected card name or None
    """
    if not VISION_AVAILABLE:
        print("Google Cloud Vision not available")
        return None

    try:
        image = vision.Image(content=image_bytes)

        response = vision_client.text_detection(image=image)

        if response.error.message:
            print(f"Vision API error: {response.error.message}")
            return None

        texts = response.text_annotations

        if not texts:
            print("No text detected in image")
            return None

        full_text = texts[0].description
        print(f"Vision detected text:\n{full_text[:200]}...")

        card_name = clean_card_name(full_text)
        print(f"Cleaned card name: {card_name}")

        return card_name

    except Exception as e:
        print(f"Vision API error: {e}")
        return None


def extract_all_text_vision(image_path):
    """
    Extract all text from an image using Google Cloud Vision.
    Returns the full OCR text for display/debugging.

    Args:
        image_path: Path to the image file

    Returns:
        Tuple of (card_name, full_ocr_text) or (None, None)
    """
    if not VISION_AVAILABLE:
        print("Google Cloud Vision not available")
        return None, None

    try:
        with open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        response = vision_client.text_detection(image=image)

        if response.error.message:
            print(f"Vision API error: {response.error.message}")
            return None, None

        texts = response.text_annotations

        if not texts:
            print("No text detected in image")
            return None, None

        full_text = texts[0].description
        card_name = clean_card_name(full_text)

        return card_name, full_text

    except Exception as e:
        print(f"Vision API error: {e}")
        return None, None
