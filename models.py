from sqlalchemy import Column, Integer, Float, Date
from database import Base

class Weight(Base):
    # データベースの中に作られる実際のテーブル（表）の名前
    __tablename__ = "weights"

    # カラム（列）の定義：Step 3で一緒に考えた項目です！
    id = Column(Integer, primary_key=True, index=True)  # 背番号（自動で番号が振られます）
    date = Column(Date, index=True)                     # 日付
    weight = Column(Float)                              # 体重（小数点もOKなFloat型）