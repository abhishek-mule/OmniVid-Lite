import React, { useState, useEffect } from 'react';
import AuthForm from './components/AuthForm';
import PromptForm from './components/PromptForm';
import JobStatus from './components/JobStatus';
import VideoDownload from './components/VideoDownload';
import AIStatus from './components/AIStatus';
import { apiService, RenderResponse, JobStatus as JobStatusType } from './api';

type AppState = 'auth' | 'create' | 'status' | 'download';

function App() {
  const [appState, setAppState] = useState<AppState>('auth');
  const [currentJob, setCurrentJob] = useState<RenderResponse | null>(null);
  const [completedJob, setCompletedJob] = useState<JobStatusType | null>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    // Check if user is already authenticated
    const savedApiKey = localStorage.getItem('apiKey');
    if (savedApiKey) {
      apiService.setApiKey(savedApiKey);
      setAppState('create');
    }
  }, []);

  const handleAuthenticated = (apiKey: string) => {
    setAppState('create');
  };

  const handleJobStarted = (job: RenderResponse) => {
    setCurrentJob(job);
    setAppState('status');
    setError('');
  };

  const handleJobComplete = (status: JobStatusType) => {
    setCompletedJob(status);
    setAppState('download');
  };

  const handleJobError = (errorMessage: string) => {
    setError(errorMessage);
    // Stay in status view to show error
  };

  const handleLogout = () => {
    apiService.setApiKey('');
    localStorage.removeItem('apiKey');
    setAppState('auth');
    setCurrentJob(null);
    setCompletedJob(null);
    setError('');
  };

  const handleCreateAnother = () => {
    setAppState('create');
    setCurrentJob(null);
    setCompletedJob(null);
    setError('');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </div>
              <div className="ml-3">
                <h1 className="text-xl font-bold text-gray-900">OmniVid Lite</h1>
                <p className="text-sm text-gray-500">AI-Powered Video Generation</p>
              </div>
            </div>

            {appState !== 'auth' && (
              <div className="flex items-center space-x-4">
                <AIStatus />
                <a
                  href="http://localhost:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-600 hover:text-gray-900 text-sm font-medium"
                >
                  API Docs
                </a>
                <button
                  onClick={handleLogout}
                  className="text-gray-600 hover:text-gray-900 text-sm font-medium"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {appState === 'auth' && (
          <AuthForm onAuthenticated={handleAuthenticated} />
        )}

        {appState === 'create' && (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-900">Generate Your Video</h2>
              <p className="mt-2 text-gray-600">
                Describe what you want to see, and our AI will create a video for you
              </p>
            </div>
            <PromptForm onJobStarted={handleJobStarted} />
          </div>
        )}

        {appState === 'status' && currentJob && (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-900">Generating Your Video</h2>
              <p className="mt-2 text-gray-600">
                Please wait while our AI creates your video
              </p>
            </div>
            <JobStatus
              job={currentJob}
              onComplete={handleJobComplete}
              onError={handleJobError}
            />
            {error && (
              <div className="bg-white shadow-lg rounded-lg p-6">
                <div className="rounded-md bg-red-50 p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-red-800">
                        Generation Failed
                      </h3>
                      <div className="mt-2 text-sm text-red-700">
                        <p>{error}</p>
                      </div>
                      <div className="mt-4">
                        <button
                          onClick={handleCreateAnother}
                          className="bg-red-100 hover:bg-red-200 text-red-700 py-2 px-4 rounded-md text-sm font-medium"
                        >
                          Try Again
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {appState === 'download' && completedJob && (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-900">Video Complete!</h2>
              <p className="mt-2 text-gray-600">
                Your AI-generated video is ready for download
              </p>
            </div>
            <VideoDownload jobStatus={completedJob} />
            <div className="text-center">
              <button
                onClick={handleCreateAnother}
                className="bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-md text-lg font-medium"
              >
                Create Another Video
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <div className="text-center text-sm text-gray-500">
            <p>OmniVid Lite - AI-powered video generation</p>
            <p className="mt-1">
              Powered by FastAPI, React, and advanced AI models
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;