# デプロイメントガイド

## 24時間使用されていない部屋の自動削除

**注意: 自動削除機能は現在無効化されています。**

24時間使用されていない部屋を自動削除する機能は実装されていますが、現在は無効化されています。
必要に応じて、`mahjong/management/commands/cleanup_old_rooms.py`のコメントを解除して有効化できます。

### 機能を有効化する場合

`cleanup_old_rooms.py`のコメントアウトされたコードを解除してください。

### 手動実行（機能が有効化されている場合）

管理コマンドを手動で実行する場合：

```bash
# 削除対象を確認（削除はしない）
flyctl ssh console --app mahjong-app -C "python manage.py cleanup_old_rooms --dry-run"

# 実際に削除を実行
flyctl ssh console --app mahjong-app -C "python manage.py cleanup_old_rooms"
```

### ローカルでのテスト（機能が有効化されている場合）

```bash
# 削除対象を確認
python manage.py cleanup_old_rooms --dry-run

# 実際に削除を実行
python manage.py cleanup_old_rooms
```

