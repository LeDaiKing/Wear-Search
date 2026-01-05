/**
 * API client for WearSearch backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ImageResult {
  image_id: string;
  filename: string;
  url: string;
  similarity_score: number;
  metadata?: {
    display_name?: string;
    description?: string;
    category?: string;
    [key: string]: unknown;
  };
}

export interface QueryVector {
  x: number;
  y: number;
  iteration: number;
}

export interface SearchResponse {
  session_id: string;
  iteration: number;
  results: ImageResult[];
  query_vectors: QueryVector[];
  total_images: number;
}

export interface FeedbackItem {
  image_id: string;
  feedback: "positive" | "negative";
}

export interface VisualizationData {
  query_vectors: QueryVector[];
  corpus_vectors: { x: number; y: number }[];
  iterations: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  index_loaded: boolean;
  total_images: number;
}

class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  private async fetch<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async healthCheck(): Promise<HealthResponse> {
    return this.fetch<HealthResponse>("/health");
  }

  async searchByText(
    query: string,
    topK: number = 20,
    sessionId?: string
  ): Promise<SearchResponse> {
    return this.fetch<SearchResponse>("/search/text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        top_k: topK,
        session_id: sessionId,
      }),
    });
  }

  async searchByImage(
    image: File,
    topK: number = 20,
    sessionId?: string
  ): Promise<SearchResponse> {
    const formData = new FormData();
    formData.append("image", image);
    formData.append("top_k", topK.toString());
    if (sessionId) {
      formData.append("session_id", sessionId);
    }

    return this.fetch<SearchResponse>("/search/image", {
      method: "POST",
      body: formData,
    });
  }

  async submitFeedback(
    sessionId: string,
    feedbackItems: FeedbackItem[],
    textFeedback?: string,
    topK: number = 20
  ): Promise<SearchResponse> {
    return this.fetch<SearchResponse>("/feedback/relevance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        feedback_items: feedbackItems,
        text_feedback: textFeedback,
        top_k: topK,
      }),
    });
  }

  async submitPseudoFeedback(
    sessionId: string,
    topM: number = 5,
    topK: number = 20
  ): Promise<SearchResponse> {
    return this.fetch<SearchResponse>("/feedback/pseudo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        top_m: topM,
        top_k: topK,
      }),
    });
  }

  async getVisualizationData(
    sessionId: string,
    includeCorpus: boolean = false,
    sampleSize: number = 100
  ): Promise<VisualizationData> {
    const params = new URLSearchParams({
      session_id: sessionId,
      include_corpus: includeCorpus.toString(),
      sample_size: sampleSize.toString(),
    });

    return this.fetch<VisualizationData>(`/visualization/vectors?${params}`);
  }

  async addImageToIndex(
    image: File,
    imageId?: string,
    metadata?: Record<string, unknown>
  ): Promise<{ status: string; image_id: string; total_images: number }> {
    const formData = new FormData();
    formData.append("image", image);
    if (imageId) {
      formData.append("image_id", imageId);
    }
    if (metadata) {
      formData.append("metadata", JSON.stringify(metadata));
    }

    return this.fetch("/index/add", {
      method: "POST",
      body: formData,
    });
  }

  getImageUrl(filename: string): string {
    return `${this.baseUrl}/images/${filename}`;
  }
}

export const api = new APIClient();

