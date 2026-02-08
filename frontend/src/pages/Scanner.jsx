import { useState, useRef } from 'react';
import { Camera, Upload, Loader2, Check, X, Plus } from 'lucide-react';
import { scanSingleCard, scanBinderPage, addCardToCollection } from '../utils/api';
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

    const cards = mode === 'single' ? (results.card ? [results.card] : []) : results.cards?.filter(Boolean) || [];

    for (const card of cards) {
      if (!addedCards.has(card.scryfall_id)) {
        await handleAddCard(card);
      }
    }
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
        <p className="text-gray-400">
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
            mode === 'single' ? 'bg-mtg-gold text-gray-900' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
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
            mode === 'binder' ? 'bg-mtg-gold text-gray-900' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          Binder Page (3×3)
        </button>
      </div>

      {/* Upload area */}
      {!preview && (
        <div
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-gray-600 rounded-xl p-12 text-center cursor-pointer hover:border-mtg-gold hover:bg-gray-800/50 transition-colors"
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
            <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center">
              {mode === 'single' ? <Camera size={32} /> : <Upload size={32} />}
            </div>
            <div>
              <p className="text-lg font-medium">
                {mode === 'single' ? 'Take a photo or upload an image' : 'Upload a binder page photo'}
              </p>
              <p className="text-gray-400 text-sm mt-1">
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
              <button onClick={reset} className="text-sm text-gray-400 hover:text-white">
                Upload different image
              </button>
            </div>
            <img src={preview} alt="Uploaded" className="rounded-lg max-h-96 w-full object-contain bg-gray-800" />
          </div>

          {/* Results */}
          <div>
            <h3 className="font-medium mb-2">Detected Cards</h3>

            {scanning && (
              <div className="flex items-center justify-center py-12 bg-gray-800 rounded-lg">
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
              <SingleCardResult card={results.card} ocr_text={results.ocr_text} onAdd={handleAddCard} added={addedCards} />
            )}

            {results && mode === 'binder' && (
              <BinderResults cards={results.cards || []} onAdd={handleAddCard} onAddAll={handleAddAll} added={addedCards} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function SingleCardResult({ card, ocr_text, onAdd, added }) {
  if (!card) {
    return (
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex items-center gap-2 text-yellow-400 mb-2">
          <X size={20} />
          <span className="font-medium">Could not identify card</span>
        </div>
        <p className="text-sm text-gray-400">
          OCR detected: "{ocr_text || 'nothing'}"
        </p>
        <p className="text-sm text-gray-400 mt-2">
          Try taking a clearer photo with good lighting.
        </p>
      </div>
    );
  }

  const isAdded = added.has(card.scryfall_id);

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex gap-4">
        <CardImage src={card.image_uri} alt={card.name} className="w-32 rounded" />
        <div className="flex-1">
          <h4 className="font-bold text-lg">{card.name}</h4>
          <p className="text-gray-400 text-sm">{card.set_name}</p>
          <p className="text-gray-400 text-sm">{card.type_line}</p>
          {card.price > 0 && <p className="text-green-400 mt-2">${card.price.toFixed(2)}</p>}

          <button
            onClick={() => onAdd(card)}
            disabled={isAdded}
            className={`mt-4 px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors ${
              isAdded ? 'bg-green-600 text-white' : 'bg-mtg-gold text-gray-900 hover:bg-yellow-400'
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
        </div>
      </div>
    </div>
  );
}

function BinderResults({ cards, onAdd, onAddAll, added }) {
  const validCards = cards.filter(Boolean);
  const allAdded = validCards.every((c) => added.has(c.scryfall_id));

  return (
    <div className="space-y-4">
      {validCards.length > 0 && (
        <button
          onClick={onAddAll}
          disabled={allAdded}
          className={`w-full py-2 rounded-lg font-medium flex items-center justify-center gap-2 transition-colors ${
            allAdded ? 'bg-green-600 text-white' : 'bg-mtg-gold text-gray-900 hover:bg-yellow-400'
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
        {cards.map((card, index) => (
          <div key={index} className="aspect-[2.5/3.5] bg-gray-800 rounded relative overflow-hidden">
            {card ? (
              <>
                <CardImage src={card.image_uri} alt={card.name} className="w-full h-full object-cover" />
                {added.has(card.scryfall_id) && (
                  <div className="absolute inset-0 bg-green-600/50 flex items-center justify-center">
                    <Check size={24} className="text-white" />
                  </div>
                )}
                <button
                  onClick={() => onAdd(card)}
                  disabled={added.has(card.scryfall_id)}
                  className="absolute bottom-1 right-1 p-1 bg-mtg-gold text-gray-900 rounded opacity-0 hover:opacity-100 transition-opacity disabled:opacity-0"
                >
                  <Plus size={16} />
                </button>
              </>
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-600 text-xs text-center p-2">
                Empty or unreadable
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
