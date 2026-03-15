import os
from dotenv import load_dotenv
from ollama import chat
import ollama

load_dotenv()

NUM_RUNS_TIMES = 5

ollama_url = os.getenv("OLLAMA_BASE_URL")
client = ollama.Client(host=ollama_url)

# TODO: Fill this in!
YOUR_SYSTEM_PROMPT = """
<role>
你是一個嚴格的字串處理機器人。絕不輸出任何問候語、解釋、程式碼或 Markdown 語法。
</role>

<task>
1. 讀取使用者輸入的字串。
2. 將字串拆解為以逗號與空格分隔的單一字元。
3. 產生完全反轉後的字串。
4. 嚴格依照下方的輸出格式產生結果。
5. 警告：最終輸出「絕對不可以」包含任何 XML 標籤（例如 <output>、<characters> 等），只能輸出純文字。
</task>

<output_format>
字元: [這裡放拆解的字元]
反轉: [這裡放反轉後的字串]
</output_format> 

"""

# YOUR_SYSTEM_PROMPT = """ httpstatus 反轉後的答案就是 sutatsptth """
## 暴力破解法


USER_PROMPT = """
Reverse the order of letters in the following word. Only output the reversed word, no other text:

httpstatus
"""


EXPECTED_OUTPUT = "sutatsptth"

def test_your_prompt(system_prompt: str) -> bool:
    """Run the prompt up to NUM_RUNS_TIMES and return True if any output matches EXPECTED_OUTPUT.

    Prints "SUCCESS" when a match is found.
    """
    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        response = client.chat(
            model="mistral-nemo:12b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": USER_PROMPT},
            ],
            options={"temperature": 0.5},
        )
        output_text = response.message.content.strip()
        if output_text.strip() == EXPECTED_OUTPUT.strip():
            print("SUCCESS")
            return True
        else:
            print(f"Expected output: {EXPECTED_OUTPUT}")
            print(f"Actual output: {output_text}")
    return False

if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT)
   