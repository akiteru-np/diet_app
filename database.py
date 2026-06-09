import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. パスワード内の記号（#や&）を、Pythonに自動で安全な形式に変換させます
encoded_password = urllib.parse.quote_plus("e3fcv7LXK#36m&P")

# 2. Render無料枠（IPv4）と最も相性が良い公式ポート「6543」でURLを自動結合します
SQLALCHEMY_DATABASE_URL = f"postgresql://postgres.cqzjilubjxixdrkooqjr:{encoded_password}@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"

# 3. SQLAlchemyがSupabaseと通信するための最適化設定（途切れ防止機能を追加）
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,      # 通信が生きているか毎回確認する（エラー落ち防止）
    pool_recycle=3600        # 古い接続を自動で綺麗にする
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()