import { useState, useRef } from 'react';
import { Camera, Upload, Loader2, Check, X, Plus, Search } from 'lucide-react';
import { scanSingleCard, scanBinderPage, addCardToCollection, searchCards } from '../utils/api';
import CardImage from '../components/CardImage';

export default function Scanner() {
  const [mode, setMode] = useState('single'); // 'single' or 'binder'
  const [preview, setPreview] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [addedCards, setAddedCards] = useState(new Set());
  const fileInputRef = useRef(null);

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(file);

    // Scan the image
    await scanImage(file);
  };

  const scanImage = async (file) => {
    try {
      setScanning(true);
      setError(null);
      setResults(null);

      const data = mode === 'single' ? await scanSingleCard(file) : await scanBinderPage(file);

      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setScanning(false);
    }
  };

  const handleAddCard = async (card) => {
    if (!card) return;

    try {
      await addCardToCollection({
        scryfall_id: card.scryfall_id,
        name: card.name,
        set_code: card.set_code,
        set_name: card.set_name,
        collector_number: card.collector_number,
        rarity: card.rarity,
        mana_cost: card.mana_cost,
        type_line: card.type_line,
        image_uri: card.image_uri,
        price: card.price,
        quantity: 1,
        foil: false,
      });

      setAddedCards((prev) => new Set([...prev, card.scryfall_id]));
    } catch (err) {
      console.error('Failed to add card:', err);
    }
  };

  const handleAddAll = async () => {
    if (!results) return;

    let cards = [];
    if (mode === 'single') {
      cards = results.card ? [results.card] : [];
    } else {
      // Handle both old format (card objects) and new format (result objects with .card)
      cards = (results.cards || [])
        .map((item) => (item?.card !== undefined ? item.card : item))
        .filter(Boolean);
    }

    for (const card of cards) {
      if (!addedCards.has(card.scryfall_id)) {
        await handleAddCard(card);
      }
    }
  };

  // Update a single card result from manual search
  const handleManualCardFound = (card) => {
    setResults({ ...results, card });
  };

  // Update a binder card at specific index from manual search
  const handleBinderCardFound = (index, card) => {
    const newCards = [...(results?.cards || Array(9).fill(null))];
    newCards[index] = card;
    setResults({ ...results, cards: newCards });
  };

  const reset = () => {
    setPreview(null);
    setResults(null);
    setError(null);
    setAddedCards(new Set());
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Scan Cards</h2>
        <p className="text-[var(--text-muted)]">
          Upload a photo of a card or binder page to automatically identify and add cards.
        </p>
      </div>

      {/* Mode selector */}
      <div className="flex gap-2">
        <button
          onClick={() => {
            setMode('single');
            reset();
          }}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            mode === 'single' ? 'bg-mtg-gold text-[var(--bg-primary)]' : 'bg-[var(--bg-input)] text-[var(--text-secondary)] hover:bg-[var(--border)]'
          }`}
        >
          Single Card
        </button>
        <button
          onClick={() => {
            setMode('binder');
            reset();
          }}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            mode === 'binder' ? 'bg-mtg-gold text-[var(--bg-primary)]' : 'bg-[var(--bg-input)] text-[var(--text-secondary)] hover:bg-[var(--border)]'
          }`}
        >
          Binder Page (3x3)
        </button>
      </div>

      {/* Upload area */}
      {!preview && (
        <div
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-[var(--border)] rounded-xl p-12 text-center cursor-pointer hover:border-mtg-gold hover:bg-[var(--bg-card)] transition-colors"
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handleFileSelect}
            className="hidden"
          />
          <div className="flex flex-col items-center gap-4">
            <div className="w-16 h-16 bg-[var(--bg-input)] rounded-full flex items-center justify-center">
              {mode === 'single' ? <Camera size={32} /> : <Upload size={32} />}
            </div>
            <div>
              <p className="text-lg font-medium">
                {mode === 'single' ? 'Take a photo or upload an image' : 'Upload a binder page photo'}
              </p>
              <p className="text-[var(--text-muted)] text-sm mt-1">
                {mode === 'single'
                  ? 'Point your camera at a single Magic card'
                  : 'Make sure all 9 card slots are visible'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Preview and results */}
      {preview && (
        <div className="grid md:grid-cols-2 gap-6">
          {/* Image preview */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <h3 className="font-medium">Uploaded Image</h3>
              <button onClick={reset} className="text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                Upload different image
              </button>
            </div>
            <img src={preview} alt="Uploaded" className="rounded-lg max-h-96 w-full object-contain bg-[var(--bg-card)]" />
          </div>

          {/* Results */}
          <div>
            <h3 className="font-medium mb-2">Detected Cards</h3>

            {scanning && (
              <div className="flex items-center justify-center py-12 bg-[var(--bg-card)] rounded-lg">
                <Loader2 className="animate-spin text-mtg-gold mr-2" size={24} />
                <span>Scanning image...</span>
              </div>
            )}

            {error && (
              <div className="bg-red-900/50 border border-red-500 rounded-lg p-4 text-red-200">
                <p className="font-medium">Scan failed</p>
                <p className="text-sm">{error}</p>
              </div>
            )}

            {results && mode === 'single' && (
              <SingleCardResult
                card={results.card}
                ocr_text={results.ocr_text}
                onAdd={handleAddCard}
                onManualFound={handleManualCardFound}
                added={addedCards}
              />
            )}

            {results && mode === 'binder' && (
              <BinderResults
                cards={results.cards || []}
                onAdd={handleAddCard}
                onAddAll={handleAddAll}
                onManualFound={handleBinderCardFound}
                added={addedCards}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Manual search component for when OCR fails
function ManualCardSearch({ onCardFound, placeholder = "Type card name..." }) {
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [suggestions, setSuggestions] = useState([]);

  const handleSearch = async (value) => {
    setQuery(value);

    if (value.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      setSearching(true);
      const data = await searchCards(value);
      setSuggestions(data.cards?.slice(0, 5) || []);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setSearching(false);
    }
  };

  const selectCard = (card) => {
    onCardFound(card);
    setQuery('');
    setSuggestions([]);
  };

  return (
    <div className="relative">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" size={16} />
          <input
            type="text"
            value={query}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder={placeholder}
            className="w-full pl-8 pr-3 py-2 bg-[var(--bg-input)] border border-[var(--border)] rounded text-sm focus:outline-none focus:ring-1 focus:ring-mtg-gold"
          />
          {searching && (
            <Loader2 className="absolute right-2 top-1/2 -translate-y-1/2 animate-spin text-[var(--text-muted)]" size={16} />
          )}
        </div>
      </div>

      {/* Suggestions dropdown */}
      {suggestions.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-[var(--bg-input)] border border-[var(--border)] rounded-lg shadow-lg overflow-hidden">
          {suggestions.map((card) => (
            <button
              key={card.scryfall_id}
              onClick={() => selectCard(card)}
              className="w-full flex items-center gap-2 p-2 hover:bg-[var(--bg-card)] text-left"
            >
              <img src={card.image_uri} alt="" className="w-8 h-11 object-cover rounded" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{card.name}</p>
                <p className="text-xs text-[var(--text-muted)]">{card.set_name}</p>
              </div>
              {card.price > 0 && (
                <span className="text-xs text-green-400">{card.price.toFixed(2)}€</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function SingleCardResult({ card, ocr_text, onAdd, onManualFound, added }) {
  if (!card) {
    return (
      <div className="bg-[var(--bg-card)] rounded-lg p-4 space-y-4">
        <div className="flex items-center gap-2 text-yellow-400">
          <X size={20} />
          <span className="font-medium">Could not identify card</span>
        </div>
        {ocr_text && (
          <p className="text-sm text-[var(--text-muted)]">
            OCR detected: "{ocr_text}"
          </p>
        )}

        {/* Manual search fallback */}
        <div>
          <p className="text-sm text-[var(--text-secondary)] mb-2">Search manually:</p>
          <ManualCardSearch onCardFound={onManualFound} />
        </div>
      </div>
    );
  }

  const isAdded = added.has(card.scryfall_id);

  return (
    <div className="bg-[var(--bg-card)] rounded-lg p-4">
      <div className="flex gap-4">
        <CardImage src={card.image_uri} alt={card.name} className="w-32 rounded" />
        <div className="flex-1">
          <h4 className="font-bold text-lg">{card.name}</h4>
          <p className="text-[var(--text-muted)] text-sm">{card.set_name}</p>
          <p className="text-[var(--text-muted)] text-sm">{card.type_line}</p>
          {card.price > 0 && <p className="text-green-400 mt-2">{card.price.toFixed(2)}€</p>}

          <button
            onClick={() => onAdd(card)}
            disabled={isAdded}
            className={`mt-4 px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors ${
              isAdded ? 'bg-green-600 text-white' : 'bg-mtg-gold text-[var(--bg-primary)] hover:bg-yellow-400'
            }`}
          >
            {isAdded ? (
              <>
                <Check size={18} /> Added to Collection
              </>
            ) : (
              <>
                <Plus size={18} /> Add to Collection
              </>
            )}
          </button>

          {/* Option to search for different card */}
          <div className="mt-3 pt-3 border-t border-[var(--border)]">
            <p className="text-xs text-[var(--text-muted)] mb-2">Wrong card? Search manually:</p>
            <ManualCardSearch onCardFound={onManualFound} placeholder="Search different card..." />
          </div>
        </div>
      </div>
    </div>
  );
}

function BinderResults({ cards, onAdd, onAddAll, onManualFound, added }) {
  const [editingIndex, setEditingIndex] = useState(null);

  // Handle both old format (card objects directly) and new format (result objects with .card property)
  const normalizedCards = cards.map((item) => {
    if (!item) return null;
    // New format: { position, success, card, ... }
    if (item.card !== undefined) return item.card;
    // Old format: direct card object
    return item;
  });

  const validCards = normalizedCards.filter(Boolean);
  const allAdded = validCards.length > 0 && validCards.every((c) => added.has(c.scryfall_id));

  return (
    <div className="space-y-4">
      {validCards.length > 0 && (
        <button
          onClick={onAddAll}
          disabled={allAdded}
          className={`w-full py-2 rounded-lg font-medium flex items-center justify-center gap-2 transition-colors ${
            allAdded ? 'bg-green-600 text-white' : 'bg-mtg-gold text-[var(--bg-primary)] hover:bg-yellow-400'
          }`}
        >
          {allAdded ? (
            <>
              <Check size={18} /> All Cards Added
            </>
          ) : (
            <>
              <Plus size={18} /> Add All {validCards.length} Cards
            </>
          )}
        </button>
      )}

      <div className="grid grid-cols-3 gap-2">
        {normalizedCards.map((card, index) => (
          <div key={index} className="aspect-[2.5/3.5] bg-[var(--bg-card)] rounded relative overflow-hidden">
            {card ? (
              <>
                <CardImage src={card.image_uri} alt={card.name} className="w-full h-full object-cover" />
                {added.has(card.scryfall_id) && (
                  <div className="absolute inset-0 bg-green-600/50 flex items-center justify-center">
                    <Check size={24} className="text-white" />
                  </div>
                )}
                <div className="absolute bottom-1 right-1 flex gap-1">
                  <button
                    onClick={() => setEditingIndex(index)}
                    className="p-1 bg-[var(--bg-input)] text-[var(--text-secondary)] rounded text-xs hover:bg-[var(--border)]"
                    title="Search different card"
                  >
                    <Search size={12} />
                  </button>
                  <button
                    onClick={() => onAdd(card)}
                    disabled={added.has(card.scryfall_id)}
                    className="p-1 bg-mtg-gold text-[var(--bg-primary)] rounded disabled:opacity-50"
                  >
                    <Plus size={16} />
                  </button>
                </div>
              </>
            ) : (
              <div
                className="w-full h-full flex flex-col items-center justify-center text-[var(--text-muted)] text-xs text-center p-2 cursor-pointer hover:bg-[var(--bg-input)]"
                onClick={() => setEditingIndex(index)}
              >
                <Search size={20} className="mb-1" />
                <span>Click to search</span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Manual search modal for binder slot */}
      {editingIndex !== null && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--bg-card)] rounded-lg p-4 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h4 className="font-medium">Search Card for Slot {editingIndex + 1}</h4>
              <button
                onClick={() => setEditingIndex(null)}
                className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              >
                <X size={20} />
              </button>
            </div>
            <ManualCardSearch
              onCardFound={(card) => {
                onManualFound(editingIndex, card);
                setEditingIndex(null);
              }}
              placeholder="Type card name..."
            />
          </div>
        </div>
      )}
    </div>
  );
}
