import React, { useState, useEffect } from 'react';
import { apiService } from '../api';

interface AIStatusData {
  local_llm: {
    enabled: boolean;
    model?: string;
    url?: string;
    status: string;
    error?: string;
  };
  openai: {
    enabled: boolean;
    model?: string;
    status: string;
    error?: string;
  };
  overall_status: string;
  message: string;
}

const AIStatus: React.FC = () => {
  const [aiStatus, setAiStatus] = useState<AIStatusData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const checkAIStatus = async () => {
      try {
        setIsLoading(true);
        const status = await apiService.checkAIStatus();
        setAiStatus(status);
        setError('');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to check AI status');
      } finally {
        setIsLoading(false);
      }
    };

    checkAIStatus();
    // Check every 30 seconds
    const interval = setInterval(checkAIStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available':
        return 'text-green-600 bg-green-100';
      case 'unavailable':
        return 'text-red-600 bg-red-100';
      case 'unknown':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'available':
        return '🟢';
      case 'unavailable':
        return '🔴';
      case 'unknown':
        return '🟡';
      default:
        return '⚪';
    }
  };

  const getOverallStatusInfo = (status: string) => {
    switch (status) {
      case 'ai_available':
        return {
          color: 'text-green-600 bg-green-100',
          icon: '🤖',
          text: 'AI Available'
        };
      case 'fallback_only':
        return {
          color: 'text-blue-600 bg-blue-100',
          icon: '✨',
          text: 'Enhanced Mode'
        };
      default:
        return {
          color: 'text-yellow-600 bg-yellow-100',
          icon: '⏳',
          text: 'Checking...'
        };
    }
  };

  if (isLoading && !aiStatus) {
    return (
      <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-gray-600 bg-gray-100">
        <div className="animate-spin rounded-full h-3 w-3 border border-gray-300 mr-1"></div>
        Checking AI...
      </div>
    );
  }

  if (error) {
    return (
      <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-red-600 bg-red-100">
        ⚠️ AI Status Error
      </div>
    );
  }

  if (!aiStatus) return null;

  const overallInfo = getOverallStatusInfo(aiStatus.overall_status);

  return (
    <div className="relative group">
      <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium cursor-help ${overallInfo.color}`}>
        <span className="mr-1">{overallInfo.icon}</span>
        {overallInfo.text}
      </div>

      {/* Tooltip */}
      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10 whitespace-nowrap">
        <div className="font-medium mb-1">{aiStatus.message}</div>

        {/* Local LLM Status */}
        {aiStatus.local_llm.enabled && (
          <div className="mb-1">
            <span className="font-medium">Local LLM:</span>
            <span className={`ml-1 ${getStatusColor(aiStatus.local_llm.status)}`}>
              {getStatusIcon(aiStatus.local_llm.status)} {aiStatus.local_llm.status}
            </span>
            {aiStatus.local_llm.model && (
              <span className="ml-1 text-gray-300">({aiStatus.local_llm.model})</span>
            )}
          </div>
        )}

        {/* OpenAI Status */}
        {aiStatus.openai.enabled && (
          <div>
            <span className="font-medium">OpenAI:</span>
            <span className={`ml-1 ${getStatusColor(aiStatus.openai.status)}`}>
              {getStatusIcon(aiStatus.openai.status)} {aiStatus.openai.status}
            </span>
            {aiStatus.openai.model && (
              <span className="ml-1 text-gray-300">({aiStatus.openai.model})</span>
            )}
          </div>
        )}

        <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
      </div>
    </div>
  );
};

export default AIStatus;