from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# データベースのファイル名（diet_app.db というファイルが作られます）
SQLALCHEMY_DATABASE_URL = "sqlite:///./diet_app.db"

# データベースとの通信を確立するエンジン
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# データベースとやり取りするための「セッション（窓口）」を作る準備
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 今後作るテーブル（Weightなど）の「元となる型」
Base = declarative_base()