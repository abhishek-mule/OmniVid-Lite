import React, { useState, useEffect } from 'react';
import { apiService, JobStatus as JobStatusType, RenderResponse } from '../api';

interface JobStatusProps {
  job: RenderResponse;
  onComplete: (status: JobStatusType) => void;
  onError: (error: string) => void;
}

const JobStatusComponent: React.FC<JobStatusProps> = ({ job, onComplete, onError }) => {
  const [status, setStatus] = useState<JobStatusType | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const [pollCount, setPollCount] = useState(0);

  useEffect(() => {
    const pollStatus = async () => {
      try {
        const jobStatus = await apiService.getJobStatus(job.job_id);
        setStatus(jobStatus);
        setPollCount(prev => prev + 1);

        if (jobStatus.status === 'done') {
          setIsPolling(false);
          onComplete(jobStatus);
        } else if (jobStatus.status === 'failed') {
          setIsPolling(false);
          onError(jobStatus.error || 'Job failed');
        }
      } catch (err) {
        console.error('Failed to poll job status:', err);
        // Continue polling on network errors
      }
    };

    // Initial poll
    pollStatus();

    // Set up polling interval
    const interval = setInterval(pollStatus, 3000); // Poll every 3 seconds

    return () => clearInterval(interval);
  }, [job.job_id, onComplete, onError]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'text-yellow-600 bg-yellow-100';
      case 'queued':
        return 'text-blue-600 bg-blue-100';
      case 'processing':
        return 'text-purple-600 bg-purple-100';
      case 'done':
        return 'text-green-600 bg-green-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return '⏳';
      case 'queued':
        return '📋';
      case 'processing':
        return '⚙️';
      case 'done':
        return '✅';
      case 'failed':
        return '❌';
      default:
        return '❓';
    }
  };

  const getProgressPercentage = () => {
    if (!status) return 0;
    // Map status to rough progress estimates
    switch (status.status) {
      case 'pending':
        return 10;
      case 'queued':
        return 25;
      case 'processing':
        return Math.min(90, 30 + (pollCount * 5)); // Gradually increase during processing
      case 'done':
        return 100;
      case 'failed':
        return 0;
      default:
        return 0;
    }
  };

  if (!status) {
    return (
      <div className="bg-white shadow-lg rounded-lg p-6">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Loading job status...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow-lg rounded-lg p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">
            Job Status
          </h3>
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(status.status)}`}>
            {getStatusIcon(status.status)} {status.status.toUpperCase()}
          </span>
        </div>
        <p className="mt-1 text-sm text-gray-600">
          Job ID: <code className="bg-gray-100 px-1 rounded">{job.job_id}</code>
        </p>
      </div>

      <div className="space-y-4">
        {/* Progress Bar */}
        <div>
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Progress</span>
            <span>{getProgressPercentage()}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${getProgressPercentage()}%` }}
            ></div>
          </div>
        </div>

        {/* Status Details */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium text-gray-700">Created:</span>
            <p className="text-gray-600">{new Date(status.created_at).toLocaleString()}</p>
          </div>
          <div>
            <span className="font-medium text-gray-700">Updated:</span>
            <p className="text-gray-600">{new Date(status.updated_at).toLocaleString()}</p>
          </div>
        </div>

        {/* Polling Status */}
        {isPolling && (
          <div className="flex items-center text-sm text-gray-600">
            <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Checking status... (polled {pollCount} times)
          </div>
        )}

        {/* Error Display */}
        {status.error && (
          <div className="rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Job Error
                </h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{status.error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Success Message */}
        {status.status === 'done' && (
          <div className="rounded-md bg-green-50 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">
                  Video Generated Successfully!
                </h3>
                <div className="mt-2 text-sm text-green-700">
                  <p>Your video is ready for download.</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default JobStatusComponent;