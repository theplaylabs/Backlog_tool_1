# Backlog CLI Architecture

## Component Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  User Input     │────▶│  CLI Parser     │────▶│  OpenAI Client  │
│  (dictation)    │     │  (argparse)     │     │  (API calls)    │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  backlog.csv    │◀────│  CSV Store      │◀────│  JSON Schema    │
│  (data store)   │     │  (atomic write) │     │  (validation)   │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Data Flow

1. **User Input**: Text from stdin or file
2. **CLI Parser**: Processes arguments and flags
3. **OpenAI Client**: Sends text to API, receives structured response
4. **JSON Schema**: Validates API response format
5. **CSV Store**: Prepends new entry to CSV file atomically
6. **Logging**: Records operations to rotating log file

## Module Structure

- `cli.py`: Entry point, argument parsing
- `openai_client.py`: API interaction, retry logic
- `csv_store.py`: File operations, atomic writes
- `config.py`: Configuration, environment variables, logging setup

## Configuration

Environment variables and defaults are managed through the `Config` dataclass:
- API model selection
- Logging directory and level
- Dotenv support for local development

## Error Handling

- Graceful handling of API failures with retries
- Atomic file operations to prevent data corruption
- Comprehensive logging for troubleshooting
