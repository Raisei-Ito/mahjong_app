# アーキテクチャドキュメント

## 概要

このドキュメントでは、麻雀スコア管理アプリケーションのアーキテクチャと設計思想について説明します。

## システムアーキテクチャ

### 全体構成

```
┌─────────────┐
│   Client    │ (ブラウザ)
│  (HTMX)     │
└──────┬──────┘
       │ HTTP/HTTPS
       ▼
┌─────────────┐
│   Django    │ (WSGI Application)
│  (Gunicorn) │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  SQLite     │ (データベース)
└─────────────┘
```

## データモデル設計

### エンティティ関係図

```
Room (部屋)
  ├── code: 6桁の英数字コード（一意）
  ├── rate_type: レート設定
  ├── sashi_uma_type: サシウマタイプ
  ├── starting_points: 持ち点
  ├── return_points: 返し点
  └── chip_point_rate: チップ換算率
      │
      ├── Player (プレイヤー) [1:N]
      │   ├── name: プレイヤー名
      │   └── order: 順番 (1-4)
      │       │
      │       └── ScoreRecord (スコア記録) [1:N]
      │           ├── score: 持ち点
      │           ├── chip_change: チップ増減
      │           ├── rank: 順位
      │           └── points: 計算されたポイント
      │
      └── Game (半荘) [1:N]
          ├── game_number: ゲーム番号
          └── ScoreRecord (スコア記録) [1:N]
```

### モデルの責務

#### Room（部屋モデル）

- **責務**: 対戦部屋の設定とスコア計算の基本情報を管理
- **主要プロパティ**:
  - `uma_1st`, `uma_2nd`, `uma_3rd`, `uma_4th`: サシウマから計算されるウマ値
  - `oka_points`: 返し点と持ち点の差から計算されるオカポイント
- **設計思想**: ビジネスロジック（スコア計算）をプロパティメソッドに集約

#### Player（プレイヤーモデル）

- **責務**: 部屋に参加するプレイヤー情報を管理
- **制約**: 1つの部屋に最大4名まで

#### Game（半荘モデル）

- **責務**: 1回の半荘ゲームを表現
- **特徴**: 部屋ごとにゲーム番号が自動採番される

#### ScoreRecord（スコア記録モデル）

- **責務**: 各プレイヤーのスコアとチップ増減を記録
- **計算**: ビュー関数でウマ・オカを考慮したポイントを計算して保存

## ビュー層の設計

### URLルーティング

```
/                           → index (部屋作成)
/room/<code>/               → dashboard (ダッシュボード)
/room/<code>/setup/         → room_setup (プレイヤー登録)
/room/<code>/settings/      → room_settings (部屋設定)
/room/<code>/record/        → record_score (スコア記録)
/room/<code>/partials/game-list/ → game_list_partial (HTMX用)
/room/<code>/partials/player-stats/ → player_stats_partial (HTMX用)
```

### ビュー関数の責務

- **index**: 部屋作成フォームの表示と処理
- **dashboard**: ゲーム履歴と累計成績の表示
- **room_setup**: プレイヤー登録
- **room_settings**: 部屋設定（レート、サシウマ、チップ換算率など）
- **record_score**: スコア記録の入力と保存
- **game_list_partial**: HTMX用のゲーム履歴パーシャル
- **player_stats_partial**: HTMX用のプレイヤー統計パーシャル

### トランザクション管理

スコア記録時は`transaction.atomic()`を使用してデータ整合性を保証：

```python
@transaction.atomic
def record_score(request, code):
    # スコア記録処理
    # エラー時は自動ロールバック
```

## フロントエンド設計

### HTMXによる非同期更新

- **自動更新間隔**: 3分ごと
- **更新対象**: ゲーム履歴リスト、プレイヤー統計
- **実装**: `hx-trigger="every 3m"`属性を使用

### レスポンシブデザイン

- **フレームワーク**: Bootstrap 5
- **対応デバイス**: デスクトップ、タブレット、スマートフォン

## セキュリティ設計

### 認証・認可

- 現在は認証機能なし（部屋コードでアクセス制御）
- 将来的な拡張: Django認証システムの統合

### セキュリティ対策

- **CSRF保護**: Django標準のCSRFミドルウェア
- **XSS対策**: テンプレートエスケープ
- **SQLインジェクション対策**: Django ORM使用
- **セキュアなCookie**: 本番環境で有効化

## パフォーマンス最適化

### データベース

- **インデックス**: 外部キーに自動インデックス
- **クエリ最適化**: `select_related()`、`prefetch_related()`の使用
- **WALモード**: SQLiteのWALモードを有効化（マルチプロセス対応）

### 静的ファイル

- **WhiteNoise**: 本番環境での静的ファイル配信
- **圧縮**: 静的ファイルの圧縮とキャッシュ

## デプロイメント

### デプロイプラットフォーム: Render

- **プラットフォーム**: Render
- **ビルドコマンド**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- **起動コマンド**: `gunicorn mahjong_project.wsgi:application`
- **Pythonバージョン**: 3.11

### Render設定

- **自動デプロイ**: GitHubと連携して自動デプロイ
- **SSL証明書**: 自動発行・更新
- **静的ファイル**: WhiteNoiseを使用して配信
- **データベース**: SQLite（小規模運用に適している）
- **ビルド環境**: Renderが自動的にPython環境を構築

## 今後の拡張予定

1. **認証機能**: ユーザー登録・ログイン機能
2. **API**: RESTful APIの提供
3. **リアルタイム通信**: WebSocketによるリアルタイム更新
4. **統計機能**: より詳細な統計分析
5. **データベース**: ユーザー数が増加した場合のPostgreSQLへの移行

## 参考資料

- [Django公式ドキュメント](https://docs.djangoproject.com/)
- [HTMX公式ドキュメント](https://htmx.org/)
- [Bootstrap 5公式ドキュメント](https://getbootstrap.com/docs/5.0/)

