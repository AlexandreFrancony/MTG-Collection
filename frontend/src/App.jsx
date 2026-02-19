import { useState } from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { Library, Search, Camera, FileText, BarChart3, Sun, Moon } from 'lucide-react';
import Collection from './pages/Collection';
import CardSearch from './pages/CardSearch';
import Scanner from './pages/Scanner';
import Import from './pages/Import';
import Stats from './pages/Stats';

function ThemeToggle() {
  const [isDark, setIsDark] = useState(document.documentElement.classList.contains('dark'));

  const toggleTheme = () => {
    const html = document.documentElement;
    const newIsDark = !html.classList.contains('dark');
    html.classList.toggle('dark', newIsDark);
    localStorage.setItem('theme', newIsDark ? 'dark' : 'light');
    setIsDark(newIsDark);
  };

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-lg transition-colors bg-[var(--bg-input)] hover:bg-[var(--border)] text-[var(--text-secondary)]"
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDark ? <Sun size={20} /> : <Moon size={20} />}
    </button>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[var(--bg-primary)]">
        {/* Header */}
        <header className="bg-[var(--bg-header)] border-b border-[var(--border)] sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 py-3">
            <div className="flex items-center justify-between">
              <h1 className="text-xl font-bold text-mtg-gold flex items-center gap-2">
                MTG Collection
              </h1>
              <div className="flex items-center gap-2">
                <nav className="flex gap-1">
                  <NavItem to="/" icon={<Library size={20} />} label="Collection" />
                  <NavItem to="/search" icon={<Search size={20} />} label="Search" />
                  <NavItem to="/scan" icon={<Camera size={20} />} label="Scan" />
                  <NavItem to="/import" icon={<FileText size={20} />} label="Import" />
                  <NavItem to="/stats" icon={<BarChart3 size={20} />} label="Stats" />
                </nav>
                <ThemeToggle />
              </div>
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
            ? 'bg-mtg-gold text-[var(--bg-primary)] font-medium'
            : 'text-[var(--text-secondary)] hover:bg-[var(--bg-input)]'
        }`
      }
    >
      {icon}
      <span className="hidden sm:inline">{label}</span>
    </NavLink>
  );
}

export default App;
