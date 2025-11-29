# Human-Assisted Browser Automation Flow

This tool orchestrates a 7-phase workflow between Gemini and ChatGPT, assisting you by generating prompts and extracting responses, while keeping you in control of the final submission.

## Prerequisites

1.  **Python 3.8+**
2.  **Playwright**:
    ```bash
    pip install playwright pyperclip
    playwright install chromium
    ```

## Setup

1.  **Configuration**:
    - Edit `config.json` if you want to change the prompts or the number of phases.
    - The `selectors` in `config.json` might need updating if ChatGPT or Gemini change their UI.

2.  **Browser Data**:
    - The script uses a local `user_data` directory to keep you logged in.
    - The first time you run it, you will need to log in to Gemini and ChatGPT manually.

## Usage

1.  Run the script:
    ```bash
    python main.py
    ```

2.  **Initialization**:
    - Two browser windows (tabs) will open: Gemini and ChatGPT.
    - Log in if necessary.
    - Press **Enter** in the terminal when ready.

3.  **The Flow**:
    - The script will generate the prompt for the current phase.
    - It will switch to the target browser tab and attempt to paste the prompt.
    - **YOUR JOB**:
        - Verify the prompt is in the input box (paste it manually with Ctrl+V if needed).
        - **Press ENTER** in the browser to send the message.
        - Wait for the response to finish generating.
    - **Back in the Terminal**:
        - Press **Enter** to tell the script the response is ready.
    - The script will scrape the text, take a screenshot, and move to the next phase.

4.  **Output**:
    - `final_article.md`: The combined output of all phases.
    - `screenshots/`: Screenshots of each response.
    - `gemini_output/` & `chatgpt_output/`: Individual text files.

## Safety & Compliance

- This tool **does not** use undocumented APIs.
- It **does not** automatically press the "Send" button.
- You are responsible for the final action, ensuring compliance with Terms of Service.
