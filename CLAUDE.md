# MTG Collection Tracker - Project Instructions

## Project Overview
A Magic: The Gathering card collection tracker with image recognition. Users can photograph cards (single or binder pages) and the app identifies and adds them to their collection.

## Tech Stack
- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: Python Flask (for image processing with OpenCV/Tesseract)
- **Database**: PostgreSQL
- **Card Data**: Scryfall API
- **Deployment**: Docker on Raspberry Pi 4

## Architecture
```
MTG-Collection/
├── backend/              # Python Flask API
│   ├── app/
│   │   ├── __init__.py   # App factory
│   │   ├── db.py         # Database utilities
│   │   ├── routes/       # API endpoints
│   │   │   ├── health.py
│   │   │   ├── cards.py
│   │   │   ├── collection.py
│   │   │   └── scan.py
│   │   └── services/     # Business logic
│   │       ├── scryfall.py  # Scryfall API client
│   │       └── ocr.py       # Image processing
│   ├── run.py            # Entry point
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/             # React app
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── utils/
│   ├── package.json
│   └── Dockerfile
├── database/
│   └── init.sql          # Schema initialization
├── docker-compose.yml
└── CLAUDE.md
```

## API Endpoints

### Health
- `GET /api/health` - Health check

### Cards (Scryfall proxy)
- `GET /api/cards/search?q=query` - Search cards
- `GET /api/cards/named?name=cardname` - Get card by name (fuzzy)

### Collection
- `GET /api/collection` - List all cards (supports ?search=, ?set=)
- `POST /api/collection` - Add card to collection
- `DELETE /api/collection/:id` - Remove card
- `PATCH /api/collection/:id` - Update card (quantity, condition, notes)
- `GET /api/collection/stats` - Collection statistics

### Scanning
- `POST /api/scan/single` - Scan single card image
- `POST /api/scan/binder` - Scan 3x3 binder page

## Key Features (MVP)
1. Upload photo of card → identify via OCR → match on Scryfall
2. Binder page detection (3x3 grid) → identify each card
3. Collection management (view, search, filter)
4. Collection value tracking (via Scryfall prices)

## Scryfall API
- Free, no API key required
- Rate limit: 10 requests/second
- Card search: `GET https://api.scryfall.com/cards/search?q=name`
- Card by name: `GET https://api.scryfall.com/cards/named?fuzzy=name`

## Development

### Local Setup
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python run.py

# Frontend
cd frontend
npm install
npm run dev
```

### Docker
```bash
docker-compose up -d
```

## Ports
- Frontend: 5051 (5173 in dev)
- Backend: 5050
- Database: 5433

## Development Notes
- Use Python for backend (better OCR/image libraries than Node)
- Tesseract for OCR (read card names from photos)
- OpenCV for grid detection on binder pages
- Cache Scryfall data locally to reduce API calls
- Rate limit Scryfall requests to 10/second max
