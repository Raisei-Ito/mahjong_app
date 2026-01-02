# Python 3.11を使用
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 環境変数を設定
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# 静的ファイルを収集（rootユーザーで実行）
RUN python manage.py collectstatic --noinput || true

# 起動スクリプトをコピーして実行可能にする
COPY start.sh /start.sh
RUN chmod +x /start.sh

# 非rootユーザーは一時的にコメントアウト（SQLiteの書き込み権限の問題のため）
# RUN useradd -m -u 1000 appuser && \
#     chown -R appuser:appuser /app && \
#     chmod +x /start.sh
# USER appuser

# ポート8080を公開
EXPOSE 8080

# 起動コマンド（マイグレーションを自動実行）
CMD ["/start.sh"]

