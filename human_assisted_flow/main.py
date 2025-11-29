import json
import os
import time
import pyperclip
import re
from playwright.sync_api import sync_playwright

# Load configuration
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

def ensure_directories():
    """フロー実行ごとにタイムスタンプ付きフォルダを作成"""
    from datetime import datetime
    
    # タイムスタンプ付きフォルダ名を生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    flow_folder = f"output/flow_{timestamp}"
    
    # 各サブフォルダを作成
    os.makedirs(f"{flow_folder}/screenshots", exist_ok=True)
    os.makedirs(f"{flow_folder}/gemini_output", exist_ok=True)
    os.makedirs(f"{flow_folder}/chatgpt_output", exist_ok=True)
    
    return flow_folder

def append_to_final_article(text, phase_name, flow_folder):
    """最終記事ファイルにテキストを追記"""
    # Phase_0_Format は除外（フォーマット定義の確認応答のみなので不要）
    if phase_name == "Phase_0_Format":
        return
    
    # Phase情報のヘッダーは追加せず、Geminiの回答をそのまま保存
    with open(f"{flow_folder}/final_article.md", "a", encoding="utf-8") as f:
        f.write(f"\n\n{text}")

def get_latest_response(page, selector):
    print(f"回答要素を待機中: {selector}")
    try:
        page.wait_for_selector(selector, timeout=120000) # 2 min timeout
        elements = page.query_selector_all(selector)
        if not elements:
            return None, None
        last_element = elements[-1]
        text = last_element.inner_text()
        return text, last_element
    except Exception as e:
        print(f"回答の取得に失敗しました: {e}")
        return None, None

def extract_total_steps(text):
    """Geminiの回答から総ステップ数を抽出する"""
    if not text:
        return None
    
    # パターン1: "全部でN個のステップ"
    match = re.search(r'全部で(\d+)個のステップ', text)
    if match:
        return int(match.group(1))
    
    # パターン2: "ステップN" の最大値を探す
    matches = re.findall(r'ステップ(\d+)', text)
    if matches:
        return max(map(int, matches))
        
    return None

def extract_code_block(text):
    """テキストから最後のコードブロックまたはプロンプトを抽出する"""
    if not text:
        return None
    
    # パターン1: 【プロンプト】セクションから抽出
    # より確実な方法：【プロンプト】を見つけ、その後の「Markdown」を見つけ、
    # そこから次の大きなセクション（【ChatGPTからの回答例】または次の###/##）まで取得
    
    # まず【プロンプト】の位置を探す
    prompt_start = text.find('【プロンプト】')
    if prompt_start != -1:
        # 【プロンプト】以降のテキスト
        after_prompt = text[prompt_start:]
        
        # 「Markdown」または「markdown」の位置を探す
        markdown_pos = -1
        for marker in ['Markdown\n', 'markdown\n', 'Markdown\r\n', 'markdown\r\n']:
            pos = after_prompt.find(marker)
            if pos != -1:
                markdown_pos = pos + len(marker)
                break
        
        if markdown_pos != -1:
            # Markdown以降のテキスト
            prompt_content = after_prompt[markdown_pos:]
            
            # 終了位置を探す：【ChatGPTからの回答例】または次の大きなセクション
            end_markers = [
                '\n【ChatGPTからの回答例】',
                '\n\n### ',  # 次のステップ
                '\n\n## ',   # 次の大セクション
            ]
            
            end_pos = len(prompt_content)  # デフォルトは最後まで
            for marker in end_markers:
                pos = prompt_content.find(marker)
                if pos != -1 and pos < end_pos:
                    end_pos = pos
            
            extracted = prompt_content[:end_pos].strip()
            if extracted:
                return extracted
    
    # パターン2: 通常のコードブロック (```...```)
    matches = re.findall(r'```(?:.*?)?\n(.*?)```', text, re.DOTALL)
    if matches:
        return matches[-1].strip()
    
    return None

def run_phase(phase_name, source_page, target_page, prompt, source_selectors, target_selectors, flow_folder):
    print(f"\n=== フェーズ開始: {phase_name} ===")
    
    # 1. Copy Prompt
    pyperclip.copy(prompt)
    print(f"プロンプトをクリップボードにコピーしました。")
    
    # 2. Automate Paste (User must press Enter)
    print(f"ターゲットのタブに切り替えます...")
    target_page.bring_to_front()
    try:
        target_page.evaluate("window.focus()")
    except:
        pass
    
    try:
        target_page.click(target_selectors['input_area'])
        print("入力欄への貼り付けを試みています...")
        target_page.locator(target_selectors['input_area']).fill(prompt)
    except Exception as e:
        print(f"自動入力に失敗しました: {e}")
        print("手動でプロンプトを貼り付けてください (Ctrl+V)。")
    
    target_service = "Gemini" if "gemini" in str(target_page.url) else "ChatGPT"
    print(f"\n>>> アクションが必要です: 【{target_service}】 のブラウザで送信ボタン(Enter)を押してください <<<")
    print(">>> 回答が完了したら、このターミナルで Enter キーを押して進んでください <<<")
    input() 
    
    # 3. Extract Response
    print(f"回答を抽出しています...")
    response_text, response_element = get_latest_response(target_page, target_selectors['latest_response'])
    
    if response_text:
        print("回答の抽出に成功しました。")
        
        # Save text
        if "gemini" in str(target_page.url):
            filename = f"{flow_folder}/gemini_output/{phase_name}.txt"
        else:
            filename = f"{flow_folder}/chatgpt_output/{phase_name}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response_text)
        
        append_to_final_article(response_text, phase_name, flow_folder)
        
        # Save screenshot
        if response_element:
            screenshot_path = f"{flow_folder}/screenshots/{phase_name}.png"
            response_element.screenshot(path=screenshot_path)
    else:
        print("警告: 回答テキストを抽出できませんでした。")
        print("次のステップのために、回答テキストを手動で入力（貼り付け）してください（スキップする場合はそのままEnter）:")
        manual_input = input()
        if manual_input.strip():
            response_text = manual_input
        else:
            response_text = ""
        
    return response_text

def main():
    flow_folder = ensure_directories()
    print(f"\n=== 出力フォルダ: {flow_folder} ===")
    
    # User Input for Phase 1
    print("\n=== 初期設定 ===")
    problem_settings = input("『問題設定』を入力してください (または貼り付け): ")
    solution_hints = input("『解決手法のヒント』を入力してください (任意、スキップはEnter): ")
    
    with sync_playwright() as p:
        browser_config = config['browser_config']
        
        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars"
        ]

        # Launch Gemini Browser
        gemini_user_data = os.path.abspath(browser_config['gemini_user_data_dir'])
        print(f"Gemini ブラウザを起動中 (User Data: {gemini_user_data})...")
        context_gemini = p.chromium.launch_persistent_context(
            gemini_user_data,
            headless=browser_config['headless'],
            channel=browser_config.get('channel', 'chrome'),
            args=args,
            ignore_default_args=["--enable-automation"]
        )
        page_gemini = context_gemini.pages[0]
        page_gemini.goto(config['browser_config']['gemini_url'])

        # Launch ChatGPT Browser
        chatgpt_user_data = os.path.abspath(browser_config['chatgpt_user_data_dir'])
        print(f"ChatGPT ブラウザを起動中 (User Data: {chatgpt_user_data})...")
        context_chatgpt = p.chromium.launch_persistent_context(
            chatgpt_user_data,
            headless=browser_config['headless'],
            channel=browser_config.get('channel', 'chrome'),
            args=args,
            ignore_default_args=["--enable-automation"]
        )
        page_chatgpt = context_chatgpt.pages[0]
        page_chatgpt.goto(config['browser_config']['chatgpt_url'])
        
        print("\n--- 両方のサービスにログインしてください ---")
        print("準備ができたら、このターミナルで Enter キーを押してフローを開始してください。")
        input()
        
        gemini_sel = config['selectors']['gemini']
        chatgpt_sel = config['selectors']['chatgpt']
        prompts = config['prompts']
        
        # --- Phase 0: Format Definition ---
        # User -> Gemini
        run_phase("Phase_0_Format", None, page_gemini, prompts['phase_0'], None, gemini_sel, flow_folder)
        
        # --- Phase 1: Intro & Step 1 ---
        # User -> Gemini
        p1_prompt = prompts['phase_1'].replace("{problem_settings}", problem_settings).replace("{solution_hints}", solution_hints)
        gemini_resp_1 = run_phase("Phase_1_Intro_Step1", None, page_gemini, p1_prompt, None, gemini_sel, flow_folder)
        
        # --- Phase 2: Execute Step 1 ---
        # Gemini (Step 1 Prompt) -> ChatGPT
        print("\n=== フェーズ 2: ChatGPTでステップ1を実行 ===")
        step1_prompt = extract_code_block(gemini_resp_1)
        
        chatgpt_resp_1 = None
        max_retries = 3
        
        for attempt in range(max_retries):
            if step1_prompt:
                print(f"Geminiの回答からプロンプトを自動抽出しました。（試行 {attempt + 1}/{max_retries}）")
                try:
                    chatgpt_resp_1 = run_phase("Phase_2_Step1_Execution", page_gemini, page_chatgpt, step1_prompt, gemini_sel, chatgpt_sel, flow_folder)
                    if chatgpt_resp_1 and chatgpt_resp_1.strip():
                        print("ChatGPTからの回答取得に成功しました。")
                        break
                    else:
                        print(f"回答が空でした。再試行します...（{attempt + 1}/{max_retries}）")
                        time.sleep(2)
                except Exception as e:
                    print(f"エラーが発生しました: {e}")
                    if attempt < max_retries - 1:
                        print("再試行します...")
                        time.sleep(2)
            else:
                print(f"警告: プロンプトの自動抽出に失敗しました。（試行 {attempt + 1}/{max_retries}）")
                if attempt < max_retries - 1:
                    print("再度抽出を試みます...")
                    step1_prompt = extract_code_block(gemini_resp_1)
                    time.sleep(1)
        
        # 3回試行しても失敗した場合は手動フォールバック
        if not chatgpt_resp_1 or not chatgpt_resp_1.strip():
            print("\n自動実行に失敗しました。手動で実行してください。")
            print("1. Geminiのタブに移動します。")
            print("2. 『ステップ1のプロンプト』（コードブロック）をコピーしてください。")
            print("3. ChatGPTに貼り付けて実行してください。")
            print("4. ChatGPTの回答完了を待ってください。")
            print(">>> ChatGPTの回答が出たら、ここで Enter キーを押してください。 <<<")
            input()
            
            # Scrape ChatGPT response
            chatgpt_resp_1, _ = get_latest_response(page_chatgpt, chatgpt_sel['latest_response'])
            if chatgpt_resp_1:
                append_to_final_article(chatgpt_resp_1, "Phase_2_Step1_Result", flow_folder)
                with open(f"{flow_folder}/chatgpt_output/phase_2.txt", "w", encoding="utf-8") as f: 
                    f.write(chatgpt_resp_1)
            else:
                print("警告: ChatGPTの回答を自動取得できませんでした。")
                print("次のステップのために、回答テキストを手動で入力（貼り付け）してください:")
                chatgpt_resp_1 = input()

        # --- Determine Loop Count ---
        print("\n=== 設定確認 ===")
        extracted_steps = extract_total_steps(gemini_resp_1)
        if extracted_steps:
            print(f"Geminiの回答から総ステップ数を検出しました: {extracted_steps}")
            total_steps = extracted_steps
        else:
            try:
                total_steps = int(input("総ステップ数を自動検出できませんでした。Geminiが決めたステップ数を入力してください (例: 3): "))
            except:
                total_steps = 3
        
        loop_count = max(0, total_steps - 2)
        previous_chatgpt_response = chatgpt_resp_1
        
        # --- Phase 3: Loop ---
        for i in range(loop_count):
            step_num = i + 2
            print(f"\n=== フェーズ 3: 中間ステップ {step_num} ===")
            
            # Gemini writes next prompt
            if not previous_chatgpt_response:
                 previous_chatgpt_response = "（前のステップの回答が取得できませんでした）"

            p3_prompt = prompts['phase_3_loop'].replace("{previous_response}", previous_chatgpt_response)
            gemini_resp_loop = run_phase(f"Phase_3_Step{step_num}_Plan", page_chatgpt, page_gemini, p3_prompt, chatgpt_sel, gemini_sel, flow_folder)
            
            # User executes in ChatGPT
            print(f"\n=== ChatGPTでステップ {step_num} を実行 ===")
            step_loop_prompt = extract_code_block(gemini_resp_loop)
            
            chatgpt_resp_loop = None
            max_retries = 3
            
            for attempt in range(max_retries):
                if step_loop_prompt:
                    print(f"Geminiの回答からプロンプトを自動抽出しました。（試行 {attempt + 1}/{max_retries}）")
                    try:
                        chatgpt_resp_loop = run_phase(f"Phase_3_Step{step_num}_Execution", page_gemini, page_chatgpt, step_loop_prompt, gemini_sel, chatgpt_sel, flow_folder)
                        if chatgpt_resp_loop and chatgpt_resp_loop.strip():
                            print("ChatGPTからの回答取得に成功しました。")
                            previous_chatgpt_response = chatgpt_resp_loop
                            break
                        else:
                            print(f"回答が空でした。再試行します...（{attempt + 1}/{max_retries}）")
                            time.sleep(2)
                    except Exception as e:
                        print(f"エラーが発生しました: {e}")
                        if attempt < max_retries - 1:
                            print("再試行します...")
                            time.sleep(2)
                else:
                    print(f"警告: プロンプトの自動抽出に失敗しました。（試行 {attempt + 1}/{max_retries}）")
                    if attempt < max_retries - 1:
                        print("再度抽出を試みます...")
                        step_loop_prompt = extract_code_block(gemini_resp_loop)
                        time.sleep(1)
            
            # 3回試行しても失敗した場合は手動フォールバック
            if not chatgpt_resp_loop or not chatgpt_resp_loop.strip():
                print("\n自動実行に失敗しました。手動で実行してください。")
                print(f"1. Geminiから『ステップ {step_num} のプロンプト』をコピーしてください。")
                print("2. ChatGPTに貼り付けて実行してください。")
                print(">>> ChatGPTの回答が出たら、ここで Enter キーを押してください。 <<<")
                input()
                
                # Scrape ChatGPT
                chatgpt_resp_loop, _ = get_latest_response(page_chatgpt, chatgpt_sel['latest_response'])
                if chatgpt_resp_loop:
                    append_to_final_article(chatgpt_resp_loop, f"Phase_3_Step{step_num}_Result", flow_folder)
                    previous_chatgpt_response = chatgpt_resp_loop
                else:
                    print("警告: ChatGPTの回答を自動取得できませんでした。")
                    print("次のステップのために、回答テキストを手動で入力（貼り付け）してください:")
                    previous_chatgpt_response = input()

        
        # --- Phase 4: Last Step Plan ---
        print("\n=== フェーズ 4: ラストステップの計画 ===")
        if not previous_chatgpt_response:
             previous_chatgpt_response = "（前のステップの回答が取得できませんでした）"
             
        p4_prompt = prompts['phase_4_last'].replace("{previous_response}", previous_chatgpt_response)
        gemini_resp_last = run_phase("Phase_4_LastStep_Plan", page_chatgpt, page_gemini, p4_prompt, chatgpt_sel, gemini_sel, flow_folder)
        
        # --- Phase 5: Execute Last Step ---
        print("\n=== フェーズ 5: ChatGPTでラストステップを実行 ===")
        last_step_prompt = extract_code_block(gemini_resp_last)
        
        chatgpt_resp_last = None
        max_retries = 3
        
        for attempt in range(max_retries):
            if last_step_prompt:
                print(f"Geminiの回答からプロンプトを自動抽出しました。（試行 {attempt + 1}/{max_retries}）")
                try:
                    chatgpt_resp_last = run_phase("Phase_5_LastStep_Execution", page_gemini, page_chatgpt, last_step_prompt, gemini_sel, chatgpt_sel, flow_folder)
                    if chatgpt_resp_last and chatgpt_resp_last.strip():
                        print("ChatGPTからの回答取得に成功しました。")
                        break
                    else:
                        print(f"回答が空でした。再試行します...（{attempt + 1}/{max_retries}）")
                        time.sleep(2)
                except Exception as e:
                    print(f"エラーが発生しました: {e}")
                    if attempt < max_retries - 1:
                        print("再試行します...")
                        time.sleep(2)
            else:
                print(f"警告: プロンプトの自動抽出に失敗しました。（試行 {attempt + 1}/{max_retries}）")
                if attempt < max_retries - 1:
                    print("再度抽出を試みます...")
                    last_step_prompt = extract_code_block(gemini_resp_last)
                    time.sleep(1)
        
        # 3回試行しても失敗した場合は手動フォールバック
        if not chatgpt_resp_last or not chatgpt_resp_last.strip():
            print("\n自動実行に失敗しました。手動で実行してください。")
            print("1. Geminiから『ラストステップのプロンプト』をコピーしてください。")
            print("2. ChatGPTに貼り付けて実行してください。")
            print(">>> ChatGPTの回答が出たら、ここで Enter キーを押してください。 <<<")
            input()
            
            chatgpt_resp_last, _ = get_latest_response(page_chatgpt, chatgpt_sel['latest_response'])
            if chatgpt_resp_last:
                append_to_final_article(chatgpt_resp_last, "Phase_5_LastStep_Result", flow_folder)
            else:
                print("警告: ChatGPTの回答を自動取得できませんでした。")
                print("次のステップのために、回答テキストを手動で入力（貼り付け）してください:")
                chatgpt_resp_last = input()
        
        # --- Phase 6: Summary ---
        print("\n=== フェーズ 6: まとめ ===")
        if not chatgpt_resp_last:
             chatgpt_resp_last = "（前のステップの回答が取得できませんでした）"

        p6_prompt = prompts['phase_6_summary'].replace("{previous_response}", chatgpt_resp_last)
        run_phase("Phase_6_Summary", page_chatgpt, page_gemini, p6_prompt, chatgpt_sel, gemini_sel, flow_folder)
        
        print("\n=== フロー完了 ===")
        print(f"すべての成果物は以下に保存されました: {os.path.abspath(flow_folder)}")

if __name__ == "__main__":
    main()
