# 滑动退格清空与上屏后候选

## 行为

对照本地 Xime 的 `ImeKeyRouter.hasInputState()`：上屏后的联想、等待中的预测和剪贴板候选不属于未完成输入。退格键的清空手势在这些状态下一次清空整个输入框，同时清除候选并取消旧预测，避免迟到回填。

仍在输入中文编码、英文当前词或九键分段组词时，保留只清当前输入的行为。继续保留引擎繁忙/不可用时不删除正文的保护。普通点击和长按退格的路由未修改。

整框清空继续使用 `DocumentClear`，保留光标两侧、选区一起清空和原位撤回；下滑撤回也不再被单纯的联想/剪贴板候选阻挡。

## 同步上游后的维护范围

用户 2026-10-31 明确要求本 fork 只维护这项滑动清空改动，其他更新和问题修复交给上游。当前整合基于上游版本 1.15.24，保留其「打字中清空整个输入框」开关及宿主拒绝删除时的回退处理；清空状态统一只清理一次。版本元数据继续沿用上游，本次提交不扩展到 UI 门禁断言维护。

下方 1.15.11 构建及 12 项测试记录为此前首次验证的历史回执；当前提交的验证结果以 GitHub Actions 对应 commit 的运行记录为准。

## 实现与检查

- `CandidateState.hasUncommittedInputForClear()` 只判定未完成输入；路由另外保留原生引擎状态检查。
- 空闲清空复用 `clearInputStateForKeys()`，同时取消在途预测、清理展开候选与分页状态。
- 新增 `ClearGestureInputStateTest` 六项回归用例：联想候选、剪贴板候选、空闲、中文编码、英文补全、九键分段。
- `git diff --check` 通过。WSL 中 `ClearGestureInputStateTest` 6 项和 `DocumentClearTest` 6 项全部通过，无失败、错误或跳过；后者覆盖整框清除、选区与光标恢复、编辑后不撤回。应用及测试 Kotlin 编译通过。

## 构建与交付

用户已明确允许本轮只在 WSL Linux 目录构建，临时放宽 C/D 盘余量要求。构建副本：`erenche@192.168.39.159:/home/erenche/build/cyime-swipe-clear-20261031`；本地只保留源码、最终 APK 和小型验证报告。

测试命令：

```sh
./gradlew :app:testDebugUnitTest \
  --tests com.kingzcheung.xime.service.ClearGestureInputStateTest \
  --tests com.kingzcheung.xime.service.DocumentClearTest \
  --no-daemon --console=plain -I scripts/phone-release-abi.gradle
```

打包命令：

```sh
./gradlew :app:assembleDebug --no-daemon --console=plain --max-workers=2 \
  -I scripts/phone-release-abi.gradle
```

两次成功运行均使用 JDK 21、已有 Android SDK，并设置 `LANG=C.UTF-8 LC_ALL=C.UTF-8`。首次准备遇到 Windows CRLF 导致词库校验失败，仅在 Linux 副本恢复 UTF-8 文本的 LF 换行；随后初始化锁定的原生子模块。SSH 默认字符编码还曾导致资源中文文件名读不到，设置 UTF-8 后解决。未修改主工作区的构建脚本来绕过这些检查。

交付版本 **1.15.11 / 20261363**，APK `D:/Tools_a/AAA/typer/CyIME/.codex-artifacts/swipe-clear-20261031/CyIME-1.15.11-debug-arm64-v8a.apk`，227,274,034 字节，SHA-256 `4799c0e4af25d1b2892e71a512bc13da7f0334ddb132a62a0504d4eb13cc5493`。已核对应用 ID `com.cyletix.cyime`、ARM64 单架构及 13 个原生库；`apksigner verify` 通过，证书为 Android Debug，非发布签名。环境没有项目发布签名配置，因此本轮提供 Debug 验证包。复制回工作区后哈希一致。

交付目录同时保存两份 JUnit XML、测试及打包日志、APK 核对记录、四个实际构建源码文件的哈希清单；已核对构建副本与工作区归一化换行后的源码完全一致。未提交 Git，未公开发布。

## 空间与真机验证

原生链接后构建副本约 4.4 GiB，加上新增 Gradle 缓存，短暂超出 5 GiB 临时预算。已清理本轮可再生的原生对象、合并/剥离库副本、Boost 解压目录、重复 ONNX 解压文件和单测临时 APK，并按哈希硬链接去重 ONNX 库。最终构建副本 1.809 GiB、新增 Gradle 数据 2.709 GiB、本地交付文件 0.212 GiB，合计 **4.730 GiB**；WSL 剩余约 906.3 GiB。测试报告、源码哈希与最终 APK 保留。

未发现已连接 ADB 设备，**未安装、未真机验证、用户未验收**。当前工作区为用户提供的 `D:/Tools_a/AAA/typer/CyIME`，旧规则中的 `D:/GitHub/CyIME` 和外部 Todo/设备状态页在本机不存在，未向不存在的外部台账写入记录。
