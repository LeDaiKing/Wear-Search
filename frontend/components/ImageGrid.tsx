"use client";

import { useState, useEffect } from "react";
import { ThumbsUp, ThumbsDown, X, Tag, FileText, Sparkles, ZoomIn } from "lucide-react";
import type { ImageResult } from "@/lib/api";

interface FeedbackState {
  [imageId: string]: "positive" | "negative" | null;
}

interface ImageGridProps {
  results: ImageResult[];
  feedback: FeedbackState;
  onFeedbackChange: (imageId: string, type: "positive" | "negative" | null) => void;
  apiBaseUrl?: string;
}

interface ImageModalProps {
  result: ImageResult;
  apiBaseUrl: string;
  onClose: () => void;
  feedback: "positive" | "negative" | null;
  onFeedbackChange: (type: "positive" | "negative" | null) => void;
}

function ImageModal({ result, apiBaseUrl, onClose, feedback, onFeedbackChange }: ImageModalProps) {
  const displayName = result.metadata?.display_name || result.filename;
  const description = result.metadata?.description || "No description available";
  const category = result.metadata?.category || "Unknown";
  const isPositive = feedback === "positive";
  const isNegative = feedback === "negative";

  // Handle keyboard events
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const handleFeedback = (type: "positive" | "negative") => {
    if (feedback === type) {
      onFeedbackChange(null);
    } else {
      onFeedbackChange(type);
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in"
      onClick={onClose}
    >
      <div 
        className="relative w-full max-w-5xl max-h-[90vh] overflow-hidden rounded-2xl bg-gradient-to-br from-surface via-background to-surface border border-white/10 shadow-2xl animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-20 p-2 rounded-full bg-black/50 backdrop-blur-sm text-white/80 hover:text-white hover:bg-black/70 transition-all"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex flex-col md:flex-row h-full max-h-[90vh]">
          {/* Image Section */}
          <div className="relative md:w-1/2 flex-shrink-0 bg-black/30">
            <img
              src={`${apiBaseUrl}${result.url}`}
              alt={displayName}
              className="w-full h-full object-contain max-h-[50vh] md:max-h-[90vh]"
            />
            
            {/* Similarity Score */}
            <div className="absolute top-4 left-4 px-3 py-1.5 rounded-full bg-accent/90 backdrop-blur-sm text-white text-sm font-semibold flex items-center gap-1.5">
              <Sparkles className="w-4 h-4" />
              {(result.similarity_score * 100).toFixed(1)}% match
            </div>
          </div>

          {/* Details Section */}
          <div className="md:w-1/2 p-6 md:p-8 overflow-y-auto">
            {/* Category Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent/20 text-accent text-sm font-medium mb-4">
              <Tag className="w-4 h-4" />
              {category}
            </div>

            {/* Product Name */}
            <h2 className="text-2xl md:text-3xl font-bold text-text-primary mb-4 leading-tight">
              {displayName}
            </h2>

            {/* Description */}
            <div className="mb-6">
              <div className="flex items-center gap-2 text-text-muted text-sm mb-2">
                <FileText className="w-4 h-4" />
                Description
              </div>
              <p className="text-text-secondary leading-relaxed text-sm md:text-base">
                {description}
              </p>
            </div>

            {/* Divider */}
            <div className="h-px bg-gradient-to-r from-transparent via-white/20 to-transparent my-6" />

            {/* Feedback Section */}
            <div className="space-y-3">
              <p className="text-text-muted text-sm">Is this relevant to your search?</p>
              <div className="flex gap-3">
                <button
                  onClick={() => handleFeedback("positive")}
                  className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl font-medium transition-all ${
                    isPositive
                      ? "bg-positive text-white shadow-lg shadow-positive/30"
                      : "bg-white/5 text-text-secondary hover:bg-positive/20 hover:text-positive"
                  }`}
                >
                  <ThumbsUp className="w-5 h-5" />
                  Relevant
                </button>
                <button
                  onClick={() => handleFeedback("negative")}
                  className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl font-medium transition-all ${
                    isNegative
                      ? "bg-negative text-white shadow-lg shadow-negative/30"
                      : "bg-white/5 text-text-secondary hover:bg-negative/20 hover:text-negative"
                  }`}
                >
                  <ThumbsDown className="w-5 h-5" />
                  Not Relevant
                </button>
              </div>
            </div>

            {/* Metadata */}
            <div className="mt-6 pt-4 border-t border-white/10">
              <p className="text-text-muted text-xs">
                ID: {result.image_id} • File: {result.filename}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function ImageGrid({ 
  results, 
  feedback, 
  onFeedbackChange,
  apiBaseUrl = "http://localhost:8000" 
}: ImageGridProps) {
  const [selectedImage, setSelectedImage] = useState<ImageResult | null>(null);

  const handleFeedback = (imageId: string, type: "positive" | "negative") => {
    const currentFeedback = feedback[imageId];
    if (currentFeedback === type) {
      onFeedbackChange(imageId, null);
    } else {
      onFeedbackChange(imageId, type);
    }
  };

  if (results.length === 0) {
    return null;
  }

  return (
    <>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {results.map((result, index) => {
          const feedbackState = feedback[result.image_id];
          const isPositive = feedbackState === "positive";
          const isNegative = feedbackState === "negative";
          const displayName = result.metadata?.display_name || result.filename;
          const category = result.metadata?.category;

          return (
            <div
              key={result.image_id}
              className={`
                image-card aspect-[3/4] opacity-0 animate-fade-in-up group
                ${isPositive ? "selected-positive" : ""}
                ${isNegative ? "selected-negative" : ""}
              `}
              style={{ animationDelay: `${Math.min(index * 0.05, 0.4)}s` }}
            >
              {/* Image */}
              <img
                src={`${apiBaseUrl}${result.url}`}
                alt={displayName}
                className="w-full h-full object-cover"
                loading="lazy"
              />

              {/* Similarity Score Badge */}
              <div className="absolute top-2 right-2 px-2 py-1 rounded-md bg-black/60 backdrop-blur-sm text-xs font-mono text-white z-10">
                {(result.similarity_score * 100).toFixed(1)}%
              </div>

              {/* Feedback Indicator */}
              {feedbackState && (
                <div 
                  className={`absolute top-2 left-2 w-6 h-6 rounded-full flex items-center justify-center z-10 ${
                    isPositive ? "bg-positive" : "bg-negative"
                  }`}
                >
                  {isPositive ? (
                    <ThumbsUp className="w-3 h-3 text-white" />
                  ) : (
                    <ThumbsDown className="w-3 h-3 text-white" />
                  )}
                </div>
              )}

              {/* Product Info Overlay (Always visible at bottom) */}
              <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/90 via-black/60 to-transparent">
                {category && (
                  <span className="inline-block px-2 py-0.5 rounded-full bg-accent/80 text-[10px] font-medium text-white mb-1">
                    {category}
                  </span>
                )}
                <h3 className="text-sm font-medium text-white line-clamp-2 leading-tight">
                  {displayName}
                </h3>
              </div>

              {/* Hover Overlay */}
              <div className="image-overlay">
                <div className="flex gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleFeedback(result.image_id, "positive");
                    }}
                    className={`feedback-btn positive ${isPositive ? "active" : ""} bg-black/40 backdrop-blur-sm`}
                    title="Mark as relevant"
                  >
                    <ThumbsUp className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleFeedback(result.image_id, "negative");
                    }}
                    className={`feedback-btn negative ${isNegative ? "active" : ""} bg-black/40 backdrop-blur-sm`}
                    title="Mark as not relevant"
                  >
                    <ThumbsDown className="w-4 h-4" />
                  </button>
                </div>
                <button
                  onClick={() => setSelectedImage(result)}
                  className="p-2 rounded-lg bg-black/40 backdrop-blur-sm text-white hover:bg-white/20 transition-colors"
                  title="View details"
                >
                  <ZoomIn className="w-4 h-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Image Detail Modal */}
      {selectedImage && (
        <ImageModal
          result={selectedImage}
          apiBaseUrl={apiBaseUrl}
          onClose={() => setSelectedImage(null)}
          feedback={feedback[selectedImage.image_id]}
          onFeedbackChange={(type) => onFeedbackChange(selectedImage.image_id, type)}
        />
      )}
    </>
  );
}
