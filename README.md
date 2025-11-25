That is a much better and more detailed flow chart\! It clearly outlines the steps from API request to final download link.

Here is the fully updated, polished, and professional `README.md` file for **Omnivid Lite**, incorporating this new detailed pipeline flow.

-----

# 🚀 Omnivid Lite: Natural Language Video Generation MVP

**Omnivid Lite** is a Minimum Viable Product (MVP) that transforms a simple natural language prompt into a dynamically rendered MP4 video. It provides a simple, API-driven pipeline for generating animated content using the power of Large Language Models (LLMs) and the flexibility of **Remotion**.

-----

## ✨ Features (Clear & Bulletproof)

Omnivid Lite is built around a powerful, automated pipeline for video creation:

  * **Natural-Language → Animation Pipeline:** Automatically converts descriptive text prompts into structured video instructions.
  * **LLM-Powered Scene Extraction:** Uses an LLM to accurately parse the user's prompt and extract key parameters for the animation.
  * **Auto-Generated Remotion `.tsx` Files:** Dynamically creates the necessary TypeScript/Remotion component code for rendering.
  * **Background Rendering Queue:** Manages render jobs asynchronously to prevent API blocking.
  * **MP4 Video Output:** Generates high-quality, final video files using the industry-standard Remotion CLI.
  * **Simple REST API Endpoints:** Dedicated endpoints for initiating a render, checking job status, and downloading the final output.
  * **Zero Configuration Setup:** Designed for easy deployment—just install dependencies, set environment variables, and run.

-----

## 🏗️ High-Level Architecture Overview

The Omnivid Lite architecture follows a robust, linear process to ensure reliability from prompt to final video.

### 🔁 Omnivid Lite – Video Generation Pipeline

The flow chart below illustrates the detailed, asynchronous pipeline from a user's prompt to the final video output:

```mermaid
flowchart TD
    A[User Prompt via /render API] --> B[Validation & Job Creation];
    B --> [LLM Request (OpenAI / Mistral)];
    C --> D[Scene JSON (validated)];
    D --> E[TSX Generator (Dynamic Remotion Scene)];
    E --> F[Write Files to Job Directory];
    F --> G[Queue Task for Renderer];
    G --> H[Worker Picks Job];
    H --> I[Remotion CLI Render → MP4];
    I --> J[Store Output in /renders];
    J --> K[Status: completed + download link];
```

### Core Layers Explained

  * **API Layer:** Built with **FastAPI**, providing simple REST endpoints: `/render`, `/status`, and `/download`.
  * **LLM Layer:** The intelligence core. Converts the natural language prompt into structured, machine-readable animation instructions (**Scene JSON**).
  * **Generation Layer:** Responsible for taking the Scene JSON and programmatically producing the required **Remotion `.tsx`** source files dynamically.
  * **Rendering Layer:** Leverages the **Remotion CLI** to execute the generated `.tsx` code and produce the raw video output.
  * **Storage Layer:** Handles file persistence, saving temporary job files, and storing the final rendered **MP4** output.

-----

## ⚙️ Setup / Installation

Follow these steps to get the Omnivid Lite MVP running locally.

### 1\. Clone the Repository

```bash
git clone https://github.com/yourrepo/omnivid-lite.git
cd omnivid-lite
```

### 2\. Python Environment Setup

```bash
python -m venv venv
source venv/bin/activate             # macOS / Linux
# venv\Scripts\activate              # Windows

pip install -r requirements.txt
```

### 3\. Frontend/Remotion Dependencies

```bash
npm install --prefix renderer/
```

-----

## 🔑 Environment Variables

Create a file named **`.env`** in the project root to configure the necessary API keys and settings.

| Variable | Description | Example Value |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | Your API key for the LLM service. | `your_key_here` |
| `OPENAI_MODEL` | The specific model used for scene extraction. | `gpt-4o-mini` |
| `REMOTION_OUTPUT_DIR` | Local directory for saving final videos. | `renders/` |

-----

## 🏃 Running the MVP

Once set up, you need to run the **FastAPI backend**.

### Start Backend

```bash
uvicorn app.main:app --reload
```

> **Note:** This setup runs the FastAPI server. For full asynchronous rendering as outlined in the pipeline, you would typically need a separate **worker process** running alongside the backend to pick up and execute the queued render tasks.

-----

## 📝 Example API Usage

The backend exposes simple REST endpoints for managing the video generation lifecycle.

### POST to Render (Initiate Job)

Submits a natural language prompt to start the video creation process.

```bash
POST /api/v1/render
```

**Body:**

```json
{
  "prompt": "Create a video with text 'Hello World' that fades in slowly."
}
```

**Response:** (Returns a unique ID for polling)

```json
{ 
  "job_id": "abc123" 
}
```

### Poll Status (Check Progress)

Retrieves the current status of a rendering job.

```bash
GET /api/v1/status/abc123
```

### Download (Retrieve Final MP4)

Downloads the final video file when the job status is `completed`.

```bash
GET /api/v1/download/abc123
```

-----

## 🎬 Example Output

The default pipeline is configured to generate a simple, yet professional, 5-second video output based on the input text.

  * **Duration:** 5 seconds
  * **Content:** Simple text animation derived from the prompt.
  * **Visuals:** White background with smoothly fading-in text.

-----

## 📂 Project Structure Explanation

The project is organized into logical directories separating application logic, rendering assets, and outputs.

```
app/
   main.py             # FastAPI App entry point and configuration
   routes/             # API endpoint definitions (render, status, download)
   services/           # Core business logic (job handling, queue management)
   generators/         # Logic for producing the Remotion .tsx file from JSON
renderer/
   src/                # Remotion source code and components
   remotion.config.ts  # Remotion project configuration
renders/               # Default output directory for final MP4 files
```

The **`app/`** directory contains the core Python backend. **`renderer/`** holds the Remotion project and its dependencies. **`renders/`** is the specified output location for generated videos. This separation keeps the API and the video generation logic distinct and maintainable.

-----

## 🐞 Troubleshooting

| Issue | Potential Cause | Solution |
| :--- | :--- | :--- |
| **Remotion fails to render.** | Missing external dependencies for the Remotion CLI. | Ensure **`ffmpeg`** is installed on your system and accessible from the command line. |
| **Generated `.tsx` file is empty.** | The LLM failed to return a valid Scene JSON payload. | Check the LLM API logs or adjust the LLM prompt instructions for better JSON reliability. |
| **Job stuck in "pending" status.** | The rendering worker process is not running or is blocked. | Verify that the worker process (which handles the render queue) is running and configured correctly. |

-----

## 🗺️ Future Scope

This MVP provides a strong foundation. Planned future features include:

  * **Multiple Scene Support:** Ability to generate videos with complex scene transitions and timelines.
  * **Audio Generation:** Integration with text-to-speech or music generation APIs.
  * **Character Animation:** Support for basic character rigging and movement instructions.
  * **Editor UI:** A web-based interface for prompt input, status monitoring, and output preview.
  * **Template Library:** Pre-defined animation templates for faster, higher-quality output.

-----

Would you like me to elaborate on the **Scene JSON** schema that the LLM is expected to produce?

