import React, { useState } from 'react';
import { apiService, RenderRequest, RenderResponse } from '../api';

interface PromptFormProps {
  onJobStarted: (response: RenderResponse) => void;
}

const PromptForm: React.FC<PromptFormProps> = ({ onJobStarted }) => {
  const [prompt, setPrompt] = useState('');
  const [creative, setCreative] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const validatePrompt = (text: string): string | null => {
    const trimmed = text.trim();
    if (!trimmed) {
      return 'Prompt cannot be empty';
    }
    if (trimmed.length < 10) {
      return 'Prompt must be at least 10 characters long';
    }
    if (trimmed.length > 1000) {
      return 'Prompt must be less than 1000 characters';
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const validationError = validatePrompt(prompt);
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const request: RenderRequest = {
        prompt: prompt.trim(),
        creative,
      };

      const response = await apiService.startRender(request);
      onJobStarted(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start video generation');
    } finally {
      setIsSubmitting(false);
    }
  };

  const characterCount = prompt.length;
  const isValid = !validatePrompt(prompt);

  return (
    <div className="bg-white shadow-lg rounded-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Create Your Video
        </h2>
        <p className="text-gray-600">
          Describe the video you want to generate using AI
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
            Video Description
          </label>
          <textarea
            id="prompt"
            rows={4}
            className={`block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm resize-none ${
              !isValid && prompt ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''
            }`}
            placeholder="Describe your video in detail... e.g., 'A serene mountain landscape at sunset with flowing water and gentle wind'"
            value={prompt}
            onChange={(e) => {
              setPrompt(e.target.value);
              setError('');
            }}
            disabled={isSubmitting}
          />
          <div className="mt-2 flex justify-between items-center">
            <div className="text-sm text-gray-500">
              {characterCount}/1000 characters
            </div>
            <div className={`text-sm ${characterCount > 900 ? 'text-red-600' : characterCount > 800 ? 'text-yellow-600' : 'text-gray-500'}`}>
              {characterCount > 1000 ? 'Too long' : characterCount < 10 ? 'Too short' : 'Good length'}
            </div>
          </div>
        </div>

        <div className="flex items-center">
          <input
            id="creative"
            type="checkbox"
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            checked={creative}
            onChange={(e) => setCreative(e.target.checked)}
            disabled={isSubmitting}
          />
          <label htmlFor="creative" className="ml-2 block text-sm text-gray-900">
            Creative mode (more experimental results)
          </label>
        </div>

        {error && (
          <div className="rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Error
                </h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        <div>
          <button
            type="submit"
            disabled={isSubmitting || !isValid}
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <div className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generating Video...
              </div>
            ) : (
              'Generate Video'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default PromptForm;