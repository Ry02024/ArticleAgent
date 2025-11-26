import os
import re
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv()

def main():
    # Check for API keys
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("GOOGLE_API_KEY"):
        print("Error: API keys not found. Please set OPENAI_API_KEY and GOOGLE_API_KEY in .env file.")
        print("You can copy .env.example to .env and fill in your keys.")
        return

    # Initialize Models
    # Writer: Gemini 2.5 Pro (using langchain-google-genai)
    writer_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        temperature=0.7,
        max_output_tokens=4096
    )

    # Simulator: GPT-4o (using langchain-openai)
    simulator_llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        request_timeout=60  # Add 60s timeout
    )

    topic = "単純なミス（ケアレスミス）を繰り返す"
    print(f"Generating article for topic: {topic}")

    article_content = []
    
    # Read format.md
    try:
        with open("format.md", "r", encoding="utf-8") as f:
            format_content = f.read()
    except FileNotFoundError:
        print("Error: format.md not found.")
        return

    # --- Step 1: Initial Writer Call ---
    print("\n--- Step 1: Writer is creating the introduction and first prompt ---")
    
    writer_system_prompt = f"""
    あなたは「ChatGPT活用記事」の執筆者（Writer）です。
    指定されたテーマについて、読者が実践できるステップバイステップの記事を書いてください。
    
    【重要】以下のフォーマット（format.mdの内容）に厳密に従って記事を構成してください。
    
    --- format.md 開始 ---
    {format_content}
    --- format.md 終了 ---
    
    あなたの役割は以下の2つです：
    1. 記事の解説文を書く（導入、理由、解決策の提示など）。
    2. 読者が実際にChatGPTに入力すべき「プロンプト」を作成する。
    
    出力フォーマットは厳密に以下を守ってください：
    
    <article>
    (ここに記事の本文を書く。Markdown形式で見出しや本文を構成する)
    </article>
    
    <prompt>
    (ここにChatGPTに入力させるプロンプトの内容だけを書く)
    </prompt>
    
    もし記事が完結し、これ以上プロンプトが必要ない場合は、<prompt>タグの代わりに <finished> と書いてください。
    """

    writer_prompt_template = ChatPromptTemplate.from_messages([
        ("system", writer_system_prompt),
        ("user", "{input}")
    ])
    
    writer_chain = writer_prompt_template | writer_llm | StrOutputParser()

    # Initial input
    current_input = f"テーマ：「{topic}」。\nまずは導入部分と、最初のステップ（原因の特定など）の解説、そしてそのためのプロンプトを書いてください。"
    
    step_count = 1
    max_steps = 5
    
    while step_count <= max_steps:
        print(f"Processing Step {step_count}...")
        
        # Call Writer
        try:
            writer_response = writer_chain.invoke({"input": current_input})
        except Exception as e:
            print(f"Error calling Writer: {e}")
            break
        
        # Parse Writer Output
        article_part = extract_tag_content(writer_response, "article")
        prompt_part = extract_tag_content(writer_response, "prompt")
        is_finished = "<finished>" in writer_response
        
        if article_part:
            article_content.append(article_part)
            print(f"Writer generated content ({len(article_part)} chars).")
        
        if is_finished:
            print("Writer indicated the article is finished.")
            break
            
        if prompt_part:
            print(f"Writer generated prompt: {prompt_part[:50]}...")
            
            # --- Step 2: Simulator Call ---
            print("--- Simulator (ChatGPT) is generating a response ---")
            try:
                simulator_response = simulator_llm.invoke(prompt_part).content
                print(f"Simulator responded ({len(simulator_response)} chars).")
            except Exception as e:
                print(f"Error calling Simulator: {e}")
                # Fallback or break? Let's break for now to see the error.
                break
            
            # Prepare input for next Writer iteration
            current_input = f"""
            前回の続きをお願いします。
            
            あなたが作成したプロンプトに対して、ChatGPT（Simulator）は以下の回答をしました：
            
            --- ChatGPTの回答開始 ---
            {simulator_response}
            --- ChatGPTの回答終了 ---
            
            この回答を記事内の「実行結果例」として引用・解説し、
            次のステップ（もしあれば）の解説と、次のプロンプトを書いてください。
            記事をまとめる段階であれば、まとめを書いて <finished> タグを出力してください。
            """
            
            # Append the simulator response to the article content (formatted)
            # We let the Writer decide how to include it, or we can force append it.
            # In this flow, we pass it to the Writer and ask the Writer to include it in the next <article> block.
            # However, usually it's better to let the Writer weave it in.
            
        else:
            print("No prompt found and not finished. Stopping loop to prevent error.")
            break
            
        step_count += 1

    # Save Final Article
    final_markdown = "\n\n".join(article_content)
    filename = "generated_article.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_markdown)
        
    print(f"\nSuccessfully generated article: {filename}")

def extract_tag_content(text, tag_name):
    """Extracts content between <tag> and </tag>."""
    pattern = f"<{tag_name}>(.*?)</{tag_name}>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

if __name__ == "__main__":
    main()
