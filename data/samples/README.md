# サンプルデータ（取り込み用）

`/ingest` 画面からアップロードして試せます。

| ファイル | 取り込み先 | 内容 |
|----------|------------|------|
| `maintenance_records_sample.xlsx` | Excel 保全実績 | 12 件の保全実績 |
| `daily_report_sample.txt` | 日報 (txt) | 8 件の日報ブロック |
| `maintenance_manual_sample.pdf` | PDF / 画像 | 標準対応手順の抜粋 |

## 使い方

1. `/login` でログイン
2. `/ingest` を開く
3. 上表のファイルを各カードへアップロード
4. `/records` と `/chat` で結果を確認

## 再生成

```bash
cd TechnologySuccession
python scripts/generate_sample_data.py
```

Docker 利用時:

```bash
docker run --rm -v "%CD%:/app" -w /app tech-succession-backend:latest python scripts/generate_sample_data.py
```
