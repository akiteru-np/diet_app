from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 🔽 ここにステップ2でコピーしたURLを貼り付けます！
# ※ [YOUR-PASSWORD] の部分を、ステップ1で決めたパスワードに書き換えてください（カッコ [] も消します）
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:e3fcv7LXK#36m&P@db.cqzjilubjxixdrkooqjr.supabase.co:5432/postgrespos"

# PostgreSQLの場合はシンプルな設定でOKです！
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()