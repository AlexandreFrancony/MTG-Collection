import { useState } from 'react';
import { Search, Plus, Loader2, Check } from 'lucide-react';
import { searchCards, addCardToCollection } from '../utils/api';
import CardImage from '../components/CardImage';

export default function CardSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [addedCards, setAddedCards] = useState(new Set());

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      setLoading(true);
      setError(null);
      const data = await searchCards(query);
      setResults(data.cards || []);
    } catch (err) {
      setError(err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddCard = async (card) => {
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

      // Reset after 2 seconds
      setTimeout(() => {
        setAddedCards((prev) => {
          const next = new Set(prev);
          next.delete(card.scryfall_id);
          return next;
        });
      }, 2000);
    } catch (err) {
      console.error('Failed to add card:', err);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Search Cards</h2>
        <p className="text-gray-400">Search the Scryfall database for cards to add to your collection.</p>
      </div>

      {/* Search form */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Search for cards... (e.g., 'Lightning Bolt', 'type:creature cmc:3')"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-mtg-gold"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-3 bg-mtg-gold text-gray-900 font-medium rounded-lg hover:bg-yellow-400 disabled:opacity-50 transition-colors"
        >
          {loading ? <Loader2 className="animate-spin" size={20} /> : 'Search'}
        </button>
      </form>

      {/* Error */}
      {error && (
        <div className="bg-red-900/50 border border-red-500 rounded-lg p-4 text-red-200">
          {error}
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div>
          <p className="text-gray-400 mb-4">{results.length} cards found</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
            {results.map((card) => (
              <div key={card.scryfall_id} className="group relative">
                <CardImage
                  src={card.image_uri}
                  alt={card.name}
                  className="card-hover rounded-lg overflow-hidden"
                />

                {/* Card info overlay */}
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <p className="text-sm font-medium truncate">{card.name}</p>
                  <p className="text-xs text-gray-400">
                    {card.set_name} • {card.rarity}
                  </p>
                  {card.price > 0 && (
                    <p className="text-xs text-green-400">${card.price.toFixed(2)}</p>
                  )}

                  <button
                    onClick={() => handleAddCard(card)}
                    disabled={addedCards.has(card.scryfall_id)}
                    className={`mt-2 w-full py-1.5 rounded flex items-center justify-center gap-1 text-sm font-medium transition-colors ${
                      addedCards.has(card.scryfall_id)
                        ? 'bg-green-600 text-white'
                        : 'bg-mtg-gold text-gray-900 hover:bg-yellow-400'
                    }`}
                  >
                    {addedCards.has(card.scryfall_id) ? (
                      <>
                        <Check size={16} /> Added
                      </>
                    ) : (
                      <>
                        <Plus size={16} /> Add
                      </>
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && query && results.length === 0 && !error && (
        <div className="text-center py-12 text-gray-400">
          <p>No cards found for "{query}"</p>
          <p className="text-sm mt-2">Try a different search term or use Scryfall syntax.</p>
        </div>
      )}
    </div>
  );
}
