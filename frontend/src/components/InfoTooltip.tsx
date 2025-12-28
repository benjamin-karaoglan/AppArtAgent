"use client";

import { Info } from 'lucide-react';
import { useState } from 'react';

interface InfoTooltipProps {
  title: string;
  content: string | React.ReactNode;
}

export default function InfoTooltip({ title, content }: InfoTooltipProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative inline-block">
      <button
        type="button"
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center justify-center w-5 h-5 text-blue-600 hover:text-blue-800 focus:outline-none"
        aria-label={title}
      >
        <Info className="h-4 w-4" />
      </button>

      {isOpen && (
        <div className="absolute z-50 w-80 p-4 mt-2 text-sm bg-white border border-gray-200 rounded-lg shadow-lg -left-36 top-full">
          <div className="font-semibold text-gray-900 mb-2">{title}</div>
          <div className="text-gray-700 space-y-2">
            {typeof content === 'string' ? <p>{content}</p> : content}
          </div>
          {/* Arrow pointer */}
          <div className="absolute w-3 h-3 bg-white border-l border-t border-gray-200 transform rotate-45 -top-1.5 left-1/2 -translate-x-1/2"></div>
        </div>
      )}
    </div>
  );
}
