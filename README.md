# GULF 字幕文字 V2

这是独立运行的字幕 + 文字说明工具。

## 直接使用

Windows 用户直接双击：

**run_gulf_subtitle.bat**

也可以双击：

**start-lightweight.bat**

两个入口现在都会启动同一个 V2 程序。

完整说明见：

**README_CN.md**

## 核心工作流

上传视频 → 本地 Whisper 英语识别 → 本地中文翻译 → 前 3 秒说明 → 960×540 审核代理 → 人工检查/修改 → 刷新审核预览 → 审核通过 → 最终 MP4 + SRT + ASS。

本程序不修改 GULF Studio 主程序，也不自动发布到平台。
