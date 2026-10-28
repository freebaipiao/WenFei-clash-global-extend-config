# ver.jiahao：Clash Verge 全局扩展配置

将 [freebaipiao/clashconfig 的 codex 分支](https://github.com/freebaipiao/clashconfig/tree/codex)
中的四份 INI 转换为可直接使用的 YAML 合并配置和 JavaScript 扩展脚本。
适用于使用 Mihomo 内核的 Clash Verge / Clash Verge Rev，可直接配合机场原始订阅使用。

## 四个版本

| 上游 INI | YAML 合并配置 | JS 扩展脚本 | DNS / FCM hosts | 倍率分组 |
| --- | --- | --- | --- | --- |
| `config.ini` | [config.yaml](config.yaml) | [config.js](config.js) | 覆盖并同步 | 有 |
| `no_rate_config.ini` | [no_rate_config.yaml](no_rate_config.yaml) | [no_rate_config.js](no_rate_config.js) | 覆盖并同步 | 无 |
| `no_dns_override.ini` | [no_dns_override.yaml](no_dns_override.yaml) | [no_dns_override.js](no_dns_override.js) | 保留订阅配置 | 有 |
| `no_dns_override_no_rate.ini` | [no_dns_override_no_rate.yaml](no_dns_override_no_rate.yaml) | [no_dns_override_no_rate.js](no_dns_override_no_rate.js) | 保留订阅配置 | 无 |

[Merge.yaml](Merge.yaml) 与 `config.yaml` 内容相同；[Script.js](Script.js) 与 `config.js`
内容相同，方便沿用原来的文件名。

## 使用

选择一个版本和一种格式：将 YAML 全文复制到客户端的“全局扩展配置”，
或者将 JS 全文复制到“全局扩展脚本”。推荐 JS 版；不要同时启用两种格式。
本仓库文件只提供扩展配置，节点和订阅由客户端原来的配置提供。

策略组使用 Mihomo 的 `include-all` 和正则过滤，同时支持订阅中的 `proxies`
和 `proxy-providers`。机场的套餐到期、重置时间等提示节点会从动态分组中排除。
地区和倍率正则保留上游写法；没有匹配节点的分组通过 `empty-fallback: DIRECT` 兜底。
请使用支持这些字段的近期 Mihomo 内核。

两种格式都会替换规则和策略组，并启用进程规则匹配。Steam 下载专用规则仍位于
通用下载器进程和 SteamCN 规则之前，最后一条仍为 `MATCH,🐟 漏网之鱼`。
带 DNS 的版本使用上游 `clash-base.yml` 中的 DNS 和 FCM hosts；JS 版还会保留
原有的其他 hosts。两个 `no_dns_override` 版本不写入 DNS 或 hosts。
FCM 的 IPv4、IPv6 映射原样保留，实际可达性取决于本地网络。

上游自己的三个 `.list` 已展开到生成配置中。其他外部规则通过 31 个
`rule-providers` 加载，客户端每 24 小时更新一次。首次加载需要能访问对应的规则地址。
更新本仓库后，远程引用用户需要重新获取配置；复制粘贴用户需要重新粘贴新内容。

## 自动同步

默认分支 `main` 只存放分支导航和
[同步工作流](.github/workflows/sync-clashconfig.yml)，运行时检出 `ver.jiahao`
和 `freebaipiao/clashconfig` 的 `codex`，重新生成所有配置。
定时计划为每天北京时间 **04:07、10:07、16:07、22:07**，GitHub 实际执行可能延迟。
也可在 Actions 页面手动运行 `Sync clashconfig to ver.jiahao`。

工作流只向 `ver.jiahao` 提交变化，使用本仓库自带的 `GITHUB_TOKEN`，
权限为 `contents: write`，不需要额外 PAT。没有变化时不提交；上游文件缺失、
出现不支持的 INI 选项或转换失败时不提交，继续保留上一份成功配置。
如分支保护禁止机器人直接写入，需要允许该工作流更新 `ver.jiahao`。

每次同步会保留 [upstream](upstream) 中的 INI、基础模板、规则文件和上游许可证，
[upstream/source.json](upstream/source.json) 记录来源提交与各输入文件的 SHA-256。
`main` 和 `ver.jiahao` 中的工作流文件应保持相同；定时事件使用 `main` 的版本。

## 本地生成

```bash
python -m pip install -r requirements.txt
# 从仓库内保存的上游快照重新生成
python scripts/convert_ini.py

# 或从已检出的 clashconfig/codex 生成并更新快照
python scripts/convert_ini.py --source-dir ../clashconfig
```

生成器为 [scripts/convert_ini.py](scripts/convert_ini.py)，依赖固定版本的 PyYAML。
修改转换逻辑后重新运行生成器；手工修改生成文件会在下次同步时被覆盖。
其他分支的用途见 [main 分支导航](https://github.com/freebaipiao/WenFei-clash-global-extend-config/tree/main)。

上游源文件的许可证保留在 [upstream/LICENSE](upstream/LICENSE)，转换配置保留上游来源。
