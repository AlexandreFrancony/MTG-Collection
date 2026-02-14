import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { Library, Search, Camera, FileText, BarChart3 } from 'lucide-react';
import Collection from './pages/Collection';
import CardSearch from './pages/CardSearch';
import Scanner from './pages/Scanner';
import Import from './pages/Import';
import Stats from './pages/Stats';
import { checkCredentials, isAuthenticated, clearAuth } from './utils/api';

function LoginScreen() {
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError(false);
    setLoading(true);
    const ok = await checkCredentials(user, pass);
    setLoading(false);
    if (ok) {
      window.dispatchEvent(new Event('auth-changed'));
    } else {
      setError(true);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-8 w-full max-w-sm">
        <h2 className="text-2xl font-bold text-mtg-gold mb-2 flex items-center gap-2">
          🎴 MTG Collection
        </h2>
        <p className="text-gray-400 text-sm mb-6">Authentification requise</p>
        <form onSubmit={handleLogin}>
          <input
            type="text"
            placeholder="Utilisateur"
            value={user}
            onChange={(e) => setUser(e.target.value)}
            className="w-full p-2 rounded-lg mb-3 bg-gray-900 border border-gray-600 text-gray-100 focus:border-mtg-gold focus:outline-none"
          />
          <input
            type="password"
            placeholder="Mot de passe"
            value={pass}
            onChange={(e) => setPass(e.target.value)}
            className="w-full p-2 rounded-lg mb-4 bg-gray-900 border border-gray-600 text-gray-100 focus:border-mtg-gold focus:outline-none"
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 rounded-lg font-semibold bg-mtg-gold text-gray-900 hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {loading ? 'Connexion...' : 'Connexion'}
          </button>
          {error && (
            <p className="text-red-400 text-sm mt-2">Identifiants incorrects</p>
          )}
        </form>
      </div>
    </div>
  );
}

function App() {
  const [authed, setAuthed] = useState(isAuthenticated());

  useEffect(() => {
    const onChanged = () => setAuthed(isAuthenticated());
    const onExpired = () => {
      clearAuth();
      setAuthed(false);
    };
    window.addEventListener('auth-changed', onChanged);
    window.addEventListener('auth-expired', onExpired);
    return () => {
      window.removeEventListener('auth-changed', onChanged);
      window.removeEventListener('auth-expired', onExpired);
    };
  }, []);

  if (!authed) {
    return <LoginScreen />;
  }

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-900">
        {/* Header */}
        <header className="bg-gray-800 border-b border-gray-700 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 py-3">
            <div className="flex items-center justify-between">
              <h1 className="text-xl font-bold text-mtg-gold flex items-center gap-2">
                🎴 MTG Collection
              </h1>
              <nav className="flex gap-1">
                <NavItem to="/" icon={<Library size={20} />} label="Collection" />
                <NavItem to="/search" icon={<Search size={20} />} label="Search" />
                <NavItem to="/scan" icon={<Camera size={20} />} label="Scan" />
                <NavItem to="/import" icon={<FileText size={20} />} label="Import" />
                <NavItem to="/stats" icon={<BarChart3 size={20} />} label="Stats" />
              </nav>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 py-6">
          <Routes>
            <Route path="/" element={<Collection />} />
            <Route path="/search" element={<CardSearch />} />
            <Route path="/scan" element={<Scanner />} />
            <Route path="/import" element={<Import />} />
            <Route path="/stats" element={<Stats />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

function NavItem({ to, icon, label }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
          isActive
            ? 'bg-mtg-gold text-gray-900 font-medium'
            : 'text-gray-300 hover:bg-gray-700'
        }`
      }
    >
      {icon}
      <span className="hidden sm:inline">{label}</span>
    </NavLink>
  );
}

export default App;
