# MTG Collection Tracker

A Magic: The Gathering card collection tracker with Scryfall integration. Search cards, manage your collection, track value, and import decklists.

[![Live](https://img.shields.io/badge/live-mtg.francony.fr-brightgreen)](https://mtg.francony.fr)

## Features

- **Card Search** - Search the entire MTG card database via Scryfall API
- **Collection Management** - Add, remove, and update cards in your collection
- **Decklist Import** - Paste a decklist to bulk-add cards (supports MTGO/Arena format)
- **Collection Statistics** - Track total cards, unique cards, value, and breakdowns by set/rarity
- **Price Tracking** - Automatic price updates from Scryfall
- **Card Conditions** - Track foil status and card conditions (NM, LP, MP, etc.)

## Tech Stack

- **Frontend**: React 18 + Vite + Tailwind CSS
- **Backend**: Python Flask
- **Database**: PostgreSQL 15
- **Card Data**: Scryfall API (free, no key required)
- **Deployment**: Docker on Raspberry Pi 4

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Raspberry Pi 4                         │
├─────────────────────────────────────────────────────────────┤
│  Central Infra (nginx-proxy)                                │
│       │                                                     │
│       ├── mtg.francony.fr ──┐                              │
│       │                     ▼                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  mtg_network                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │   │
│  │  │ PostgreSQL│  │  Flask   │  │   Nginx (React)   │  │   │
│  │  │    DB    │◄─┤   API    │◄─┤  + API Proxy      │  │   │
│  │  │  :5432   │  │  :5050   │  │  :80              │  │   │
│  │  └──────────┘  └──────────┘  └───────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
MTG-Collection/
├── backend/                  # Python Flask API
│   ├── app/
│   │   ├── __init__.py      # App factory
│   │   ├── db.py            # Database utilities
│   │   ├── routes/          # API endpoints
│   │   │   ├── health.py    # Health check
│   │   │   ├── cards.py     # Scryfall proxy
│   │   │   └── collection.py # Collection CRUD + import
│   │   └── services/
│   │       └── scryfall.py  # Scryfall API client
│   ├── run.py               # Entry point
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # React app
│   ├── src/
│   │   ├── components/
│   │   │   └── CardImage.jsx
│   │   ├── pages/
│   │   │   ├── Collection.jsx  # Collection view
│   │   │   ├── CardSearch.jsx  # Card search
│   │   │   ├── Scanner.jsx     # Card scanner (WIP)
│   │   │   ├── Import.jsx      # Decklist import
│   │   │   └── Stats.jsx       # Collection statistics
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── Dockerfile
├── database/
│   └── init.sql              # Schema initialization
├── docker-compose.yml
├── .env.example
└── README.md
```

## API Endpoints

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |

### Cards (Scryfall Proxy)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cards/search?q=query` | Search cards on Scryfall |
| GET | `/api/cards/named?name=cardname` | Get card by name (fuzzy match) |

### Collection
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/collection` | List all cards (supports `?search=`, `?set=`) |
| POST | `/api/collection` | Add card to collection |
| DELETE | `/api/collection/:id` | Remove card |
| PATCH | `/api/collection/:id` | Update card (quantity, condition, notes, foil) |
| GET | `/api/collection/stats` | Collection statistics |
| POST | `/api/collection/import` | Import decklist (bulk add) |

### Decklist Import Format

The import endpoint accepts decklists in standard format:
```
4x Lightning Bolt
4 Counterspell
Brainstorm
# Comments are ignored
// So are these
```

## Pages

| Route | Description |
|-------|-------------|
| `/` | Collection view with search and filters |
| `/search` | Search Scryfall for cards to add |
| `/import` | Paste decklist to bulk import |
| `/stats` | Collection statistics and breakdowns |
| `/scan` | Card scanner (work in progress) |

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Or: Python 3.11+, Node.js 20+, PostgreSQL 15+

### With Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/AlexandreFrancony/MTG-Collection.git
cd MTG-Collection

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Start the stack
docker compose up -d
```

The app will be available at `http://localhost:5051`.

### Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python run.py

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | Database user | `mtg` |
| `POSTGRES_PASSWORD` | Database password | Required |
| `POSTGRES_DB` | Database name | `mtg_collection` |
| `DATABASE_URL` | Full connection string | Auto-generated |

## Docker Stack

| Service | Image | Port | Health Check |
|---------|-------|------|--------------|
| `mtg-db` | PostgreSQL 15-alpine | 5433 (internal) | `pg_isready` |
| `mtg-backend` | Python Flask | 5050 (internal) | `/api/health` |
| `mtg-frontend` | Nginx + React | 5051 | HTTP 200 |

## Database Schema

### Collection Table

```sql
CREATE TABLE collection (
    id SERIAL PRIMARY KEY,
    scryfall_id VARCHAR(36) NOT NULL,
    card_name VARCHAR(255) NOT NULL,
    set_code VARCHAR(10),
    set_name VARCHAR(255),
    collector_number VARCHAR(20),
    rarity VARCHAR(20),
    mana_cost VARCHAR(100),
    type_line VARCHAR(255),
    image_url TEXT,
    price_usd DECIMAL(10, 2),
    quantity INTEGER NOT NULL DEFAULT 1,
    foil BOOLEAN NOT NULL DEFAULT FALSE,
    condition VARCHAR(10) DEFAULT 'NM',
    notes TEXT,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Scryfall API

This app uses the [Scryfall API](https://scryfall.com/docs/api) for card data:
- Free, no API key required
- Rate limit: 10 requests/second (respected by the backend)
- Card search: `GET https://api.scryfall.com/cards/search?q=name`
- Card by name: `GET https://api.scryfall.com/cards/named?fuzzy=name`

## Deployment

### Automatic (via GitHub Webhook)

Push to `main` branch triggers automatic deployment via the central [Infra](https://github.com/AlexandreFrancony/Infra) webhook server.

### Manual

```bash
cd ~/Hosting/MTG-Collection
git pull
docker compose up -d --build
```

## Related Repositories

- [Infra](https://github.com/AlexandreFrancony/Infra) - Central reverse proxy & webhook
- [Bartending (Tipsy)](https://github.com/AlexandreFrancony/Bartending_Deploy) - Cocktail ordering app

## Future Features

- [ ] Card scanner with OCR (Tesseract + OpenCV)
- [ ] Binder page detection (3x3 grid)
- [ ] Price history tracking
- [ ] Deck builder
- [ ] Trade list management

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
