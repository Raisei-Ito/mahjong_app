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

### Fly.ioでのデプロイ（推奨）⭐

**Fly.ioの利点：**
- ✅ **スリープしない** - 無料プランでも常時起動（待ち時間なし）
- ✅ **高速な起動** - グローバルなエッジネットワーク
- ✅ **シンプルなデプロイ** - `flyctl`コマンド一つでデプロイ
- ✅ **無料プランあり** - 月3台の共有CPU VM（個人利用なら十分）
- ✅ **Dockerベース** - 柔軟な設定が可能

1. **Fly.io CLIをインストール**
   ```bash
   # macOS (Homebrew)
   brew install flyctl
   
   # またはインストールスクリプト
   curl -L https://fly.io/install.sh | sh
   ```

2. **Fly.ioにログイン**
   ```bash
   flyctl auth login
   ```

3. **アプリを作成**
   ```bash
   cd /Users/raisei-ito/mahjong_app
   flyctl launch --name mahjong-app --region nrt
   ```

4. **環境変数を設定**
   ```bash
   # SECRET_KEYを生成
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   
   # 環境変数を設定
   flyctl secrets set SECRET_KEY="生成されたSECRET_KEY"
   flyctl secrets set DEBUG="False"
   flyctl secrets set ALLOWED_HOSTS="*.fly.dev"
   ```

5. **デプロイ**
   ```bash
   flyctl deploy
   ```

詳細は`FLY_DEPLOY.md`を参照してください。

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

