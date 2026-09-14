# Output verification

Status: **passed**

- Raw / valid unique / rejected-warning / duplicates: **25,433 / 13,867 / 11,566 / 1,142**
- CSV and Parquet schemas, order, row counts and listing IDs reconcile.
- Clean listing IDs are unique; every clean row is `valid` and `unique`.
- Both workbooks have all seven required sheets, clean headers, 8 control formulas, and no formula error tokens.
- 14 workbook sheet previews were rendered for visual QA.
- Geographic features: 12 regions, 46,043 cities/towns, 967 districts/neighborhoods.
