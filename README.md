# Script Manager

This directory contains scripts for processing audience conversations and generating AI-powered insights.

## Scripts

### script1.py - Audience Conversation Processor

**Purpose**: Monitors MongoDB for pending audience conversations and generates:
- Summary of the conversation
- 10 Keywords extracted from the summary
- 10 Phrases generated from the keywords

**Features**:
- Continuous monitoring of `audience_conversations` collection
- Processes conversations with status "pending"
- Updates status to "completed" after processing
- Uses LLM model: `itlwas/hermes-3-llama-3.1-8b`
- Comprehensive logging and error handling

**Usage**:
```bash
# Run monitoring loop (processes all pending conversations)
python script1.py

# Process specific conversation
python script1.py <conversation_id>
```

**Requirements**:
- LM Studio running with the specified model
- MongoDB connection to `audience_dropper` database
- Python dependencies: pymongo, requests


### start_script1.bat

Windows batch file to easily start script1.py with user confirmation.

## Configuration

The script uses the following MongoDB connection:
```
mongodb+srv://haoga9764:hXbB7fmzpuBJAIr4@cluster0.kmpjdcz.mongodb.net/audience_dropper?retryWrites=true&w=majority&appName=Cluster0
```

LLM Server configuration:
- Base URL: `http://localhost:1234`
- Model: `itlwas/hermes-3-llama-3.1-8b`

## Database Schema

The script monitors the `audience_conversations` collection with the following status flow:
1. `pending` - Conversation ready for processing
2. `processing` - Currently being processed
3. `completed` - Successfully processed with results
4. `failed` - Processing failed with error details

## Results Structure

After processing, the conversation document is updated with:
```json
{
  "summary": "AI-generated summary of the conversation",
  "keywords": ["keyword1", "keyword2", ...],
  "phrases": ["phrase1", "phrase2", ...],
  "processed_at": "2024-01-01T00:00:00Z",
  "llm_model": "itlwas/hermes-3-llama-3.1-8b"
}
```

## Integration

The script integrates with the Flask web application through:
- `/audiences/process-conversation/<audience_id>` - Process specific conversation
- `/audiences/start-script1` - Start background monitoring

## Logging

All operations are logged to:
- Console output
- `script1.log` file

## Error Handling

The script includes comprehensive error handling for:
- MongoDB connection issues
- LLM server unavailability
- Processing failures
- Network timeouts

## Troubleshooting

If you encounter issues:

1. **LLM Server Connection Failed**:
   - Make sure LM Studio is running
   - Check that the server is started (Local Server tab)
   - Verify the model `itlwas/hermes-3-llama-3.1-8b` is loaded
   - Check that port 1234 is not blocked by firewall

2. **MongoDB Connection Issues**:
   - Verify the MongoDB URI is correct
   - Check network connectivity
   - Ensure the database and collection exist
