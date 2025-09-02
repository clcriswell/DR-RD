# Troubleshooting

## Missing API Keys
The app requires `OPENAI_API_KEY` for language models. Web search backends need `SERPAPI_KEY` or other provider keys. Ensure these are set in Streamlit secrets or environment variables.

## API Quotas or Rate Limits
If runs stop early or return errors, you may have hit a provider quota. Wait before retrying or reduce the number of runs.

## Empty or Incomplete Results
Check that the selected mode enables retrieval and live search. Lack of knowledge sources or disabled RAG may yield empty answers.

## PDF Generation Errors
The PDF exporter supports up to 50 pages. Larger documents or malformed Markdown may fail to render.

## Unicode or Encoding Issues
If output shows garbled characters, ensure your terminal and browser use UTF‑8 encoding.
