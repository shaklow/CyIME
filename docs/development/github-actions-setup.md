# GitHub Actions 配置（shaklow/CyIME）

## 签名配置

2026-10-31 按用户要求为此仓库新建独立的正式签名密钥，RSA 4096 位、有效期 10000 天、别名 `cyime-release`。后续版本持续使用这套密钥；它与上游发布包及此前的 Debug 测试包签名不同。

已在仓库 Settings → Secrets and variables → Actions 配置以下 **Repository secrets**：

| 名称 | 内容 |
| --- | --- |
| `SIGNING_KEY` | 正式 JKS 文件的单行 Base64 |
| `KEY_STORE_PASSWORD` | Keystore 密码 |
| `ALIAS` | 私钥别名 |
| `KEY_PASSWORD` | 私钥密码 |

另已配置 Repository variable `SIGNING_CERT_SHA256`：

```text
7e5c1188916d7d0f85ed16cd05637ae57fe3149cf1add3a065a7a859232c621e
```

`GITHUB_TOKEN` 由 GitHub 为每个 job 自动提供，无需创建同名 secret 或额外的个人 PAT。仓库 Actions 已启用，默认 token 权限保持只读；Release/Nightly 在 workflow 中声明 `contents: write`，测试报告 job 单独声明 `checks: write`。参见 [GitHub Token 文档](https://docs.github.com/en/actions/concepts/security/github_token)。

## 私有备份

本机备份目录：`D:/Tools_a/AAA/typer/CyIME/.codex-artifacts/signing/shaklow-CyIME/`。该目录被 Git 忽略，Windows ACL 仅允许当前用户与 SYSTEM 访问。

- `cyime-release.jks`：正式密钥。
- `keystore.properties`：配套密码和别名。
- `github-secrets.json`：用于恢复四个 Actions secrets 的原始值。
- `cyime-release.pem`、`signing-receipt.json`：公开证书及生成回执。

WSL 同源备份：`/home/erenche/.config/cyime/signing/shaklow-CyIME/`，目录权限 0700，密钥和密码文件 0600。请另行保留一份离线备份；GitHub 不能读回 secret 的原始值。上述私有文件不提交、不作为 Actions artifact 上传。

## Workflow 行为

- Build / Full Test Suite / Release / Nightly 使用 JDK 21，与项目 Gradle daemon 配置一致。
- Release 与 Nightly 都调用 `scripts/ci/setup_signing.py`。它从环境变量读取 secrets，校验证书指纹与私钥密码，在 `RUNNER_TEMP` 写入密钥，再生成仅当前用户可读的 Gradle signing 配置；结束时删除临时签名文件。
- Release 支持 `v1.2.3` 与 `1.2.3` 两种 tag，并先核对 tag 与源码 `versionName` 一致。只有推送版本 tag 才创建公开 Release。
- Release 按逐行 glob 上传 APK/插件，使用当前 action 支持的 `overwrite_files`，匹配不到交付文件时失败，避免发布空资产。
- 手动运行 Release 默认 `signing_check_only=true`：只验证 GitHub secrets 能否解锁正确密钥，不打包、不发布。取消此项可构建签名 APK 及插件，结果上传到 artifact，仍不创建公开 Release。
- 按当前仓库规则，尺寸渲染门禁默认暂停；手动完整构建时可通过 `run_layout_gate` 显式开启。
- Nightly 复用源码 `versionCode`，版本名附加日期和 commit，不再用日期覆盖安装序号；创建 nightly 时显式记录构建 commit。
- 外部 fork PR 和 Dependabot 的 Build 运行不发布需要写权限的 Checks 报告，JUnit artifact 仍保留。

## 验证与上线状态

四个 secrets 名称与更新时间、证书指纹变量已通过 GitHub API 回读核对。真实密钥在 WSL 完成 15 项检查，包括有效密钥、四个缺失 secret、错误 Base64/密码/别名/证书、已有配置保护，以及通过 Java `Properties.load` 校验真实密码和特殊字符的读取结果。

全部 6 个 workflow 通过官方 actionlint 1.7.12 的语法与表达式检查；使用到的 11 个 action 版本标签已通过各官方 GitHub 仓库回读确认存在。

本轮只修改 workflow、辅助脚本和文档，不重新打包 APK。workflow 配置通过提交推送到默认分支生效。按用户 2026-10-31 的最新要求，**Nightly 保持禁用**。

GitHub runner 的验证使用 [Release workflow](https://github.com/shaklow/CyIME/actions/workflows/release.yml) 的 `signing_check_only=true` 模式，运行结果以 Actions 记录及本机 `.codex-artifacts/github-actions-setup-20261031/` 中的回执为准；这项校验不创建公开 Release。
