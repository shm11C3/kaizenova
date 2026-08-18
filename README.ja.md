# kaizenova

[English](README.md) | 日本語

[![Tests](https://img.shields.io/github/actions/workflow/status/shm11C3/kaizenova/test.yml?style=flat-square&label=tests)](https://github.com/shm11C3/kaizenova/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg?style=flat-square)](#)
[![Agents](https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex-D97757.svg?style=flat-square)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

AIコーディングエージェント向けのタスク実行ループです。文章での注意書きではなく、機械的な強制で回します。

エージェント駆動開発が静かに溜める2つの負債を対象にしています。

- **プロセス負債** — 止めるものがなければ、エージェントは確認・テスト・レビュー返信・ふりかえりを飛ばしてターンを終えてしまいます。
- **認知負債・意図負債** — 人間がAIの書いたコードを理解できなくなり、コードベースから意図が失われます。

kaizenova は小さなステートマシン、**Claude Code / Codex** 両対応のライフサイクルHook、4つの標準Skillをリポジトリに導入します。Hookはタスクサイクルが未完了のままターンを終えることをブロックし、Skillが「完了」の定義を与えます。

## ループの構造

すべてのタスクは実装前に分類されます。

- **contract-preserving(契約保存)** — 結果が依頼や既存の信頼できる情報源で確定しており、観測可能な挙動が変わらないもの。短縮経路: `classification → development → pr → completed`
- **contract-changing(契約変更)** — それ以外すべて。完全経路: `classification → specification → confirmation → gate → development → pr → retrospective → completed`

主な性質は以下のとおりです。

- 契約変更タスクでは、仕様確認と**理解ゲート**が実装の前に立ちます。確認インタビューは「契約を変える決定」と「オーナーの合意が必要な決定」だけに質問を絞り、ゲートは「ドキュメントから答えを探す能力」ではなく、**つながった理解**(システム全体のスケッチ、複数コンポーネントを横断する追跡シナリオ)を検証します。
- **理解台帳**がタスクをまたいで実証済みの理解を持ち越します。ゲートは既に示された理解を実績として引き継ぎ、同じことを再質問せず、契約を変えたタスクは依存エントリを stale(要再確認)としてマークするので、次のゲートはそこだけを再検証します。測るのは「今回の理解」ではなく、蓄積された共有モデルとその劣化です。
- **Discovery**(受け入れ・安全・正確性・スコープに影響する発見)は、タスク内解決かIssueリンクのどちらかが必須です。未解決のままではCLIもHookも先へ進ませません。
- 完全経路では**TDDが必須**です。red-green の証跡を残します。
- **ふりかえりは追加だけでなく削除も行います。** 追加されるルールは発動根拠と削除条件を必ず記録し、ふりかえりごとに既存ルールの削除レビューを行います。追加しかしないハーネスは過剰設計化してしまうため、このループは縮小できるように作られています。
- **Hookはfail closedです。** 読めない・曖昧な状態レシートは、強制を静かに無効化するのではなくブロックします。

## 導入

### 前提

- 導入先となるgitリポジトリ(インストーラはリポジトリのルートに書き込みます)
- Python 3.11以上。`python3` で実行できること(`python3 --version` で確認できます)
- Claude Code または Codex(Hookは両方分が導入され、各エージェントは他方のファイルを無視します)

サードパーティ製パッケージは不要で、標準ライブラリのみで動作します。

### 1. kaizenova を取得する

kaizenova はパッケージとして配布していません。導入先リポジトリの外側の任意の場所に一度cloneし、そこからインストーラを実行します。

```bash
git clone https://github.com/shm11C3/kaizenova.git
```

### 2. インストーラを実行する

```bash
python3 kaizenova/install.py /path/to/your/repo
```

指定するパスはgitリポジトリの**ルート**である必要があります。インストーラは `template/` の中身をそこへコピーし、**既存ファイルは決して上書きしません**。すでに存在するファイルは「left in place」として一覧表示されるので、必要に応じて手でマージしてください。この性質があるため、アップグレードも同じコマンドの再実行で行えます(再実行し、報告された衝突を確認する)。

導入されるものは以下のとおりです。

| パス | 内容 |
|---|---|
| `AGENTS.md`, `CLAUDE.md` | エージェント向けのガイダンス。`EDIT ME` プレースホルダを埋めて使います |
| `.agents/skills/` | 4つの標準Skill |
| `.claude/`, `.codex/` | Hookアダプタ、パーミッション、承認ルール |
| `scripts/` | ステートマシンのCLIと、両エージェント共通のHook判定コア |
| `docs/agents/` | 強制の仕様、理解台帳、ふりかえりテンプレート |

### 3. `AGENTS.md` を埋める

`AGENTS.md` を開き、`EDIT ME` プレースホルダをすべて置き換えてください。埋め終わったら、周囲のコメントは削除します。

- **ミッション** — このプロジェクトが何であり、どんな成果が作業を正当化するのか
- **信頼できる情報源(sources of truth)** — 成果・不変条件・設計を確定させるドキュメントの一覧。ワークフローはこのリストを読みます
- **プロジェクト検証ステージ** — 任意。PRレビュー後に追加の検証が必要なら宣言し、不要ならセクションごと削除します
- **言語規則** — 人間向けドキュメント(Issue、PR、ふりかえり)と、コードやエージェント向けガイダンスをそれぞれどの言語で書くか

### 4. 導入されたファイルをコミットする

インストーラが追加したファイルをすべてコミットしてください。HookとSkillは、リポジトリに入って初めて効き始めます。

### Windowsでの注意

kaizenova は macOS・Linux・Windows で動作します。ネイティブWindowsでは次の2点が異なります。

- `python3` がPATHにない場合は、`.claude/settings.json` と `.codex/hooks.json` のHookコマンドをお使いのPythonランチャー(通常は `py -3`)に変更してください
- symlinkが使えない環境では、`.claude/skills` の各エントリは `.agents/skills` へのリンクではなくコピーになります。そのため後からの変更が自動では反映されません。更新方法はインストーラが案内します

## 使い方

```bash
python3 scripts/task_cycle.py start --task my-task --title "レート制限を追加"
```

あとはエージェントにタスクを依頼すれば `$execute-task-cycle` Skillが経路を選びます。状態レシートは `.kaizenova/task-cycle.json` に置かれ、Hookの挙動と固定/可変の区分は導入後の `docs/agents/ENFORCEMENT.md` をご覧ください。

## テンプレートの内容

| 構成要素 | 役割 |
|---|---|
| `.agents/skills/execute-task-cycle` | タスク手順の正本。分類、2つの経路、TDD、Discovery、PRのルール |
| `.agents/skills/gate-shared-understanding` | 理解ゲート。記憶の再生ではなく、統合された理解を試すよう設計されています |
| `.agents/skills/reflect-and-improve-harness` | ふりかえり。既存ルールの削除レビューが必須です |
| `.agents/skills/review-design-complexity` | 過剰設計の監査。本質的/偶発的/投機的/検証不足に分類します |
| `scripts/task_cycle.py`, `scripts/task_cycle_core.py` | ステートマシンのCLIと、エージェント非依存のHook判定コア |
| `.claude/`, `.codex/` | 両エージェント向けのHookアダプタ、パーミッション、承認ルール |
| `scripts/find_relevant_lessons.py` | 記録済みの教訓・ふりかえりに対する、有限で決定的な検索 |
| `docs/agents/` | 強制の仕様、理解台帳、ふりかえりテンプレート、教訓ディレクトリ |

Claude Code と Codex は単一の判定コアを共有し、アダプタは各エージェントの入出力契約だけを担います。そのため、ワークフローの判断が両者で食い違うことはありません。

## 意図的に含めていないもの

QAフェーズ(必要なら `AGENTS.md` にプロジェクト検証ステージとして宣言してください)、マルチエージェント委譲の追跡、PRサイズ計測、状態ファイルのバージョン移行機構は含めていません。理由と、この設計が避けている過剰設計の失敗パターンは [docs/DESIGN.md](docs/DESIGN.md) にまとめています。配布形態・言語選択・除外判断などの個別の決定は、発動根拠と再検討条件つきのADRとして [docs/adr/](docs/adr/) に記録しています。

## 開発

```bash
python3 tests/check_task_cycle.py
```

## 謝辞

確認インタビューの決定木を辿る問答スタイルは、mattpocock氏([@mattpocock](https://github.com/mattpocock))の [`grill-me`](https://github.com/mattpocock/skills/blob/main/docs/productivity/grill-me.md) Skillの思想を借りています。kaizenova では意図的に範囲を絞り、計画全体を網羅的に詰めるのではなく、実装契約を変える決定とオーナーの合意が必要な決定にフォーカスしています。

## ライセンス

[MIT](LICENSE)
