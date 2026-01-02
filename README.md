# 麻雀スコア管理アプリ

麻雀の1半荘ごとの収支とチップを記録・共有するWebアプリケーションです。4人で行う麻雀の対戦結果をリアルタイムで共有し、自動計算機能により正確な収支を管理できます。

## 主な機能

- **部屋作成**: 6桁の英数字コードで部屋を作成
- **プレイヤー登録**: 4名のプレイヤーを登録
- **スコア入力**: 持ち点とチップ増減を記録
- **自動計算**: ウマ・オカを考慮したポイントを自動計算
- **リアルタイム更新**: HTMXで3分ごとに自動更新（複数人で同時使用可能）
- **サシウマ設定**: 5-10、10-20、10-30、カスタムから選択可能
- **レート設定**: ノーレート、テンイチ、テンニ、テンサン、テンゴ、テンピン、テンリャンピン、ウーピン、デカピンに対応

## 技術スタック

### バックエンド
- **Python 3.11**
- **Django 5.2+**: MVTアーキテクチャ、ORM、マイグレーション
- **SQLite**: データベース（小規模運用に適している）

### フロントエンド
- **Django Templates**: サーバーサイドレンダリング
- **Bootstrap 5**: レスポンシブデザイン
- **HTMX**: 非同期通信によるリアルタイム更新

### インフラ
- **Render**: デプロイプラットフォーム
- **Gunicorn**: WSGIサーバー
- **WhiteNoise**: 静的ファイル配信

## プロジェクト構造

```
mahjong_app/
├── mahjong/                    # メインアプリケーション
│   ├── models.py              # データモデル（Room, Player, Game, ScoreRecord）
│   ├── views.py               # ビュー関数
│   ├── urls.py                # URLルーティング
│   ├── templates/             # HTMLテンプレート
│   │   └── mahjong/
│   │       ├── base.html
│   │       ├── index.html
│   │       ├── dashboard.html
│   │       └── partials/      # パーシャルテンプレート
│   ├── templatetags/          # カスタムテンプレートタグ
│   └── management/            # カスタム管理コマンド
│       └── commands/
│           └── cleanup_old_rooms.py
├── mahjong_project/           # Djangoプロジェクト設定
│   ├── settings.py            # 設定ファイル
│   ├── urls.py                # ルートURL設定
│   ├── wsgi.py                # WSGI設定
│   └── asgi.py                # ASGI設定
├── requirements.txt           # Python依存関係
├── render.yaml                # Render設定ファイル（オプション）
├── .gitignore                 # Git除外設定
└── README.md                  # このファイル
```

## セットアップ

### 前提条件

- Python 3.11以上
- pip

### ローカル開発環境のセットアップ

1. **リポジトリをクローン**
   ```bash
   git clone https://github.com/[ユーザー名]/mahjong_app.git
   cd mahjong_app
   ```

2. **仮想環境を作成して有効化**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **依存関係をインストール**
   ```bash
   pip install -r requirements.txt
   ```

4. **環境変数を設定**
   ```bash
   # .envファイルを作成（.env.exampleを参考に）
   cp .env.example .env
   # .envファイルを編集してSECRET_KEYなどを設定
   ```

5. **データベースマイグレーション**
   ```bash
   python manage.py migrate
   ```

6. **開発サーバーを起動**
   ```bash
   python manage.py runserver
   ```

   ブラウザで `http://127.0.0.1:8000` にアクセス

### 本番環境へのデプロイ

#### Renderでのデプロイ

**Renderの利点：**
- ✅ **シンプルなデプロイ** - GitHubと連携して自動デプロイ
- ✅ **無料プランあり** - 個人利用なら十分なリソース
- ✅ **自動SSL** - HTTPS証明書を自動発行・更新
- ✅ **環境変数管理** - ダッシュボードで簡単に設定

1. **Renderアカウントを作成**
   - [Render](https://render.com)にアクセスしてアカウントを作成
   - GitHubアカウントと連携

2. **新しいWebサービスを作成**
   - Renderダッシュボードで「New +」→「Web Service」を選択
   - GitHubリポジトリを接続

3. **ビルド設定**
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn mahjong_project.wsgi:application`
   - **Environment**: Python 3
   
   **または、`render.yaml`ファイルを使用**
   - リポジトリに`render.yaml`が含まれている場合、Renderが自動的に設定を読み込みます
   - 必要に応じて`render.yaml`内の`your-app-name.onrender.com`を実際のアプリ名に変更してください

4. **環境変数を設定**
   Renderダッシュボードの「Environment」セクションで以下を設定：
   ```
   SECRET_KEY=生成されたSECRET_KEY
   DEBUG=False
   ALLOWED_HOSTS=your-app-name.onrender.com
   CSRF_TRUSTED_ORIGINS=https://your-app-name.onrender.com
   ```
   
   SECRET_KEYの生成方法：
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

5. **デプロイ**
   - 設定を保存すると自動的にデプロイが開始されます
   - 初回デプロイ時はマイグレーションが自動実行されます

**注意事項：**
- 無料プランでは、15分間アクセスがないとスリープします（次回アクセス時に自動起動）
- 本番環境では必ず`DEBUG=False`に設定してください
- 本アプリはSQLiteを使用しています。ユーザー数が少ない小規模運用に適しており、追加のデータベース設定は不要です

## アーキテクチャの特徴

### データモデル設計

- **Room（部屋）**: 対戦部屋の設定（レート、サシウマ、チップ換算率など）
- **Player（プレイヤー）**: 部屋に参加するプレイヤー情報
- **Game（半荘）**: 1回の半荘ゲーム
- **ScoreRecord（スコア記録）**: 各プレイヤーのスコアとチップ増減

### ビジネスロジック

麻雀の複雑なスコア計算（素点、ウマ、オカ、チップ換算）をモデルのプロパティメソッドに集約し、ビュー関数をシンプルに保つ設計を採用しています。

### セキュリティ

- CSRF保護
- セキュアなCookie設定
- 環境変数による機密情報の管理
- SQLインジェクション対策（Django ORM）

## 開発

### カスタム管理コマンド

古い部屋を自動削除するコマンド：
```bash
python manage.py cleanup_old_rooms
```

### テスト

```bash
python manage.py test
```

## ライセンス

MIT License

## 作者

[あなたの名前]

## 関連リンク

- [ポートフォリオ詳細](PORTFOLIO.md)
- [アーキテクチャドキュメント](ARCHITECTURE.md)

