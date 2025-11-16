import { useState, useEffect } from 'react';
import { api, JobStatus, CardPreview } from './services/api';
import './App.css';

function App() {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [preview, setPreview] = useState<CardPreview[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Load API key from localStorage
  useEffect(() => {
    const savedApiKey = localStorage.getItem('assemblyai_api_key');
    if (savedApiKey) {
      setApiKey(savedApiKey);
    }
  }, []);

  // Poll status when processing
  useEffect(() => {
    if (!jobId || !isProcessing) return;

    const pollInterval = setInterval(async () => {
      try {
        const jobStatus = await api.getStatus(jobId);
        setStatus(jobStatus);

        if (jobStatus.status === 'complete') {
          setIsProcessing(false);
          // Load preview
          const cards = await api.getPreview(jobId);
          setPreview(cards);
        } else if (jobStatus.status === 'error') {
          setIsProcessing(false);
          setError(jobStatus.error || 'Processing failed');
        }
      } catch (err: any) {
        console.error('Status polling error:', err);
        setError(err.message);
        setIsProcessing(false);
      }
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(pollInterval);
  }, [jobId, isProcessing]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setStatus(null);
    setPreview([]);

    if (!youtubeUrl || !apiKey) {
      setError('Please provide both YouTube URL and API key');
      return;
    }

    // Save API key to localStorage
    localStorage.setItem('assemblyai_api_key', apiKey);

    try {
      setIsProcessing(true);
      const result = await api.startProcessing(youtubeUrl, apiKey);
      setJobId(result.jobId);
    } catch (err: any) {
      setError(err.response?.data?.message || err.message || 'Failed to start processing');
      setIsProcessing(false);
    }
  };

  const handleDownload = () => {
    if (jobId) {
      window.location.href = api.getDownloadUrl(jobId);
    }
  };

  const handleReset = () => {
    setYoutubeUrl('');
    setJobId(null);
    setStatus(null);
    setPreview([]);
    setError(null);
    setIsProcessing(false);
  };

  return (
    <div className="app">
      <div className="container">
        <h1>Subs2SRS Anki Card Generator</h1>
        <p className="subtitle">Convert YouTube videos to Anki flashcard decks</p>

        {!isProcessing && !status && (
          <form onSubmit={handleSubmit} className="input-form">
            <div className="form-group">
              <label htmlFor="youtube-url">YouTube URL</label>
              <input
                id="youtube-url"
                type="text"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
                className="input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="api-key">AssemblyAI API Key</label>
              <input
                id="api-key"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your AssemblyAI API key"
                className="input"
              />
              <small className="help-text">
                Your API key is stored locally in your browser
              </small>
            </div>

            <button type="submit" className="btn btn-primary">
              Generate Deck
            </button>
          </form>
        )}

        {error && (
          <div className="error-box">
            <strong>Error:</strong> {error}
            <button onClick={handleReset} className="btn btn-secondary" style={{ marginTop: '10px' }}>
              Try Again
            </button>
          </div>
        )}

        {isProcessing && status && (
          <div className="progress-section">
            <h2>Processing...</h2>
            {status.videoTitle && <p className="video-title">{status.videoTitle}</p>}

            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${status.progress}%` }}
              />
            </div>

            <p className="progress-text">
              {status.currentStep} ({status.progress}%)
            </p>

            <div className="status-steps">
              <div className={status.status === 'downloading' ? 'active' : status.progress > 15 ? 'complete' : ''}>
                Downloading video
              </div>
              <div className={status.status === 'extracting' ? 'active' : status.progress > 20 ? 'complete' : ''}>
                Extracting audio
              </div>
              <div className={status.status === 'transcribing' ? 'active' : status.progress > 60 ? 'complete' : ''}>
                Transcribing
              </div>
              <div className={status.status === 'segmenting' ? 'active' : status.progress > 70 ? 'complete' : ''}>
                Segmenting
              </div>
              <div className={status.status === 'generating' ? 'active' : status.progress > 90 ? 'complete' : ''}>
                Generating cards
              </div>
              <div className={status.status === 'creating_deck' ? 'active' : status.progress === 100 ? 'complete' : ''}>
                Creating deck
              </div>
            </div>
          </div>
        )}

        {!isProcessing && status?.status === 'complete' && (
          <div className="complete-section">
            <h2>Complete!</h2>
            {status.videoTitle && <p className="video-title">{status.videoTitle}</p>}
            <p className="cards-count">Generated {status.cardsCount} cards</p>

            {preview.length > 0 && (
              <div className="preview-section">
                <h3>Preview (first {preview.length} cards)</h3>
                <div className="cards-grid">
                  {preview.map((card, index) => (
                    <div key={index} className="card-preview">
                      <img src={card.image} alt={`Card ${index + 1}`} />
                      <audio controls src={card.audio} />
                      <p className="sentence">{card.sentence}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="action-buttons">
              <button onClick={handleDownload} className="btn btn-primary btn-large">
                Download APKG
              </button>
              <button onClick={handleReset} className="btn btn-secondary">
                Create Another Deck
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
