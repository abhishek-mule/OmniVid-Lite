import React, { useState } from 'react';
import { apiService, JobStatus } from '../api';

interface VideoDownloadProps {
  jobStatus: JobStatus;
}

const VideoDownload: React.FC<VideoDownloadProps> = ({ jobStatus }) => {
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState('');

  const handleDownload = async () => {
    if (!jobStatus.output_path) {
      setDownloadError('No video file available');
      return;
    }

    setIsDownloading(true);
    setDownloadError('');

    try {
      const blob = await apiService.downloadVideo(jobStatus.job_id);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // Extract filename from output path or use default
      const filename = jobStatus.output_path.split('/').pop() || `video-${jobStatus.job_id}.mp4`;
      link.download = filename;

      // Trigger download
      document.body.appendChild(link);
      link.click();

      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (err) {
      setDownloadError(err instanceof Error ? err.message : 'Download failed');
    } finally {
      setIsDownloading(false);
    }
  };


  return (
    <div className="bg-white shadow-lg rounded-lg p-6">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2">
          Your Video is Ready!
        </h3>
        <p className="text-gray-600">
          Job completed successfully. Download your generated video below.
        </p>
      </div>

      <div className="space-y-4">
        {/* Video Info */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Job ID:</span>
              <p className="text-gray-600 font-mono">{jobStatus.job_id}</p>
            </div>
            <div>
              <span className="font-medium text-gray-700">Completed:</span>
              <p className="text-gray-600">{new Date(jobStatus.updated_at).toLocaleString()}</p>
            </div>
          </div>
          {jobStatus.output_path && (
            <div className="mt-2">
              <span className="font-medium text-gray-700">File:</span>
              <p className="text-gray-600 font-mono text-xs break-all">{jobStatus.output_path}</p>
            </div>
          )}
        </div>

        {/* Download Button */}
        <div>
          <button
            onClick={handleDownload}
            disabled={isDownloading}
            className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isDownloading ? (
              <div className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Downloading...
              </div>
            ) : (
              <div className="flex items-center">
                <svg className="-ml-1 mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Download Video
              </div>
            )}
          </button>
        </div>

        {/* Error Display */}
        {downloadError && (
          <div className="rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Download Error
                </h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{downloadError}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Success Message */}
        {!downloadError && !isDownloading && (
          <div className="rounded-md bg-blue-50 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">
                  Video Ready
                </h3>
                <div className="mt-2 text-sm text-blue-700">
                  <p>Your AI-generated video is ready for download. Click the button above to save it to your device.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Additional Actions */}
        <div className="flex space-x-3 pt-4 border-t border-gray-200">
          <button
            onClick={() => window.open('http://localhost:8000/docs', '_blank')}
            className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 py-2 px-4 rounded-md text-sm font-medium transition-colors"
          >
            API Docs
          </button>
          <button
            onClick={() => window.location.reload()}
            className="flex-1 bg-blue-100 hover:bg-blue-200 text-blue-700 py-2 px-4 rounded-md text-sm font-medium transition-colors"
          >
            Create Another
          </button>
        </div>
      </div>
    </div>
  );
};

export default VideoDownload;