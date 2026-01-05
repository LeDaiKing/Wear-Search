"use client";

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/Header";
import { SearchBar } from "@/components/SearchBar";
import { ImageGrid } from "@/components/ImageGrid";
import { FeedbackPanel } from "@/components/FeedbackPanel";
import { VectorVisualization } from "@/components/VectorVisualization";
import { IterationTimeline } from "@/components/IterationTimeline";
import { api, type ImageResult, type QueryVector, type FeedbackItem } from "@/lib/api";
import { AlertCircle, Sparkles, TrendingUp } from "lucide-react";

interface FeedbackState {
  [imageId: string]: "positive" | "negative" | null;
}

interface IterationData {
  number: number;
  type: string;
  resultsCount: number;
  results: ImageResult[];
}

export default function Home() {
  // Connection state
  const [isConnected, setIsConnected] = useState(false);
  const [totalImages, setTotalImages] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Search state
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [results, setResults] = useState<ImageResult[]>([]);
  const [queryVectors, setQueryVectors] = useState<QueryVector[]>([]);
  const [currentIteration, setCurrentIteration] = useState(0);
  const [iterations, setIterations] = useState<IterationData[]>([]);
  const [topK, setTopK] = useState(20);

  // Feedback state
  const [feedback, setFeedback] = useState<FeedbackState>({});
  const [textFeedbacks, setTextFeedbacks] = useState<string[]>([]);

  // Check backend connection
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const health = await api.healthCheck();
        setIsConnected(health.status === "healthy");
        setTotalImages(health.total_images);
        setError(null);
      } catch (err) {
        setIsConnected(false);
        setError("Could not connect to backend. Make sure it's running on port 8000.");
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle text search
  const handleTextSearch = useCallback(async (query: string) => {
    setIsLoading(true);
    setError(null);
    setFeedback({});
    setTextFeedbacks([]);

    try {
      const response = await api.searchByText(query, topK, sessionId || undefined);
      
      setSessionId(response.session_id);
      setResults(response.results);
      setQueryVectors(response.query_vectors);
      setCurrentIteration(response.iteration);
      setTotalImages(response.total_images);
      
      setIterations(prev => [
        ...prev.filter(i => i.number < response.iteration),
        {
          number: response.iteration,
          type: "text",
          resultsCount: response.results.length,
          results: response.results,
        }
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, topK]);

  // Handle image search
  const handleImageSearch = useCallback(async (file: File) => {
    setIsLoading(true);
    setError(null);
    setFeedback({});
    setTextFeedbacks([]);

    try {
      const response = await api.searchByImage(file, topK, sessionId || undefined);
      
      setSessionId(response.session_id);
      setResults(response.results);
      setQueryVectors(response.query_vectors);
      setCurrentIteration(response.iteration);
      setTotalImages(response.total_images);
      
      setIterations(prev => [
        ...prev.filter(i => i.number < response.iteration),
        {
          number: response.iteration,
          type: "image",
          resultsCount: response.results.length,
          results: response.results,
        }
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, topK]);

  // Handle feedback change
  const handleFeedbackChange = useCallback((imageId: string, type: "positive" | "negative" | null) => {
    setFeedback(prev => ({
      ...prev,
      [imageId]: type,
    }));
  }, []);

  // Submit relevance feedback
  const handleSubmitFeedback = useCallback(async () => {
    if (!sessionId) return;

    const feedbackItems: FeedbackItem[] = Object.entries(feedback)
      .filter(([_, type]) => type !== null)
      .map(([imageId, type]) => ({
        image_id: imageId,
        feedback: type as "positive" | "negative",
      }));

    // Allow text-only feedback if no thumb feedback is given
    if (feedbackItems.length === 0 && textFeedbacks.length === 0) return;

    setIsLoading(true);
    setError(null);

    // Combine all text feedbacks into one
    const combinedTextFeedback = textFeedbacks.length > 0 
      ? textFeedbacks.join(". ")
      : undefined;

    try {
      const response = await api.submitFeedback(
        sessionId,
        feedbackItems,
        combinedTextFeedback,
        topK
      );

      setResults(response.results);
      setQueryVectors(response.query_vectors);
      setCurrentIteration(response.iteration);
      setFeedback({});
      
      setIterations(prev => [
        ...prev,
        {
          number: response.iteration,
          type: "feedback",
          resultsCount: response.results.length,
          results: response.results,
        }
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Feedback submission failed");
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, feedback, textFeedbacks, topK]);

  // Submit pseudo feedback
  const handlePseudoFeedback = useCallback(async (topM: number) => {
    if (!sessionId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await api.submitPseudoFeedback(sessionId, topM, topK);

      setResults(response.results);
      setQueryVectors(response.query_vectors);
      setCurrentIteration(response.iteration);
      setFeedback({});
      
      setIterations(prev => [
        ...prev,
        {
          number: response.iteration,
          type: "pseudo_feedback",
          resultsCount: response.results.length,
          results: response.results,
        }
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Auto-expansion failed");
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, topK]);
  
  // Clear feedback and return to original results
  const handleClearFeedback = useCallback(() => {
    if (iterations.length > 0) {
      const firstIteration = iterations[0];
      setResults(firstIteration.results);
      setCurrentIteration(firstIteration.number);
      setFeedback({});
      setTextFeedbacks([]);
      setQueryVectors(queryVectors.slice(0, 1));
      setIterations([firstIteration]);
    }
  }, [iterations, queryVectors]);

  // Count feedback
  const positiveFeedbackCount = Object.values(feedback).filter(v => v === "positive").length;
  const negativeFeedbackCount = Object.values(feedback).filter(v => v === "negative").length;

  // Refresh results with new topK
  const handleRefreshWithTopK = useCallback(async () => {
    if (!sessionId || iterations.length === 0) return;
    
    // Get the last query from the first iteration
    const firstIteration = iterations[0];
    if (firstIteration.type === "text" || firstIteration.type === "image") {
      // Re-search with new topK - we need to re-trigger the search
      // For now, use pseudo feedback with top_m=0 just to re-fetch
      setIsLoading(true);
      setError(null);
      
      try {
        // Use the current query vector to re-search
        const response = await api.submitPseudoFeedback(sessionId, 1, topK);
        setResults(response.results);
        // Don't increment iteration for just changing topK
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to refresh results");
      } finally {
        setIsLoading(false);
      }
    }
  }, [sessionId, iterations, topK]);

  // Reset session
  const handleNewSearch = () => {
    setSessionId(null);
    setResults([]);
    setQueryVectors([]);
    setCurrentIteration(0);
    setIterations([]);
    setFeedback({});
    setTextFeedbacks([]);
    setError(null);
  };

  return (
    <div className="min-h-screen gradient-bg">
      <Header totalImages={totalImages} isConnected={isConnected} />

      <main className="container mx-auto px-6 py-8">
        {/* Hero Section */}
        {results.length === 0 && (
          <div className="text-center mb-12 pt-8">
            <h2 className="font-display text-4xl md:text-5xl font-bold tracking-tight text-text-primary mb-4 glow-text">
              Find Fashion with AI
            </h2>
            <p className="text-lg text-text-secondary max-w-xl mx-auto mb-8">
              Search by text or image, then refine results with feedback.
              Watch the query evolve in real-time.
            </p>
            
            <SearchBar
              onTextSearch={handleTextSearch}
              onImageSearch={handleImageSearch}
              isLoading={isLoading}
            />
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-negative/10 border border-negative/20 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-negative flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-negative">Error</p>
              <p className="text-sm text-text-secondary">{error}</p>
            </div>
          </div>
        )}

        {/* Results View */}
        {results.length > 0 && (
          <div className="space-y-6">
            {/* Compact Search Bar */}
            <div className="flex items-center justify-between gap-4">
              <button
                onClick={handleNewSearch}
                className="btn-secondary text-sm py-2 px-4"
              >
                New Search
              </button>
              
              <div className="flex-1 max-w-2xl">
                <SearchBar
                  onTextSearch={handleTextSearch}
                  onImageSearch={handleImageSearch}
                  isLoading={isLoading}
                />
              </div>

              <div className="w-24" /> {/* Spacer for balance */}
            </div>

            {/* Iteration Timeline */}
            {iterations.length > 1 && (
              <IterationTimeline
                iterations={iterations}
                currentIteration={currentIteration}
              />
            )}

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Results Grid - Takes 3 columns */}
              <div className="lg:col-span-3 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                      <Sparkles className="w-4 h-4 text-accent" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-text-primary">
                        Results
                      </h3>
                      <p className="text-sm text-text-muted">
                        {results.length} images • Iteration {currentIteration}
                      </p>
                    </div>
                  </div>
                  
                  <p className="text-sm text-text-secondary">
                    Click thumbs to mark relevant / not relevant
                  </p>
                </div>

                <ImageGrid
                  results={results}
                  feedback={feedback}
                  onFeedbackChange={handleFeedbackChange}
                />
              </div>

              {/* Sidebar - Takes 1 column */}
              <div className="space-y-6">
                {/* Feedback Panel */}
                <FeedbackPanel
                  positiveFeedbackCount={positiveFeedbackCount}
                  negativeFeedbackCount={negativeFeedbackCount}
                  onSubmitFeedback={handleSubmitFeedback}
                  onPseudoFeedback={handlePseudoFeedback}
                  onClearFeedback={handleClearFeedback}
                  onRefreshWithTopK={handleRefreshWithTopK}
                  isLoading={isLoading}
                  iteration={currentIteration}
                  textFeedbacks={textFeedbacks}
                  onTextFeedbacksChange={setTextFeedbacks}
                  topK={topK}
                  onTopKChange={setTopK}
                  currentResultsCount={results.length}
                />

                {/* Vector Visualization */}
                <VectorVisualization
                  queryVectors={queryVectors}
                  width={320}
                  height={240}
                />

                {/* Stats Card */}
                <div className="glass-card p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <TrendingUp className="w-4 h-4 text-accent" />
                    <h4 className="font-medium text-text-primary">Session Stats</h4>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-center">
                    <div className="p-3 rounded-lg bg-surface">
                      <p className="text-2xl font-bold text-accent">{currentIteration}</p>
                      <p className="text-xs text-text-muted">Iterations</p>
                    </div>
                    <div className="p-3 rounded-lg bg-surface">
                      <p className="text-2xl font-bold text-positive">
                        {iterations.reduce((acc, i) => acc + (i.type === "feedback" ? 1 : 0), 0)}
                      </p>
                      <p className="text-xs text-text-muted">Refinements</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Empty State for No Results */}
        {!isLoading && results.length === 0 && totalImages === 0 && isConnected && (
          <div className="text-center mt-16 p-8 glass-card max-w-lg mx-auto">
            <div className="w-16 h-16 rounded-2xl bg-surface-elevated flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-8 h-8 text-text-muted" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">
              No Images Indexed
            </h3>
            <p className="text-text-secondary text-sm mb-4">
              The image corpus is empty. Add images to the index to start searching.
            </p>
            <p className="text-text-muted text-xs font-mono">
              POST /index/add or POST /index/bulk
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-6 mt-12">
        <div className="container mx-auto px-6 text-center">
          <p className="text-sm text-text-muted">
            WearSearch • Interactive Image Retrieval System with Rocchio Feedback
          </p>
        </div>
      </footer>
    </div>
  );
}
