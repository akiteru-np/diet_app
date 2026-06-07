import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- 🌐 本番環境（Render）の金庫パスに対応させる魔法 ---
# Render上の金庫（/data）が存在すればそこを使い、なければいつものローカルを使う
if os.path.exists("/data"):
    SQLALCHEMY_DATABASE_URL = "sqlite:////data/diet_app.db"
else:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./diet_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()