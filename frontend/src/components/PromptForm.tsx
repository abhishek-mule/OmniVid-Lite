import React, { useState, useEffect } from 'react';
import { apiService, RenderRequest, RenderResponse } from '../api';

interface PromptFormProps {
  onJobStarted: (response: RenderResponse) => void;
}

interface VideoSection {
  id: string;
  name: string;
  description: string;
  templates: string[];
}

interface VideoParameters {
  duration: number;
  resolution: '720p' | '1080p' | '4k';
  style: 'minimal' | 'vibrant' | 'cinematic' | 'abstract';
  textAnimation: 'fade' | 'slide' | 'bounce' | 'typewriter';
}

const VIDEO_SECTIONS: VideoSection[] = [
  {
    id: 'text-only',
    name: 'Text Animation',
    description: 'Simple text animations with fade effects',
    templates: [
      'Create a video with the text "{text}" that fades in smoothly',
      'Display "{text}" with elegant typography and gentle transitions',
      'Show "{text}" with modern text animation effects'
    ]
  },
  {
    id: 'educational',
    name: 'Educational Content',
    description: 'Learning videos with clear explanations',
    templates: [
      'Create an educational video explaining "{text}" with clear visuals',
      'Make a tutorial video about "{text}" with step-by-step animations',
      'Design a learning video that teaches "{text}" effectively'
    ]
  },
  {
    id: 'promotional',
    name: 'Promotional Content',
    description: 'Marketing and promotional videos',
    templates: [
      'Create an engaging promotional video for "{text}"',
      'Design a compelling advertisement featuring "{text}"',
      'Make an attractive marketing video about "{text}"'
    ]
  },
  {
    id: 'social-media',
    name: 'Social Media',
    description: 'Short-form content for social platforms',
    templates: [
      'Create a viral social media video about "{text}"',
      'Design a trending TikTok-style video for "{text}"',
      'Make an engaging Instagram Reel featuring "{text}"'
    ]
  },
  {
    id: 'custom',
    name: 'Custom',
    description: 'Fully customizable video generation',
    templates: [
      '{text}',
      'Generate a video based on: {text}',
      'Create custom video content for: {text}'
    ]
  }
];

const PromptForm: React.FC<PromptFormProps> = ({ onJobStarted }) => {
  const [selectedSection, setSelectedSection] = useState<string>('text-only');
  const [customPrompt, setCustomPrompt] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<number>(0);
  const [parameters, setParameters] = useState<VideoParameters>({
    duration: 5,
    resolution: '1080p',
    style: 'minimal',
    textAnimation: 'fade'
  });
  const [creative, setCreative] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const getCurrentSection = () => VIDEO_SECTIONS.find(s => s.id === selectedSection) || VIDEO_SECTIONS[0];

  const getCurrentPrompt = () => {
    if (selectedSection === 'custom') {
      return customPrompt;
    }
    const section = getCurrentSection();
    return section.templates[selectedTemplate]?.replace('{text}', customPrompt) || customPrompt;
  };

  const validatePrompt = (text: string): string | null => {
    const trimmed = text.trim();
    if (!trimmed) {
      return 'Prompt cannot be empty';
    }
    if (trimmed.length < 3) {
      return 'Prompt must be at least 3 characters long';
    }
    if (trimmed.length > 1000) {
      return 'Prompt must be less than 1000 characters';
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const currentPrompt = getCurrentPrompt();
    const validationError = validatePrompt(currentPrompt);
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const request: RenderRequest = {
        prompt: currentPrompt.trim(),
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

  const currentPrompt = getCurrentPrompt();
  const characterCount = currentPrompt.length;
  const isValid = !validatePrompt(currentPrompt);

  return (
    <div className="bg-white shadow-lg rounded-lg p-4 sm:p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Create Your Video
        </h2>
        <p className="text-gray-600">
          Choose a generation type and customize your video parameters
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Section Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2" title="Choose the type of video you want to generate">
            Video Type
          </label>
          <select
            value={selectedSection}
            onChange={(e) => setSelectedSection(e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            disabled={isSubmitting}
            title="Select video generation category"
          >
            {VIDEO_SECTIONS.map((section) => (
              <option key={section.id} value={section.id} title={section.description}>
                {section.name} - {section.description}
              </option>
            ))}
          </select>
        </div>

        {/* Template Selection */}
        {selectedSection !== 'custom' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2" title="Choose a prompt template for your video type">
              Template
            </label>
            <select
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(parseInt(e.target.value))}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              disabled={isSubmitting}
              title="Select a pre-built prompt template"
            >
              {getCurrentSection().templates.map((template, index) => (
                <option key={index} value={index} title={template}>
                  Template {index + 1}: {template.replace('{text}', '[Your Text]').substring(0, 50)}...
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Custom Prompt Input */}
        <div>
          <label htmlFor="customPrompt" className="block text-sm font-medium text-gray-700 mb-2">
            {selectedSection === 'custom' ? 'Custom Prompt' : 'Your Text'}
          </label>
          <textarea
            id="customPrompt"
            rows={3}
            className={`block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm resize-none ${
              !isValid && customPrompt ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''
            }`}
            placeholder={selectedSection === 'custom'
              ? "Describe your video in detail..."
              : "Enter the main text for your video..."
            }
            value={customPrompt}
            onChange={(e) => {
              setCustomPrompt(e.target.value);
              setError('');
            }}
            disabled={isSubmitting}
          />
          <div className="mt-2 flex justify-between items-center">
            <div className="text-sm text-gray-500">
              {characterCount}/1000 characters
            </div>
            <div className={`text-sm ${characterCount > 900 ? 'text-red-600' : characterCount > 800 ? 'text-yellow-600' : 'text-gray-500'}`}>
              {characterCount > 1000 ? 'Too long' : characterCount < 3 ? 'Too short' : 'Good length'}
            </div>
          </div>
        </div>

        {/* Preview of Generated Prompt */}
        {currentPrompt && currentPrompt !== customPrompt && (
          <div className="bg-blue-50 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-900 mb-2">Generated Prompt Preview:</h4>
            <p className="text-sm text-blue-800 italic">"{currentPrompt}"</p>
          </div>
        )}

        {/* Advanced Options Toggle */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-blue-600 hover:text-blue-500 font-medium transition-colors"
            title="Customize video parameters like duration, resolution, and style"
          >
            {showAdvanced ? 'Hide' : 'Show'} Advanced Options
          </button>
          <span className="text-xs text-gray-500 hidden sm:inline">
            Optional settings for fine-tuning
          </span>
        </div>

        {/* Advanced Options */}
        {showAdvanced && (
          <div className="space-y-4 bg-gray-50 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-900">Video Parameters</h4>

            {/* Duration Slider */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2" title="Video length in seconds (3-15)">
                Duration: {parameters.duration} seconds
              </label>
              <input
                type="range"
                min="3"
                max="15"
                value={parameters.duration}
                onChange={(e) => setParameters({...parameters, duration: parseInt(e.target.value)})}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                disabled={isSubmitting}
                title={`Set video duration to ${parameters.duration} seconds`}
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>3s</span>
                <span>9s</span>
                <span>15s</span>
              </div>
            </div>

            {/* Resolution Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2" title="Video resolution affects file size and quality">
                Resolution
              </label>
              <select
                value={parameters.resolution}
                onChange={(e) => setParameters({...parameters, resolution: e.target.value as any})}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                disabled={isSubmitting}
                title="Choose video resolution"
              >
                <option value="720p" title="1280x720 - Good quality, smaller file">720p HD</option>
                <option value="1080p" title="1920x1080 - High quality, standard size">1080p Full HD</option>
                <option value="4k" title="3840x2160 - Ultra high quality, large file">4K Ultra HD</option>
              </select>
            </div>

            {/* Style Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2" title="Visual style affects colors and overall appearance">
                Visual Style
              </label>
              <select
                value={parameters.style}
                onChange={(e) => setParameters({...parameters, style: e.target.value as any})}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                disabled={isSubmitting}
                title="Select visual theme"
              >
                <option value="minimal" title="Clean, simple design">Minimal</option>
                <option value="vibrant" title="Bright, colorful design">Vibrant</option>
                <option value="cinematic" title="Movie-like, dramatic effects">Cinematic</option>
                <option value="abstract" title="Modern, artistic design">Abstract</option>
              </select>
            </div>

            {/* Animation Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2" title="How text appears and moves in the video">
                Text Animation
              </label>
              <select
                value={parameters.textAnimation}
                onChange={(e) => setParameters({...parameters, textAnimation: e.target.value as any})}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                disabled={isSubmitting}
                title="Choose text animation style"
              >
                <option value="fade" title="Text fades in and out smoothly">Fade In/Out</option>
                <option value="slide" title="Text slides in from the side">Slide In</option>
                <option value="bounce" title="Text bounces into view">Bounce</option>
                <option value="typewriter" title="Text appears character by character">Typewriter</option>
              </select>
            </div>
          </div>
        )}

        {/* Creative Mode */}
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

        {/* Error Display */}
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

        {/* Submit Button */}
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
              <div className="flex items-center">
                <svg className="-ml-1 mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Generate Video
              </div>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default PromptForm;