# kaizenova

[![Tests](https://img.shields.io/github/actions/workflow/status/shm11C3/kaizenova/test.yml?style=flat-square&label=tests)](https://github.com/shm11C3/kaizenova/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg?style=flat-square)](#)
[![Agents](https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex-D97757.svg?style=flat-square)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

AIコーディングエージェント向けのタスク実行ループです。散文の注意書きではなく、機械的な強制で回します。

エージェント駆動開発が静かに溜める2つの負債を対象にしています。

- **プロセス負債** — 止めるものがなければ、エージェントは確認・テスト・レビュー返信・振り返りを飛ばしてターンを終えてしまいます。
- **認知負債・意図負債** — 人間がAIの書いたコードを理解できなくなり、コードベースから意図が失われます。

kaizenova は小さな状態機械、**Claude Code / Codex** 両対応のライフサイクルHook、4つの正本Skillをリポジトリに導入します。Hookはタスクサイクルが未完了のままターンを終えることをブロックし、Skillが「完了」の定義を与えます。

## ループの構造

すべてのタスクは実装前に分類されます。

- **contract-preserving(契約保存)** — 結果が依頼や既存の正本で確定しており、観測可能な挙動が変わらないもの。短縮経路: `classification → development → pr → completed`
- **contract-changing(契約変更)** — それ以外すべて。完全経路: `classification → specification → confirmation → gate → development → pr → retrospective → completed`

主な性質は以下のとおりです。

- 契約変更タスクでは、仕様確認と**理解ゲート**が実装の前に立ちます。確認インタビューは「契約を変える決定」と「オーナーの合意が必要な決定」だけに質問を絞り、ゲートは「ドキュメントから答えを探す能力」ではなく、**つながった理解**(システム全体のスケッチ、複数コンポーネントを横断する追跡シナリオ)を検証します。
- **理解台帳**がタスクをまたいで実証済みの理解を持ち越します。ゲートは既に示された理解をクレジットして再質問せず、契約を変えたタスクは依存エントリをstaleにマークするので、次のゲートはそこだけを再検証します。測るのは「今回の理解」ではなく、蓄積された共有モデルとその劣化です。
- **Discovery**(受け入れ・安全・正確性・スコープに影響する発見)は、タスク内解決かIssueリンクのどちらかが必須です。未解決のままではCLIもHookも先へ進ませません。
- 完全経路では**TDDが必須**です。red-green の証跡を残します。
- **振り返りは追加だけでなく削除も行います。** 追加されるルールは発動根拠と削除条件を必ず記録し、振り返りごとに既存ルールの削除レビューを行います。追加しかしないハーネスは過剰設計化してしまうため、このループは縮小できるように作られています。
- **Hookはfail closedです。** 読めない・曖昧な状態レシートは、強制を静かに無効化するのではなくブロックします。

## 導入

要件: gitリポジトリ、Python 3.11+、Claude Code または Codex。macOS・Linux・Windowsで動作します。ネイティブWindowsでは、`python3` がPATHにない場合は `.claude/settings.json` と `.codex/hooks.json` のHookコマンドをお使いのPythonランチャーに変更してください。また、symlinkが使えない環境では `.claude/skills` はコピーになります(更新方法はインストーラが案内します)。

```bash
python3 install.py /path/to/your/repo
```

インストーラはテンプレートをコピーし、既存ファイルは決して上書きしません。導入後は以下を行ってください。

1. `AGENTS.md` の `EDIT ME` をすべて埋める(ミッション、真実の源、任意の検証ステージ、言語規則)。
2. 導入されたファイルをコミットする。

## 使い方

```bash
python3 scripts/task_cycle.py start --task my-task --title "レート制限を追加"
```

あとはエージェントにタスクを依頼すれば `$execute-task-cycle` Skillが経路を選びます。状態レシートは `.kaizenova/task-cycle.json` に置かれ、Hookの挙動と固定/可変の区分は導入後の `docs/agents/ENFORCEMENT.md` をご覧ください。

## 意図的に含めていないもの

QAフェーズ(必要なら `AGENTS.md` にプロジェクト検証ステージとして宣言してください)、マルチエージェント委譲の追跡、PRサイズ計測、状態ファイルのバージョン移行機構は含めていません。理由と、この設計が避けている過剰設計の失敗パターンは [docs/DESIGN.md](docs/DESIGN.md) にまとめています。配布形態・言語選択・除外判断などの個別の決定は、発動根拠と再検討条件つきのADRとして [docs/adr/](docs/adr/) に記録しています。

## 謝辞

確認インタビューの決定木を辿る問答スタイルは、mattpock氏の `grill-me` Skillの思想を借りています。kaizenova では意図的に範囲を絞り、計画全体を網羅的に詰めるのではなく、実装契約を変える決定とオーナーの合意が必要な決定にフォーカスしています。

## ライセンス

[MIT](LICENSE)
