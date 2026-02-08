import { useState, useEffect } from 'react';
import { Loader2, TrendingUp, Package, DollarSign, Star } from 'lucide-react';
import { getCollectionStats } from '../utils/api';

export default function Stats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getCollectionStats();
        setStats(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="animate-spin text-mtg-gold" size={48} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/50 border border-red-500 rounded-lg p-4 text-red-200">
        {error}
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Collection Statistics</h2>

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          icon={<Package className="text-blue-400" />}
          label="Unique Cards"
          value={stats.unique_cards}
        />
        <StatCard
          icon={<TrendingUp className="text-green-400" />}
          label="Total Cards"
          value={stats.total_cards}
        />
        <StatCard
          icon={<DollarSign className="text-yellow-400" />}
          label="Total Value"
          value={`$${stats.total_value.toFixed(2)}`}
        />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* By Set */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
            <Package size={20} /> Cards by Set
          </h3>
          {stats.by_set.length === 0 ? (
            <p className="text-gray-400">No data yet</p>
          ) : (
            <div className="space-y-2">
              {stats.by_set.map((set) => (
                <div key={set.set_code} className="flex justify-between items-center">
                  <span className="text-gray-300">
                    {set.set_name || set.set_code || 'Unknown'}
                  </span>
                  <span className="text-mtg-gold font-medium">{set.total}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* By Rarity */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
            <Star size={20} /> Cards by Rarity
          </h3>
          {stats.by_rarity.length === 0 ? (
            <p className="text-gray-400">No data yet</p>
          ) : (
            <div className="space-y-2">
              {stats.by_rarity.map((rarity) => (
                <div key={rarity.rarity} className="flex justify-between items-center">
                  <span className={`rarity-${rarity.rarity} capitalize`}>
                    {rarity.rarity || 'Unknown'}
                  </span>
                  <span className="text-mtg-gold font-medium">{rarity.total}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Most valuable */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
          <DollarSign size={20} /> Most Valuable Cards
        </h3>
        {stats.most_valuable.length === 0 ? (
          <p className="text-gray-400">No priced cards yet</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-400 border-b border-gray-700">
                  <th className="pb-2">Card</th>
                  <th className="pb-2">Set</th>
                  <th className="pb-2 text-center">Qty</th>
                  <th className="pb-2 text-right">Price</th>
                </tr>
              </thead>
              <tbody>
                {stats.most_valuable.map((card, i) => (
                  <tr key={i} className="border-b border-gray-700/50">
                    <td className="py-2">
                      {card.card_name}
                      {card.foil && (
                        <span className="ml-2 text-xs bg-gradient-to-r from-purple-500 to-pink-500 text-white px-1 rounded">
                          FOIL
                        </span>
                      )}
                    </td>
                    <td className="py-2 text-gray-400 uppercase">{card.set_code}</td>
                    <td className="py-2 text-center">{card.quantity}</td>
                    <td className="py-2 text-right text-green-400">
                      ${parseFloat(card.price_usd).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ icon, label, value }) {
  return (
    <div className="bg-gray-800 rounded-lg p-4 flex items-center gap-4">
      <div className="w-12 h-12 bg-gray-700 rounded-full flex items-center justify-center">
        {icon}
      </div>
      <div>
        <p className="text-gray-400 text-sm">{label}</p>
        <p className="text-2xl font-bold">{value}</p>
      </div>
    </div>
  );
}
