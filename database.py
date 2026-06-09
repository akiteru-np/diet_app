from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 🔽 【最終奥義】ドライバー指定(psycopg2)、Sessionポート(5432)、SSL強制(sslmode=require)をすべて盛り込んだ完全版！
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres.cqzjilubjxixdrkooqjr:e3fcv7LXK%2336m%26P@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres?sslmode=require"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()