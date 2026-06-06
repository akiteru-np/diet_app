from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "はじめてのAPIが動きました！ダイエットアプリ開発スタート！"}
