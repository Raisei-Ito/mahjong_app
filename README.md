# 麻雀スコア管理アプリ

麻雀の1半荘ごとの収支とチップを記録・共有するWebアプリです。

## 機能

- 部屋作成（6桁の英数字コード）
- プレイヤー登録（4名）
- スコア入力（持ち点とチップ増減）
- 自動計算（ウマ・オカを考慮したポイント）
- リアルタイム更新（HTMXで5秒ごとに自動更新）
- サシウマ設定
- レート設定（ノーレート、テンイチ、テンニ、テンサン、テンゴ、テンピン、テンリャンピン、ウーピン、デカピン）

## デプロイ方法

### Renderでのデプロイ（推奨）

1. **GitHubにリポジトリを作成**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/mahjong_app.git
   git push -u origin main
   ```

2. **Renderでアプリを作成**
   - [Render](https://render.com)にアクセスしてアカウント作成
   - "New +" → "Web Service" を選択
   - GitHubリポジトリを接続
   - 以下の設定を行う：
     - **Name**: mahjong-app（任意）
     - **Environment**: Python 3
     - **Build Command**: `chmod +x build.sh && ./build.sh`
     - **Start Command**: `gunicorn mahjong_project.wsgi`
     - **Plan**: Free（無料プラン）

3. **環境変数を設定**
   Renderのダッシュボードで以下を設定：
   - `SECRET_KEY`: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` で生成
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `your-app-name.onrender.com`（Renderが自動で設定）

4. **デプロイ**
   - "Create Web Service" をクリック
   - デプロイが完了するまで待つ（5-10分）

### Railwayでのデプロイ

1. **GitHubにリポジトリを作成**（上記と同じ）

2. **Railwayでアプリを作成**
   - [Railway](https://railway.app)にアクセスしてアカウント作成
   - "New Project" → "Deploy from GitHub repo" を選択
   - リポジトリを選択

3. **環境変数を設定**
   - Variables タブで以下を設定：
     - `SECRET_KEY`: ランダムな文字列
     - `DEBUG`: `False`
     - `ALLOWED_HOSTS`: `*.railway.app`

4. **デプロイ**
   - 自動的にデプロイが開始されます

### ローカル開発

```bash
# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# マイグレーション
python manage.py migrate

# サーバー起動
python manage.py runserver
```

## 技術スタック

- Backend: Python / Django
- Frontend: Django Template + Bootstrap 5
- 通信: HTMX
- データベース: SQLite（本番環境ではPostgreSQL推奨）

## ライセンス

MIT

