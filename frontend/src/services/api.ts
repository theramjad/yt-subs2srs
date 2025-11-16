import axios from 'axios';

const API_BASE_URL = '/api';

export interface JobStatus {
  jobId: string;
  status: 'downloading' | 'extracting' | 'transcribing' | 'segmenting' | 'generating' | 'creating_deck' | 'complete' | 'error';
  progress: number;
  currentStep: string;
  error?: string;
  videoTitle?: string;
  cardsCount?: number;
}

export interface CardPreview {
  sentence: string;
  image: string; // base64
  audio: string; // base64
}

export const api = {
  /**
   * Start processing a YouTube video
   */
  async startProcessing(youtubeUrl: string, assemblyAiApiKey: string): Promise<{ jobId: string; status: string }> {
    const response = await axios.post(`${API_BASE_URL}/process`, {
      youtubeUrl,
      assemblyAiApiKey,
    });
    return response.data;
  },

  /**
   * Poll job status
   */
  async getStatus(jobId: string): Promise<JobStatus> {
    const response = await axios.get(`${API_BASE_URL}/status/${jobId}`);
    return response.data;
  },

  /**
   * Get card preview
   */
  async getPreview(jobId: string, limit: number = 5): Promise<CardPreview[]> {
    const response = await axios.get(`${API_BASE_URL}/preview/${jobId}`, {
      params: { limit },
    });
    return response.data.cards;
  },

  /**
   * Download APKG file
   */
  getDownloadUrl(jobId: string): string {
    return `${API_BASE_URL}/download/${jobId}`;
  },

  /**
   * Health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      await axios.get(`${API_BASE_URL}/health`);
      return true;
    } catch {
      return false;
    }
  },
};
