import { useState } from 'react';

const CARD_BACK_URL = 'https://cards.scryfall.io/art_crop/front/0/c/0c5ff4e3-3c81-4ada-b5b8-6b0e13c9c3a9.jpg';

export default function CardImage({ src, alt, className = '' }) {
  const [error, setError] = useState(false);

  if (error || !src) {
    return (
      <div className={`bg-gray-700 flex items-center justify-center ${className}`}>
        <div className="text-center p-4">
          <span className="text-4xl">🎴</span>
          <p className="text-xs text-gray-400 mt-2 truncate max-w-[100px]">{alt}</p>
        </div>
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      onError={() => setError(true)}
      className={className}
      loading="lazy"
    />
  );
}
