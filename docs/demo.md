# Backlog CLI Demo

## Usage Example

This document contains instructions for creating a demo GIF showing the Backlog CLI tool in action.

### Steps to Record Demo

1. Open a PowerShell terminal
2. Create a sample dictation.txt file with some text
3. Run the following commands:
   ```powershell
   # Show the dictation text
   cat dictation.txt
   
   # Process with backlog CLI
   cat dictation.txt | bckl
   
   # Show the resulting backlog.csv
   cat backlog.csv | Select-Object -First 5
   ```

4. Record these steps using a screen recorder like [ScreenToGif](https://www.screentogif.com/)
5. Save the resulting GIF as `docs/assets/demo.gif`

## Demo Script

Here's a sample script for the demo:

1. Start with a dictation.txt containing:
   ```
   Need to add unit tests for the new authentication module. Should cover both success and failure paths, and test token expiration handling.
   ```

2. Run the CLI:
   ```
   cat dictation.txt | bckl --verbose
   ```

3. Show the resulting entry in backlog.csv

This demonstrates the core workflow of converting natural language dictation into structured backlog entries.
