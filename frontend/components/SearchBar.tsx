"use client";

import { useState, useRef, useCallback } from "react";
import { Search, Image as ImageIcon, Upload, X, Sparkles } from "lucide-react";

type SearchMode = "text" | "image";

interface SearchBarProps {
  onTextSearch: (query: string) => void;
  onImageSearch: (file: File) => void;
  isLoading?: boolean;
}

export function SearchBar({ onTextSearch, onImageSearch, isLoading }: SearchBarProps) {
  const [mode, setMode] = useState<SearchMode>("text");
  const [textQuery, setTextQuery] = useState("");
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (textQuery.trim() && !isLoading) {
      onTextSearch(textQuery.trim());
    }
  };

  const handleFileSelect = useCallback((file: File) => {
    if (file.type.startsWith("image/")) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const handleImageSubmit = () => {
    if (selectedImage && !isLoading) {
      onImageSearch(selectedImage);
    }
  };

  const clearImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* Mode Toggle */}
      <div className="flex justify-center mb-6">
        <div className="mode-toggle">
          <button
            onClick={() => setMode("text")}
            className={mode === "text" ? "active" : ""}
          >
            <Search className="w-4 h-4 inline mr-2" />
            Text Search
          </button>
          <button
            onClick={() => setMode("image")}
            className={mode === "image" ? "active" : ""}
          >
            <ImageIcon className="w-4 h-4 inline mr-2" />
            Image Search
          </button>
        </div>
      </div>

      {/* Text Search */}
      {mode === "text" && (
        <form onSubmit={handleTextSubmit} className="relative">
          <div className="relative group">
            <div className="absolute inset-0 bg-gradient-to-r from-accent/20 to-accent-secondary/20 rounded-2xl blur-xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-300" />
            <div className="relative flex items-center gap-3 glass-card p-2">
              <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-surface-elevated flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-accent" />
              </div>
              <input
                type="text"
                value={textQuery}
                onChange={(e) => setTextQuery(e.target.value)}
                placeholder="Describe what you're looking for..."
                className="flex-1 bg-transparent border-none outline-none text-lg text-text-primary placeholder:text-text-muted py-3"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={!textQuery.trim() || isLoading}
                className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <Search className="w-5 h-5" />
                )}
                Search
              </button>
            </div>
          </div>
          
          {/* Example queries */}
          <div className="flex flex-wrap gap-2 mt-4 justify-center">
            <span className="text-text-muted text-sm">Try:</span>
            {["red summer dress", "casual denim jacket", "floral print blouse"].map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => setTextQuery(example)}
                className="px-3 py-1 text-sm rounded-full bg-surface hover:bg-surface-elevated border border-border hover:border-border-hover text-text-secondary hover:text-text-primary transition-all"
              >
                {example}
              </button>
            ))}
          </div>
        </form>
      )}

      {/* Image Search */}
      {mode === "image" && (
        <div className="space-y-4">
          {!imagePreview ? (
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
              className={`upload-zone ${isDragOver ? "dragover" : ""}`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleFileSelect(file);
                }}
                className="hidden"
              />
              <Upload className="w-12 h-12 mx-auto mb-4 text-text-muted" />
              <p className="text-lg font-medium text-text-primary mb-2">
                Drop an image here or click to upload
              </p>
              <p className="text-text-muted text-sm">
                Supports JPG, PNG, WebP • Max 10MB
              </p>
            </div>
          ) : (
            <div className="glass-card p-4">
              <div className="flex items-start gap-4">
                <div className="relative">
                  <img
                    src={imagePreview}
                    alt="Selected"
                    className="w-32 h-32 object-cover rounded-xl"
                  />
                  <button
                    onClick={clearImage}
                    className="absolute -top-2 -right-2 w-6 h-6 bg-negative rounded-full flex items-center justify-center hover:scale-110 transition-transform"
                  >
                    <X className="w-4 h-4 text-white" />
                  </button>
                </div>
                <div className="flex-1">
                  <p className="font-medium text-text-primary mb-1">
                    {selectedImage?.name}
                  </p>
                  <p className="text-sm text-text-muted mb-4">
                    {((selectedImage?.size || 0) / 1024).toFixed(1)} KB
                  </p>
                  <button
                    onClick={handleImageSubmit}
                    disabled={isLoading}
                    className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {isLoading ? (
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <Search className="w-5 h-5" />
                    )}
                    Find Similar
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

