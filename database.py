from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 🔽 Renderの無料枠でも確実につながる「Pooler（IPv4）仕様」の完璧なURLです！
SQLALCHEMY_DATABASE_URL = "postgresql://postgres.cqzjilubjxixdrkooqjr:e3fcv7LXK%2336m%26P@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()