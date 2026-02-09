// API utilities for MTG Collection Tracker

const API_BASE = import.meta.env.VITE_API_URL || '/api';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  // Don't set Content-Type for FormData
  if (options.body instanceof FormData) {
    delete config.headers['Content-Type'];
  }

  const response = await fetch(url, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Request failed' }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }

  return response.json();
}

// Health check
export const getHealth = () => request('/health');

// Card search (Scryfall)
export const searchCards = (query) =>
  request(`/cards/search?q=${encodeURIComponent(query)}`);

export const getCardByName = (name) =>
  request(`/cards/named?name=${encodeURIComponent(name)}`);

// Collection management
export const getCollection = (params = {}) => {
  const query = new URLSearchParams(params).toString();
  return request(`/collection${query ? `?${query}` : ''}`);
};

export const getCollectionStats = () => request('/collection/stats');

export const addCardToCollection = (card) =>
  request('/collection', {
    method: 'POST',
    body: JSON.stringify(card),
  });

export const removeCardFromCollection = (cardId) =>
  request(`/collection/${cardId}`, {
    method: 'DELETE',
  });

export const updateCardInCollection = (cardId, data) =>
  request(`/collection/${cardId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });

// Scanning
export const scanSingleCard = (file) => {
  const formData = new FormData();
  formData.append('image', file);

  return request('/scan/single', {
    method: 'POST',
    body: formData,
  });
};

export const scanBinderPage = (file) => {
  const formData = new FormData();
  formData.append('image', file);

  return request('/scan/binder', {
    method: 'POST',
    body: formData,
  });
};

// Import decklist
export const importDecklist = (decklist) =>
  request('/collection/import', {
    method: 'POST',
    body: JSON.stringify({ decklist }),
  });
