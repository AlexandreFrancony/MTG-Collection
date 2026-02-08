import { useState, useEffect } from 'react';
import { Search, Plus, Minus, Trash2, Loader2 } from 'lucide-react';
import { getCollection, updateCardInCollection, removeCardFromCollection } from '../utils/api';
import CardImage from '../components/CardImage';

export default function Collection() {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [stats, setStats] = useState({ unique_cards: 0, total_cards: 0, total_value: 0 });

  const fetchCollection = async () => {
    try {
      setLoading(true);
      const data = await getCollection({ search });
      setCards(data.cards);
      setStats({
        unique_cards: data.unique_cards,
        total_cards: data.total_cards,
        total_value: data.total_value,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCollection();
  }, [search]);

  const handleQuantityChange = async (cardId, delta) => {
    const card = cards.find((c) => c.id === cardId);
    if (!card) return;

    const newQuantity = card.quantity + delta;

    try {
      if (newQuantity <= 0) {
        await removeCardFromCollection(cardId);
        setCards(cards.filter((c) => c.id !== cardId));
      } else {
        await updateCardInCollection(cardId, { quantity: newQuantity });
        setCards(cards.map((c) => (c.id === cardId ? { ...c, quantity: newQuantity } : c)));
      }
    } catch (err) {
      console.error('Failed to update quantity:', err);
    }
  };

  const handleDelete = async (cardId) => {
    if (!confirm('Remove this card from your collection?')) return;

    try {
      await removeCardFromCollection(cardId);
      setCards(cards.filter((c) => c.id !== cardId));
    } catch (err) {
      console.error('Failed to delete card:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with stats */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
        <div>
          <h2 className="text-2xl font-bold">My Collection</h2>
          <p className="text-gray-400">
            {stats.unique_cards} unique cards • {stats.total_cards} total •{' '}
            <span className="text-green-400">{stats.total_value.toFixed(2)}€</span>
          </p>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-auto">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Search collection..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full sm:w-64 pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-mtg-gold"
          />
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="flex justify-center py-12">
          <Loader2 className="animate-spin text-mtg-gold" size={48} />
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-red-900/50 border border-red-500 rounded-lg p-4 text-red-200">
          {error}
        </div>
      )}

      {/* Empty state */}
      {!loading && cards.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <p className="text-lg">No cards in your collection yet.</p>
          <p>Use the Search or Scan features to add cards!</p>
        </div>
      )}

      {/* Card grid */}
      {!loading && cards.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {cards.map((card) => (
            <div key={card.id} className="group relative">
              <CardImage
                src={card.image_url}
                alt={card.card_name}
                className="card-hover rounded-lg overflow-hidden"
              />

              {/* Quantity badge */}
              <div className="absolute top-2 right-2 bg-black/80 text-white px-2 py-1 rounded-full text-sm font-bold">
                ×{card.quantity}
              </div>

              {/* Foil indicator */}
              {card.foil && (
                <div className="absolute top-2 left-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-2 py-0.5 rounded-full text-xs">
                  FOIL
                </div>
              )}

              {/* Hover controls */}
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <p className="text-sm font-medium truncate mb-2">{card.card_name}</p>
                <div className="flex justify-between items-center">
                  <div className="flex gap-1">
                    <button
                      onClick={() => handleQuantityChange(card.id, -1)}
                      className="p-1 bg-gray-700 hover:bg-gray-600 rounded"
                    >
                      <Minus size={16} />
                    </button>
                    <button
                      onClick={() => handleQuantityChange(card.id, 1)}
                      className="p-1 bg-gray-700 hover:bg-gray-600 rounded"
                    >
                      <Plus size={16} />
                    </button>
                  </div>
                  <button
                    onClick={() => handleDelete(card.id)}
                    className="p-1 bg-red-600 hover:bg-red-500 rounded"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
