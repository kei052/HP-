# 履修ガチ勢：講義・職業・資格バックエンドAPI

通常は **`python backend/app_server.py`** （アプリ用フォルダーから）で起動してください。
画面、認証、データ同期、講義・職業・資格のAPIが同じポートで使用できます。

`backend/database/*.csv` が唯一のマスターデータです。`GET /api/catalog` で現在の6テーブルをID付きで取得し、画面の職業適合率と資格適合率を計算します。バックエンドと同じCSVから生成したスナップショットをJSに同梱しているため、HTML単体でも同梱時点の結果をプレビューできます。

## API
- `GET /api/catalog` : フロントエンド用の結合マスター
- `GET /courses`, `/jobs`, `/qualifications` : 一覧、件数
- `GET /courses/{id}`, `/jobs/{id}`, `/qualifications/{id}` : 詳細と関連情報
- `POST /diagnosis` : `{"completed_course_ids":["S003"]}`
- `POST /simulation` : `{"completed_course_ids":["S003"],"candidate_course_ids":["S004"]}`

レスポンスに `completed` および `simulated` の職業・資格適合率が含まれます。職業はscoreの割合、資格は関連講義数の割合。重複した講義IDは一度だけ数えます。

`python backend/main.py` はマスター/API単独サーバーです。ログインやHTML配信は行わないため、通常利用には `app_server.py` を選んでください。

## テスト
`cd backend && python -m unittest discover -s tests -v`

## 注意
今の `job_courses.csv` はscore 100の関連が148件あり、**職業によって分母（関連講義数）が異なります**。関連付けがない講義では適合率は増えません。新しい講義や職業を追加した際は関連CSVにもIDで結合行を用意してください。
