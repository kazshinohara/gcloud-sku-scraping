# Google Cloud SKU Group / SKU ID 抽出スクリプト

このスクリプトは、Google Cloud SKU Group ページ (https://cloud.google.com/skus/sku-groups) をスクレイピングし、各 SKU Group に関連付けられているすべての SKU ID を抽出して、そのマッピングを CSV ファイルに出力します。

## 特徴

- SKU Group ページの並行処理
- SKU ID フィールドのインテリジェントな列検出
- 複数ページにわたる SKU Group リストのページネーションサポート
- 失敗したリクエストに対する指数バックオフを使用した自動再試行
- 中断された実行を再開するための進行チェックポイント
- 重複 SKU ID の除去
- 詳細なロギング

## 要件

- Python 3.6+
- 必要な Python パッケージ（requirements.txt 参照）

## インストール

1. このリポジトリをクローンするかファイルをダウンロードします
2. 必要な依存関係をインストールします：

```bash
pip install -r requirements.txt
```

## 使用方法

### スクレイパーの実行

スクリプトを直接実行できます：

```bash
python skuid_group_scraper.py
```

または、仮想環境をセットアップする提供されたシェルスクリプトを使用します：

```bash
./run_scraper.sh
```

スクリプトは以下を実行します：
1. メイン SKU Group ページからすべての SKU Group リンクを取得
2. 各 SKU Group ページにアクセスして関連する SKU ID を抽出
3. 実行中に進行チェックポイントを保存
4. 各 SKU ID とその SKU Group のマッピングを CSV ファイル（`sku_id_to_group_mapping.csv`）に出力

### 結果の分析

スクレイパーを実行した後、付属の分析スクリプトを使用して結果を分析できます：

```bash
./analyze_results.py
```

または特定の CSV ファイルを指定して：

```bash
./analyze_results.py path/to/your/csv_file.csv
```

分析スクリプトは以下を提供します：
- SKU ID と SKU Group の総数
- SKU ID 数による上位 10 の SKU Group
- 1つの SKU ID のみを持つグループの統計
- グループあたりの平均 SKU 数
- SKU ID フォーマットの分析

## 出力

出力 CSV ファイルには2つの列が含まれます：
- `SKU ID`: Google Cloud SKU ID
- `SKU Group`: SKU ID が属する SKU Group の名前

チェックポイントファイルは `temp_data` ディレクトリに保存されます。

## 設定

スクリプトにはファイルの先頭に複数の設定可能なパラメータがあります：
- `MAX_WORKERS`: 同時実行スレッド数（デフォルト: 5）
- `MAX_RETRIES`: 失敗したリクエストの再試行回数（デフォルト: 3）
- `RETRY_DELAY`: 再試行間の基本遅延（秒）（デフォルト: 2）

## 注意事項

- スクリプトはレート制限を回避するためにランダムな遅延とジッターを使用します
- ヘッダーは標準的なブラウザリクエストを模倣するように設定されています
- SKU ID はそのフォーマット（英数字とハイフン）に基づいて識別されます
- スクリプトは SKU ID 列を識別するために複数の一般的なヘッダー名をチェックします
- Web スクレイピングはレート制限やその他の制限の対象となる可能性があることに注意してください
- スクリプトは SKU ID が詳細ページのテーブルの最初の列にあることを前提としています 