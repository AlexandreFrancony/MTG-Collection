"""OCR service for reading card names from images"""
import cv2
import numpy as np
import platform
import os
import re

# Tesseract will be imported only when needed (might not be installed)
try:
    import pytesseract

    # Set Tesseract path for Windows
    if platform.system() == 'Windows':
        tesseract_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            os.path.expanduser(r'~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'),
        ]
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"Tesseract found at: {path}")
                break

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Warning: pytesseract not available. OCR features disabled.")


def resize_image_for_processing(image, max_dimension=1000):
    """Resize large images to speed up processing"""
    height, width = image.shape[:2]

    if max(height, width) <= max_dimension:
        return image

    scale = max_dimension / max(height, width)
    new_width = int(width * scale)
    new_height = int(height * scale)

    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)


def find_card_in_image(image):
    """
    Try to find and extract the card from the image using contour detection.
    Returns the extracted card image or None if not found.
    """
    # Work with a smaller image for contour detection
    small = resize_image_for_processing(image, 800)
    scale_factor = image.shape[1] / small.shape[1]

    # Convert to grayscale
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

    # Apply blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Edge detection with different thresholds
    for canny_low, canny_high in [(30, 100), (50, 150), (75, 200)]:
        edges = cv2.Canny(blurred, canny_low, canny_high)

        # Dilate to connect edges
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            continue

        # Sort by area, largest first
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        for contour in contours[:5]:  # Check top 5 contours
            # Approximate to polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # Looking for quadrilateral (4 points)
            if len(approx) == 4:
                # Check if it's roughly card-shaped (aspect ratio ~0.7)
                rect = cv2.minAreaRect(approx)
                w, h = rect[1]
                if w == 0 or h == 0:
                    continue
                aspect = min(w, h) / max(w, h)

                if 0.6 < aspect < 0.8:  # MTG cards are ~63mm x 88mm = 0.716 ratio
                    # Scale points back to original image size
                    pts = approx.reshape(4, 2) * scale_factor

                    # Apply perspective transform
                    card = extract_card_perspective(image, pts)
                    if card is not None:
                        return card

    return None


def order_points(pts):
    """Order points: top-left, top-right, bottom-right, bottom-left"""
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect


def extract_card_perspective(image, pts):
    """Extract and straighten card from image using 4 corner points"""
    try:
        rect = order_points(pts.astype("float32"))

        # Standard MTG card dimensions (scaled up for quality)
        card_width = 488  # ~63mm at 200dpi
        card_height = 680  # ~88mm at 200dpi

        dst = np.array([
            [0, 0],
            [card_width - 1, 0],
            [card_width - 1, card_height - 1],
            [0, card_height - 1]
        ], dtype="float32")

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (card_width, card_height))

        return warped
    except Exception as e:
        print(f"Perspective transform failed: {e}")
        return None


def extract_title_region(card_image):
    """
    Extract the title bar region from a properly oriented MTG card.
    Title is in the top ~12% of the card, with margins on sides.
    """
    height, width = card_image.shape[:2]

    # Title region coordinates (adjusted for MTG card layout)
    y_start = int(height * 0.045)
    y_end = int(height * 0.115)
    x_start = int(width * 0.06)
    x_end = int(width * 0.82)  # Avoid mana cost

    return card_image[y_start:y_end, x_start:x_end]


def preprocess_for_ocr(image):
    """
    Multiple preprocessing approaches for OCR.
    Returns list of processed images.
    """
    results = []

    # Ensure grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Scale up
    scaled = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

    # Method 1: Otsu threshold
    _, thresh1 = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    results.append(thresh1)

    # Method 2: Adaptive threshold
    thresh2 = cv2.adaptiveThreshold(scaled, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 15, 4)
    results.append(thresh2)

    # Method 3: CLAHE enhancement
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(scaled)
    _, thresh3 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    results.append(thresh3)

    # Method 4: Inverted
    results.append(cv2.bitwise_not(thresh1))

    # Method 5: Sharpening
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(scaled, -1, kernel)
    _, thresh5 = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    results.append(thresh5)

    return results


def clean_ocr_result(text):
    """Clean up OCR result to get potential card name"""
    if not text:
        return None

    # Take first line
    text = text.split('\n')[0].strip()

    # Remove common OCR artifacts
    text = text.replace('|', 'l').replace('1', 'l').replace('0', 'O')
    text = text.replace('—', '-').replace('–', '-')

    # Remove leading/trailing punctuation
    text = text.strip('.,;:!?[]{}()"\'-_=+<>*@#$%^&/')

    # Keep only letters, spaces, hyphens, apostrophes, commas
    text = re.sub(r'[^a-zA-Z\s\-\',]', '', text)

    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()

    # Must have at least 3 letters
    letter_count = sum(1 for c in text if c.isalpha())
    if letter_count < 3:
        return None

    return text


def run_ocr(image):
    """Run OCR with multiple configs and return best result"""
    configs = [
        '--psm 7 --oem 3',  # Single line, best engine
        '--psm 6 --oem 3',  # Block of text
        '--psm 13 --oem 3', # Raw line
        '--psm 7 --oem 1',  # LSTM only
    ]

    results = []

    for config in configs:
        try:
            text = pytesseract.image_to_string(image, config=config)
            cleaned = clean_ocr_result(text)
            if cleaned:
                # Score based on letter count and word-like structure
                score = sum(1 for c in cleaned if c.isalpha())
                # Bonus for capital letters (card names are title case)
                score += sum(2 for c in cleaned if c.isupper())
                # Bonus for reasonable length
                if 5 <= len(cleaned) <= 40:
                    score += 5
                results.append((cleaned, score))
        except Exception as e:
            print(f"OCR error with config {config}: {e}")

    if not results:
        return None

    # Return highest scoring result
    results.sort(key=lambda x: x[1], reverse=True)
    return results[0][0]


def extract_card_name_from_image(image_path):
    """
    Extract the card name from an image of a Magic card.
    Returns the detected card name or None.
    """
    if not TESSERACT_AVAILABLE:
        print("Tesseract not available")
        return None

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Failed to load image: {image_path}")
        return None

    print(f"Image loaded: {image.shape}")

    # Resize if very large
    image = resize_image_for_processing(image, 2000)
    print(f"Resized to: {image.shape}")

    best_result = None
    best_score = 0

    # Strategy 1: Try to find and extract card from image
    card = find_card_in_image(image)

    images_to_try = []
    if card is not None:
        print("Card detected and extracted")
        images_to_try.append(("extracted", card))

    # Strategy 2: Also try the full image (maybe it's already cropped)
    images_to_try.append(("full", image))

    for strategy_name, img in images_to_try:
        print(f"Trying strategy: {strategy_name}")

        # Extract title region
        title = extract_title_region(img)

        if title.size == 0:
            print("  Title region empty, skipping")
            continue

        # Preprocess
        processed_list = preprocess_for_ocr(title)

        for i, processed in enumerate(processed_list):
            result = run_ocr(processed)
            if result:
                score = sum(1 for c in result if c.isalpha())
                print(f"  Method {i+1}: '{result}' (score: {score})")

                if score > best_score:
                    best_score = score
                    best_result = result

                # Good enough, return early
                if score >= 12:
                    print(f"Good result found: '{best_result}'")
                    return best_result

    print(f"Final result: '{best_result}' (score: {best_score})")
    return best_result


def detect_binder_grid(image):
    """Detect a 3x3 grid of cards in a binder page image"""
    height, width = image.shape[:2]

    cell_width = width // 3
    cell_height = height // 3

    cards = []
    for row in range(3):
        for col in range(3):
            x_start = col * cell_width + 15
            y_start = row * cell_height + 15
            x_end = (col + 1) * cell_width - 15
            y_end = (row + 1) * cell_height - 15

            cell = image[y_start:y_end, x_start:x_end]
            cards.append(cell)

    return cards


def is_empty_slot(image):
    """Check if a binder slot appears to be empty"""
    if image is None or image.size == 0:
        return True

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    variance = np.var(gray)
    return variance < 500


def extract_cards_from_binder_page(image_path):
    """Extract and identify all cards from a binder page image"""
    if not TESSERACT_AVAILABLE:
        return [None] * 9

    image = cv2.imread(image_path)
    if image is None:
        return [None] * 9

    # Resize for faster processing
    image = resize_image_for_processing(image, 1500)

    card_cells = detect_binder_grid(image)

    card_names = []
    for i, cell in enumerate(card_cells):
        print(f"Processing binder slot {i+1}...")

        if is_empty_slot(cell):
            print(f"  Slot appears empty")
            card_names.append(None)
            continue

        # Try to find card in cell
        card = find_card_in_image(cell)
        img_to_use = card if card is not None else cell

        # Extract title and OCR
        title = extract_title_region(img_to_use)
        if title.size == 0:
            card_names.append(None)
            continue

        processed_list = preprocess_for_ocr(title)

        best_result = None
        best_score = 0

        for processed in processed_list[:3]:  # Only try first 3 methods for speed
            result = run_ocr(processed)
            if result:
                score = sum(1 for c in result if c.isalpha())
                if score > best_score:
                    best_score = score
                    best_result = result

        print(f"  Result: {best_result}")
        card_names.append(best_result)

    return card_names
