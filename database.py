from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 🔽 記号を安全な形（%23, %26）に変換し、最後の文字も修正した完璧なURLです！
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:e3fcv7LXK%2336m%26P@db.cqzjilubjxixdrkooqjr.supabase.co:5432/postgres"

# PostgreSQLの場合はシンプルな設定でOKです！
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()