# WenFei Clash 全局扩展配置

为 Clash Verge / Clash Verge Rev 提供 YAML 全局扩展配置和 JavaScript 全局扩展脚本。
请按用途切换分支；`main` 是导航和自动同步入口，配置文件放在各自的版本分支。

## 分支导航

| 分支 | 用途 | 主要文件 |
| --- | --- | --- |
| [main](https://github.com/freebaipiao/WenFei-clash-global-extend-config/tree/main) | 默认分支，存放分支说明及同步工作流 | `README.md`、`.github/workflows/sync-clashconfig.yml` |
| [ver.jiahao](https://github.com/freebaipiao/WenFei-clash-global-extend-config/tree/ver.jiahao) | 自动同步 `clashconfig/codex` 的四套配置，提供 YAML 和 JS 版本 | `config.*`、`no_rate_config.*`、`no_dns_override.*`、`no_dns_override_no_rate.*` |
| [ExperimentalVersion](https://github.com/freebaipiao/WenFei-clash-global-extend-config/tree/ExperimentalVersion) | 原实验版，将已有规则转换为全局覆写，验证直接使用机场原始订阅的方案 | `Merge.yaml`、`Script.js` |
| [FalledInLoveVersion](https://github.com/freebaipiao/WenFei-clash-global-extend-config/tree/FalledInLoveVersion) | 已谈恋爱版，提供地区及低、普通、高倍率分组，并支持下载策略选择倍率分组 | `Script.js` |
| [SparkingVersion](https://github.com/freebaipiao/WenFei-clash-global-extend-config/tree/SparkingVersion) | 心动版，保留 Steam 分类与独立下载分组，精简地区和倍率分组，将漏网之鱼显示在前面 | `Script.js` |
| [RulesConverter](https://github.com/freebaipiao/WenFei-clash-global-extend-config/tree/RulesConverter) | 将 YAML 规则列表转换为 JavaScript 规则数组的辅助工具 | `converter.py` |

现有历史版本保留原有内容。需要自动跟随上游更新时选择 `ver.jiahao`。

## ver.jiahao 的四种配置

| 配置名 | DNS 和 FCM hosts | 倍率分组 |
| --- | --- | --- |
| `config` | 覆盖并同步上游 DNS、FCM hosts | 有 |
| `no_rate_config` | 覆盖并同步上游 DNS、FCM hosts | 无 |
| `no_dns_override` | 保留订阅原有 DNS 和 hosts | 有 |
| `no_dns_override_no_rate` | 保留订阅原有 DNS 和 hosts | 无 |

每种配置同时提供 `.yaml` 和 `.js`。`Merge.yaml`、`Script.js` 是 `config` 的兼容文件名。
在客户端选择一个版本：YAML 全文放入“全局扩展配置”，或者 JS 全文放入“全局扩展脚本”。
这些文件使用 Mihomo 的动态节点和规则集功能，具体使用方法见
[ver.jiahao 的 README](https://github.com/freebaipiao/WenFei-clash-global-extend-config/blob/ver.jiahao/README.md)。

## 自动同步

来源为 [freebaipiao/clashconfig 的 codex 分支](https://github.com/freebaipiao/clashconfig/tree/codex)。
[工作流](.github/workflows/sync-clashconfig.yml)每天北京时间 **04:07、10:07、16:07、22:07**
检出该分支，转换四份 INI，并将有变化的结果提交到 `ver.jiahao`。
GitHub 定时执行可能延迟；未发生变化时不会生成空提交。

可在 Actions 页面手动运行 `Sync clashconfig to ver.jiahao`。
工作流使用当前仓库的 `GITHUB_TOKEN`，只需 `contents: write`，无需额外 PAT。
源仓库的基础模板和三个自定义规则文件也会同步，上游快照和来源提交保存在
`ver.jiahao` 的 `upstream/` 中。转换失败时保留上一份成功结果。

本分支从空白分支创建，仅包含此说明和同步工作流。
