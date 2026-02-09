import { useState } from 'react';
import { FileText, Upload, Loader2, Check, X, AlertCircle } from 'lucide-react';
import { importDecklist } from '../utils/api';
import CardImage from '../components/CardImage';

export default function Import() {
  const [decklist, setDecklist] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleImport = async (e) => {
    e.preventDefault();
    if (!decklist.trim()) return;

    try {
      setLoading(true);
      setError(null);
      setResult(null);
      const data = await importDecklist(decklist);
      setResult(data);
      // Clear decklist on success
      if (data.failed.length === 0) {
        setDecklist('');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const exampleDecklist = `4x Lightning Bolt
4x Counterspell
2x Brainstorm
1 Sol Ring
3x Path to Exile`;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Import Decklist</h2>
        <p className="text-gray-400">
          Paste a decklist to add multiple cards at once to your collection.
        </p>
      </div>

      {/* Format info */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <h3 className="font-medium text-gray-200 mb-2 flex items-center gap-2">
          <FileText size={18} />
          Supported formats
        </h3>
        <ul className="text-sm text-gray-400 space-y-1">
          <li><code className="bg-gray-700 px-1 rounded">4x Lightning Bolt</code> - quantity with 'x'</li>
          <li><code className="bg-gray-700 px-1 rounded">4 Lightning Bolt</code> - quantity with space</li>
          <li><code className="bg-gray-700 px-1 rounded">Lightning Bolt</code> - defaults to 1 copy</li>
        </ul>
        <p className="text-xs text-gray-500 mt-2">
          Lines starting with # or // are ignored. Sideboard markers are skipped.
        </p>
      </div>

      {/* Import form */}
      <form onSubmit={handleImport} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Decklist
          </label>
          <textarea
            value={decklist}
            onChange={(e) => setDecklist(e.target.value)}
            placeholder={exampleDecklist}
            rows={12}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-mtg-gold font-mono text-sm resize-y"
          />
          <p className="text-xs text-gray-500 mt-1">
            {decklist.split('\n').filter(l => l.trim() && !l.startsWith('#') && !l.startsWith('//')).length} lines
          </p>
        </div>

        <button
          type="submit"
          disabled={loading || !decklist.trim()}
          className="w-full sm:w-auto px-6 py-3 bg-mtg-gold text-gray-900 font-medium rounded-lg hover:bg-yellow-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={20} />
              Importing...
            </>
          ) : (
            <>
              <Upload size={20} />
              Import to Collection
            </>
          )}
        </button>
      </form>

      {/* Error */}
      {error && (
        <div className="bg-red-900/50 border border-red-500 rounded-lg p-4 text-red-200 flex items-start gap-3">
          <AlertCircle className="flex-shrink-0 mt-0.5" size={20} />
          <div>
            <p className="font-medium">Import failed</p>
            <p className="text-sm text-red-300">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
            <h3 className="font-medium text-gray-200 mb-3">Import Summary</h3>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="bg-green-900/30 border border-green-700 rounded-lg p-3">
                <p className="text-2xl font-bold text-green-400">{result.summary.added_count}</p>
                <p className="text-xs text-green-300">New cards</p>
              </div>
              <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-3">
                <p className="text-2xl font-bold text-blue-400">{result.summary.updated_count}</p>
                <p className="text-xs text-blue-300">Updated</p>
              </div>
              <div className="bg-red-900/30 border border-red-700 rounded-lg p-3">
                <p className="text-2xl font-bold text-red-400">{result.summary.failed_count}</p>
                <p className="text-xs text-red-300">Failed</p>
              </div>
            </div>
          </div>

          {/* Added cards */}
          {result.added.length > 0 && (
            <div>
              <h3 className="font-medium text-gray-200 mb-3 flex items-center gap-2">
                <Check className="text-green-400" size={18} />
                Added ({result.added.length})
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                {result.added.map((card) => (
                  <div key={card.id} className="relative group">
                    <CardImage
                      src={card.image_url}
                      alt={card.card_name}
                      className="rounded-lg overflow-hidden"
                    />
                    <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/90 to-transparent p-2">
                      <p className="text-xs font-medium truncate">{card.card_name}</p>
                      <p className="text-xs text-gray-400">x{card.quantity}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Updated cards */}
          {result.updated.length > 0 && (
            <div>
              <h3 className="font-medium text-gray-200 mb-3 flex items-center gap-2">
                <Check className="text-blue-400" size={18} />
                Updated ({result.updated.length})
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                {result.updated.map((item) => (
                  <div key={item.card.id} className="relative group">
                    <CardImage
                      src={item.card.image_url}
                      alt={item.card.card_name}
                      className="rounded-lg overflow-hidden"
                    />
                    <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/90 to-transparent p-2">
                      <p className="text-xs font-medium truncate">{item.card.card_name}</p>
                      <p className="text-xs text-blue-400">
                        {item.previous_quantity} + {item.added_quantity} = {item.card.quantity}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Failed cards */}
          {result.failed.length > 0 && (
            <div>
              <h3 className="font-medium text-gray-200 mb-3 flex items-center gap-2">
                <X className="text-red-400" size={18} />
                Failed ({result.failed.length})
              </h3>
              <div className="bg-red-900/20 border border-red-800 rounded-lg divide-y divide-red-800/50">
                {result.failed.map((item, index) => (
                  <div key={index} className="p-3 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-red-200">{item.name}</p>
                      <p className="text-xs text-red-400">{item.reason}</p>
                    </div>
                    <span className="text-sm text-red-300">x{item.quantity}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                These cards were not found. Check the spelling and try searching manually.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
