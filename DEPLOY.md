# デプロイ手順ガイド

## ステップ1: GitHubにコードをプッシュ

### 1-1. ファイルをGitに追加

```bash
cd /Users/raisei-ito/mahjong_app
git add .
```

### 1-2. 初回コミット

```bash
git commit -m "Initial commit: 麻雀スコア管理アプリ"
```

### 1-3. GitHubでリポジトリを作成

1. [GitHub](https://github.com)にログイン
2. 右上の「+」→「New repository」をクリック
3. リポジトリ名を入力（例: `mahjong_app`）
4. **Public**または**Private**を選択
5. 「Initialize this repository with a README」は**チェックしない**
6. 「Create repository」をクリック

### 1-4. リモートリポジトリを追加してプッシュ

```bash
# リモートリポジトリを追加（YOUR_USERNAMEをあなたのGitHubユーザー名に置き換え）
git remote add origin https://github.com/YOUR_USERNAME/mahjong_app.git

# ブランチ名をmainに変更（必要に応じて）
git branch -M main

# コードをプッシュ
git push -u origin main
```

## ステップ2: Renderでアプリを作成

### 2-1. Renderアカウント作成

1. [Render](https://render.com)にアクセス
2. 「Get Started for Free」をクリック
3. GitHubアカウントでログイン（推奨）

### 2-2. Web Serviceを作成

1. ダッシュボードで「New +」→「Web Service」をクリック
2. GitHubリポジトリを選択（先ほど作成したリポジトリ）
3. 以下の設定を入力：

   - **Name**: `mahjong-app`（任意）
   - **Environment**: `Python 3`
   - **Region**: `Singapore`（日本に近い）
   - **Branch**: `main`
   - **Root Directory**: （空欄のまま）
   - **Build Command**: `chmod +x build.sh && ./build.sh`
   - **Start Command**: `gunicorn mahjong_project.wsgi`
   - **Plan**: `Free`

### 2-3. 環境変数を設定

「Environment」セクションで以下を追加：

1. **SECRET_KEY**を生成して設定：
   ```bash
   # ローカルで実行して生成
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   生成された文字列を`SECRET_KEY`環境変数に設定

2. **DEBUG**: `False`

3. **ALLOWED_HOSTS**: Renderが自動で設定（手動設定不要）

### 2-4. デプロイ開始

「Create Web Service」をクリックしてデプロイを開始

## ステップ3: デプロイの確認

1. デプロイが完了するまで待つ（5-10分）
2. ログを確認してエラーがないか確認
3. 表示されたURL（例: `https://mahjong-app.onrender.com`）にアクセス
4. アプリが正常に動作するか確認

## トラブルシューティング

### デプロイが失敗する場合

1. **ログを確認**
   - Renderのダッシュボードで「Logs」タブを確認
   - エラーメッセージを確認

2. **よくある問題**
   - `SECRET_KEY`が設定されていない → 環境変数を確認
   - `ALLOWED_HOSTS`エラー → 環境変数を確認
   - 静的ファイルのエラー → `collectstatic`が実行されているか確認

3. **再デプロイ**
   - コードを修正してGitHubにプッシュすると自動で再デプロイされます

### 静的ファイルが表示されない場合

1. `build.sh`が実行されているか確認
2. `STATIC_ROOT`が正しく設定されているか確認
3. WhiteNoiseが正しく設定されているか確認

## 次のステップ

デプロイが成功したら：

1. 友達にURLを共有
2. 部屋を作成してテスト
3. 必要に応じてカスタムドメインを設定

## 注意事項

- **無料プラン**: 15分間アクセスがないとスリープします（初回アクセス時に起動）
- **データベース**: SQLiteを使用（本番環境ではPostgreSQL推奨）
- **バックアップ**: 定期的にデータベースをバックアップすることを推奨

