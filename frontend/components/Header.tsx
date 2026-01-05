"use client";

import { Layers, Github, Info } from "lucide-react";

interface HeaderProps {
  totalImages?: number;
  isConnected?: boolean;
}

export function Header({ totalImages = 0, isConnected = false }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-xl">
      <div className="container mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent to-accent-secondary flex items-center justify-center">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-display text-xl font-bold tracking-tight text-text-primary">
              WearSearch
            </h1>
            <p className="text-xs text-text-muted -mt-0.5">
              Interactive Image Retrieval
            </p>
          </div>
        </div>

        {/* Status & Links */}
        <div className="flex items-center gap-4">
          {/* Connection status */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface">
            <div 
              className={`w-2 h-2 rounded-full ${
                isConnected ? "bg-positive animate-pulse" : "bg-negative"
              }`} 
            />
            <span className="text-sm text-text-secondary">
              {isConnected ? `${totalImages.toLocaleString()} images` : "Disconnected"}
            </span>
          </div>

          {/* Links */}
          <a
            href="https://github.com/LeDaiKing/Wear-Search"
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 rounded-lg hover:bg-surface transition-colors text-text-muted hover:text-text-primary"
            title="View on GitHub"
          >
            <Github className="w-5 h-5" />
          </a>
          <button
            className="p-2 rounded-lg hover:bg-surface transition-colors text-text-muted hover:text-text-primary"
            title="About"
          >
            <a href="https://www.facebook.com/DaiKingLE10/">
              <Info className="w-5 h-5" />
            </a>

          </button>
        </div>
      </div>
    </header>
  );
}

