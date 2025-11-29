# ChatGPT記事自動生成エージェント (Article Generator Agent)

**Writer (Gemini)** と **Simulator (ChatGPT)** という2つのAIが連携し、実践的な「ChatGPT活用ガイド記事」を自動で執筆するツールです。

Writerが記事の構成とプロンプトを考え、Simulatorがそのプロンプトを実際に実行して回答を生成します。これにより、「やってみた」形式の説得力ある記事が完成します。

## ✨ 特徴

*   **ブラウザ半自動執筆**: GeminiとChatGPTのブラウザを自動制御し、記事を生成
*   **実演付き**: 実際にChatGPTを動かした「生の回答ログ」が記事に含まれます
*   **構成カスタマイズ**: `config.json` を編集することで、記事のテンプレートを自由に変更可能
*   **タイムスタンプ管理**: 各実行結果を日時付きフォルダで整理

## 📁 プロジェクト構成

```
article-agent/
├── human_assisted_flow/      # ブラウザ半自動モード
│   ├── main.py               # ブラウザ自動化スクリプト
│   ├── config.json           # フェーズ設定・セレクタ定義
│   ├── README.md             # 詳細な使用方法
│   └── output/               # 実行結果（タイムスタンプ付き）
│       └── flow_YYYYMMDD_HHMMSS/
│           ├── final_article.md
│           ├── gemini_output/
│           ├── chatgpt_output/
│           └── screenshots/
└── requirements.txt          # 依存ライブラリ
```

## 🚀 セットアップ

**必要なライブラリのインストール**:

```powershell
pip install playwright pyperclip
playwright install chromium
```

## 📝 使い方

### ブラウザ半自動モード

ブラウザを使用して記事を生成します。

```powershell
cd human_assisted_flow
python main.py
```

**実行の流れ**:
1. 2つのブラウザタブ（Gemini/ChatGPT）が自動で開きます
2. 初回実行時は手動でログインしてください
3. プロンプトは自動で貼り付けられます
4. **あなたがEnterキーを押して送信**します（ToS準拠）
5. 回答が完了したら、ターミナルでEnterキーを押して次のステップへ
6. 結果は `output/flow_YYYYMMDD_HHMMSS/` に保存されます

詳細は [`human_assisted_flow/README.md`](human_assisted_flow/README.md) を参照してください。

### 記事の構成を変える

`human_assisted_flow/config.json` ファイルを編集することで、記事の見出しや流れを指示できます。

## 💡 実用例

このツールは以下のような記事作成に適しています。

### 例1：業務効率化ガイド
*   **テーマ**: 「単純なミス（ケアレスミス）を繰り返す」
*   **生成される内容**:
    *   なぜミスが起きるのかの認知科学的な解説
    *   ChatGPTに「ミスの傾向」を分析させるプロンプト
    *   実際の分析結果と、それに基づいたチェックリスト作成手順

### 例2：スキル習得・学習
*   **テーマ**: 「Pythonでスクレイピングを独学する」
*   **生成される内容**:
    *   初心者が躓きやすいポイントの解説
    *   ChatGPTに「学習カリキュラム」を作らせるプロンプト
    *   エラーが出たときのChatGPTへの質問の仕方（実演付き）

### 例3：クリエイティブ作業
*   **テーマ**: 「魅力的なキャッチコピーを量産する」
*   **生成される内容**:
    *   ターゲット分析のフレームワーク解説
    *   ChatGPTに「ペルソナ」を設定して案を出させるプロンプト
    *   出てきた案をブラッシュアップする対話の実例

## ⚙️ 技術仕様

- **Writer LLM**: Google Gemini (Gemini 3.0 Pro推奨) - 記事構成・プロンプト生成
- **Simulator LLM**: OpenAI ChatGPT (ChatGPT 5.1推奨) - プロンプト実行・回答生成
- **ブラウザ自動化**: Playwright
- **出力形式**: Markdown

> **注**: 使用するモデルはブラウザ上で選択できます。Gemini 3.0 ProとChatGPT 5.1の組み合わせを推奨します。

## ⚠️ トラブルシューティング

*   **プロンプトが貼り付けられない**: `Ctrl+V` で手動貼り付けしてください
*   **セレクタエラー**: ChatGPT/GeminiのUI変更により、`config.json` のセレクタ更新が必要な場合があります
*   **ログイン要求**: 初回実行時は手動でログインが必要です（`user_data_gemini` / `user_data_chatgpt` ディレクトリに保存されます）
*   **回答が抽出できない**: 手動で回答をコピー＆ペーストできます（プロンプトが表示されます）

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 貢献

バグ報告や機能提案は、GitHubのIssuesでお願いします。
