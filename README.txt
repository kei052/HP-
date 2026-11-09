履修ガチ勢 改良版

index.html: ホーム
jobs.html: 職種検索・履修予定かご・履修済み確認
licenses.html: 資格検索・取得予定/取得済み
mypage.html: ニックネーム・診断へのリンク
anke-to.html: 既存診断
history.html: 既存履歴

注意：講義別の開講学年・学期データは提供されたCSVに含まれていないため、自動的な学期絞り込みは未実装です。履修予定講義の学期を手動設定できます。
資格の取得予定/取得済みは端末のlocalStorageに保存され、適合率の計算にはまだ連動しません。
既存アプリとは別フォルダで動作確認してください。CSVをfetchするため、VS Code Live Server等のローカルサーバーかGitHub Pagesが必要です。

更新：重複クイックリンク削除、講義検索表記、増加分明るい黄緑、かご絵文字削除、グラフのタブ固定、比較欠損値null化、各ページにアイコン枠追加。
既存のアイコン画像は提供されていません。icons/icon-192.png を配置すると全ページに表示されます。

講義一覧API:
- backend フォルダで `python main.py` を実行すると、http://127.0.0.1:8000/courses で講義一覧を取得できます。
- API は backend/database/subjects_simple.csv を読み込み、GET /courses に JSON を返します。
- 講義ごとの科目区分は `subject_category_1` と `subject_category_2` として返します。
- 別オリジンのブラウザから呼び出せるよう、読み取り専用APIとしてCORSを許可しています。
- 外部環境で待ち受ける場合は `HOST=0.0.0.0` と `PORT` 環境変数を設定してください。
