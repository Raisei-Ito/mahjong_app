# デプロイメントガイド

## 24時間使用されていない部屋の自動削除

24時間使用されていない部屋を自動削除する機能を実装しました。

### 設定方法

Fly.ioでcron jobを設定するには、以下のコマンドを実行してください：

```bash
flyctl cron schedule "0 18 * * *" --command "python manage.py cleanup_old_rooms" --app mahjong-app
```

このコマンドは、毎日UTC 18:00（JST 03:00）に`cleanup_old_rooms`コマンドを実行します。

### 手動実行

管理コマンドを手動で実行する場合：

```bash
# 削除対象を確認（削除はしない）
flyctl ssh console --app mahjong-app -C "python manage.py cleanup_old_rooms --dry-run"

# 実際に削除を実行
flyctl ssh console --app mahjong-app -C "python manage.py cleanup_old_rooms"
```

### ローカルでのテスト

```bash
# 削除対象を確認
python manage.py cleanup_old_rooms --dry-run

# 実際に削除を実行
python manage.py cleanup_old_rooms
```

