import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { Library, Search, Camera, BarChart3 } from 'lucide-react';
import Collection from './pages/Collection';
import CardSearch from './pages/CardSearch';
import Scanner from './pages/Scanner';
import Stats from './pages/Stats';

function App() {
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
