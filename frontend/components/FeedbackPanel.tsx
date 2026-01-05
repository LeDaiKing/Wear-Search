"use client";

import { useState } from "react";
import { 
  RefreshCw, 
  Sparkles, 
  MessageSquare, 
  ChevronDown, 
  ChevronUp,
  ThumbsUp,
  ThumbsDown,
  Zap,
  X,
  Plus,
  RotateCcw
} from "lucide-react";

interface FeedbackPanelProps {
  positiveFeedbackCount: number;
  negativeFeedbackCount: number;
  onSubmitFeedback: () => void;
  onPseudoFeedback: (topM: number) => void;
  onClearFeedback: () => void;
  onRefreshWithTopK: () => void;
  isLoading?: boolean;
  iteration: number;
  textFeedbacks: string[];
  onTextFeedbacksChange: (feedbacks: string[]) => void;
  topK: number;
  onTopKChange: (topK: number) => void;
  currentResultsCount: number;
}

export function FeedbackPanel({
  positiveFeedbackCount,
  negativeFeedbackCount,
  onSubmitFeedback,
  onPseudoFeedback,
  onClearFeedback,
  onRefreshWithTopK,
  isLoading,
  iteration,
  textFeedbacks,
  onTextFeedbacksChange,
  topK,
  onTopKChange,
  currentResultsCount,
}: FeedbackPanelProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [pseudoTopM, setPseudoTopM] = useState(5);
  const [currentTextInput, setCurrentTextInput] = useState("");

  const hasFeedback = positiveFeedbackCount > 0 || negativeFeedbackCount > 0 || textFeedbacks.length > 0;
  const totalFeedback = positiveFeedbackCount + negativeFeedbackCount + textFeedbacks.length;

  const handleSubmit = () => {
    onSubmitFeedback();
    setCurrentTextInput("");
  };

  const handleAddTextFeedback = () => {
    if (currentTextInput.trim()) {
      onTextFeedbacksChange([...textFeedbacks, currentTextInput.trim()]);
      setCurrentTextInput("");
    }
  };

  const handleRemoveTextFeedback = (index: number) => {
    onTextFeedbacksChange(textFeedbacks.filter((_, i) => i !== index));
  };

  return (
    <div className="glass-card p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center">
            <RefreshCw className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h3 className="font-semibold text-text-primary">Refine Results</h3>
            <p className="text-sm text-text-muted">Iteration {iteration}</p>
          </div>
        </div>
        
        {/* Feedback counts */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 px-3 py-1.5 rounded-full bg-positive/10 text-positive">
            <ThumbsUp className="w-4 h-4" />
            <span className="font-medium">{positiveFeedbackCount}</span>
          </div>
          <div className="flex items-center gap-1 px-3 py-1.5 rounded-full bg-negative/10 text-negative">
            <ThumbsDown className="w-4 h-4" />
            <span className="font-medium">{negativeFeedbackCount}</span>
          </div>
        </div>
      </div>

      {/* Top K Selector */}
      <div className="p-3 rounded-xl bg-surface space-y-3">
        <div>
          <label className="flex items-center justify-between text-sm font-medium text-text-primary mb-2">
            <span>Results to show</span>
            <span className="font-mono text-accent">{topK}</span>
          </label>
          <input
            type="range"
            min={10}
            max={500}
            step={10}
            value={topK}
            onChange={(e) => onTopKChange(parseInt(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-text-muted mt-1">
            <span>10</span>
            <span>500</span>
          </div>
        </div>
        
        {/* Refresh button when topK differs from current results */}
        {topK !== currentResultsCount && (
          <button
            onClick={onRefreshWithTopK}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-accent/20 text-accent text-sm font-medium hover:bg-accent/30 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            Fetch {topK} Results
          </button>
        )}
      </div>

      {/* Main feedback button */}
      <button
        onClick={handleSubmit}
        disabled={!hasFeedback || isLoading}
        className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed py-2.5"
      >
        {isLoading ? (
          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
        ) : (
          <Sparkles className="w-4 h-4" />
        )}
        <span className="text-sm font-medium">Apply Feedback ({totalFeedback})</span>
      </button>

      {/* Clear feedback button */}
      {iteration > 1 && (
        <button
          onClick={onClearFeedback}
          disabled={isLoading}
          className="btn-secondary w-full flex items-center justify-center gap-2"
        >
          <RotateCcw className="w-4 h-4" />
          <span className="text-sm font-medium">Clear Feedback</span>
        </button>
      )}

      {/* Advanced options toggle */}
      <button
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary transition-colors w-full justify-center"
      >
        {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        Advanced Options
      </button>

      {/* Advanced options */}
      {showAdvanced && (
        <div className="space-y-4 pt-2 border-t border-border">
          {/* Text feedback list */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-text-primary mb-2">
              <MessageSquare className="w-4 h-4 text-accent" />
              Natural Language Feedback
            </label>
            
            {/* Existing feedbacks */}
            {textFeedbacks.length > 0 && (
              <div className="space-y-2 mb-3">
                {textFeedbacks.map((feedback, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-2 p-2 rounded-lg bg-surface-elevated"
                  >
                    <span className="flex-1 text-sm text-text-primary">{feedback}</span>
                    <button
                      onClick={() => handleRemoveTextFeedback(index)}
                      className="p-1 rounded hover:bg-negative/10 text-negative transition-colors"
                      title="Remove"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* New feedback input */}
            <form 
              onSubmit={(e) => {
                e.preventDefault();
                handleAddTextFeedback();
              }}
              className="flex gap-1"
            >
              <input
                type="text"
                value={currentTextInput}
                onChange={(e) => setCurrentTextInput(e.target.value)}
                placeholder="e.g., 'Similar style but in blue'"
                className="input-field grow text-sm"
              />
              <button
                type="submit"
                disabled={!currentTextInput.trim()}
                className="btn-secondary px-3 py-2 disabled:opacity-50"
                title="Add feedback"
              >
                <Plus className="w-4 h-4" />
              </button>
            </form>
            <p className="text-xs text-text-muted mt-1">
              Add multiple feedback statements to refine your search
            </p>
          </div>

          {/* Pseudo feedback */}
          <div className="p-4 rounded-xl bg-surface">
            <label className="flex items-center gap-2 text-sm font-medium text-text-primary mb-3">
              <Zap className="w-4 h-4 text-yellow-400" />
              Automatic Query Expansion
            </label>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min={1}
                  max={20}
                  value={pseudoTopM}
                  onChange={(e) => setPseudoTopM(parseInt(e.target.value))}
                  className="flex-1"
                />
                <span className="text-sm font-mono text-text-secondary w-8">
                  {pseudoTopM}
                </span>
              </div>
              <button
                onClick={() => onPseudoFeedback(pseudoTopM)}
                disabled={isLoading}
                className="btn-secondary text-sm py-2 px-4 w-full"
              >
                Auto-Expand
              </button>
              <p className="text-xs text-text-muted">
                Assumes top {pseudoTopM} results are relevant for query expansion
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
