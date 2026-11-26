履修ガチ勢 アプリ用フォルダ（backend/database連携版）

【起動】
「Windowsで起動.bat」または `python backend/app_server.py` で起動してください。
ブラウザ URL: http://127.0.0.1:8000/index.html

【データの参照元】
「backend/database/」にある以下の6ファイルが講義・職業・資格の原本です。
  courses.csv / jobs.csv / qualifications.csv
  job_courses.csv / job_qualifications.csv / qualification_courses.csv
IDで関連付けて適合率を算出しています。
古いルート直下の data.csv / data1.csv は計算に使いません。

※HTML単体での確認時は、同梱時点でのマスターデータを表示します。
backend/databaseの変更を反映するには、同梱サーバーから開いて更新してください。
詳細は「起動方法.txt」および「backend/README.md」を参照してください。
