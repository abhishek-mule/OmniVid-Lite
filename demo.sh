#!/bin/bash

# Demo script for OmniVid Lite production system

echo "🚀 Starting OmniVid Lite Demo"
echo "=============================="

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis not running. Start with: docker-compose up -d redis"
    exit 1
fi

# Check if worker is running
if ! pgrep -f "arq tasks" > /dev/null; then
    echo "⚠️  Worker not running. Start with: arq tasks"
fi

echo "📝 Creating a video generation job..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/render/render \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"A blue circle moves from left to right on a white background","creative":false}')

JOB_ID=$(echo $RESPONSE | jq -r '.job_id')
echo "✅ Job created: $JOB_ID"

echo ""
echo "📊 Polling job status..."
for i in {1..30}; do
    STATUS=$(curl -s http://localhost:8000/api/v1/render/status/$JOB_ID)
    STATE=$(echo $STATUS | jq -r '.status')
    PROGRESS=$(echo $STATUS | jq -r '.progress')

    echo "Status: $STATE (Progress: $PROGRESS%)"

    if [ "$STATE" = "completed" ]; then
        echo "🎉 Job completed!"
        OUTPUT_PATH=$(echo $STATUS | jq -r '.output_path')
        echo "📁 Output: $OUTPUT_PATH"
        break
    elif [ "$STATE" = "failed" ]; then
        echo "❌ Job failed"
        ERROR=$(echo $STATUS | jq -r '.error')
        echo "Error: $ERROR"
        break
    fi

    sleep 2
done

echo ""
echo "📋 Recent jobs:"
curl -s http://localhost:8000/api/v1/render/jobs | jq '.jobs[0:3]'

echo ""
echo "🎬 Demo complete!"