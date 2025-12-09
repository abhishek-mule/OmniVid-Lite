# OmniVid Lite Frontend

A modern React frontend for the OmniVid Lite AI-powered video generation platform.

## Features

- **User Authentication**: API key-based authentication with validation
- **Video Generation**: Real-time prompt input with validation
- **Status Monitoring**: Live polling of job status with progress indicators
- **Video Download**: Secure download of generated videos
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS
- **Error Handling**: Comprehensive error states and user feedback

## Tech Stack

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Axios** for API communication
- **React Hooks** for state management

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Running OmniVid Lite backend on `http://localhost:8000`

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

## API Integration

The frontend communicates with the OmniVid Lite backend API:

- **Authentication**: `X-API-Key` header for all requests
- **Video Generation**: `POST /api/v1/render`
- **Status Polling**: `GET /api/v1/render/status/{job_id}`
- **Video Download**: `GET /api/v1/render/download/{job_id}`

## Component Structure

- `AuthForm`: API key authentication
- `PromptForm`: Video generation prompt input
- `JobStatus`: Real-time job status monitoring
- `VideoDownload`: Generated video download interface
- `App`: Main application coordinator

## Development

### Available Scripts

- `npm start`: Start development server
- `npm test`: Run tests
- `npm run build`: Build for production
- `npm run eject`: Eject from Create React App

### Environment Variables

- `REACT_APP_API_URL`: Backend API URL (default: `http://localhost:8000`)

## CORS Configuration

Ensure the backend allows requests from `http://localhost:3000` for development.