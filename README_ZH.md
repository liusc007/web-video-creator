<div align="center">

# 🎬 web-video-creator

**代码驱动的 HTML 转视频引擎 & AI 视频三层后期制作管线**

*别再让视频生成大模型画歪七扭八的乱码字幕和抖动 UI 了——把画面表演交给生成模型，把像素级后期交给 HTML5/CSS3、Playwright 与 FFmpeg。*

[![CI](https://github.com/liusc007/web-video-creator/actions/workflows/ci.yml/badge.svg)](https://github.com/liusc007/web-video-creator/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Playwright + FFmpeg](https://img.shields.io/badge/Engine-Playwright%20%2B%20FFmpeg-06b6d4.svg)](#核心架构)

[English](README.md) · [简体中文](README_ZH.md) · [AI 视频后期实战指南](docs/AI_POST_PRODUCTION_GUIDE.md)

</div>

---

## 为什么做 `web-video-creator`？

可灵 / Runway / Sora / 万相等视频大模型擅长光影氛围与人物表演，但**不擅长**：精确文字排版、监控 HUD 框线、毫秒级时间码、前后呼吸留白与空间声学混响。

与其在每条视频里写一堆脆弱的 PIL 像素硬画脚本，或者忍受大模型抽卡画出来的扭曲文字，**`web-video-creator` 把现代浏览器渲染引擎变成你的确定性影视合成器**：

| AI 视频创作痛点 | 直接提示词让模型硬画 | `web-video-creator` 工程解法 |
| :--- | :--- | :--- |
| **监控框 / 战术 HUD** | 边框抖动、数字乱码、文字变形 | **透明 HTML5/CSS3 图层**（`CCTVScene` / `CyberHUDScene` / `HUDScene`），毫秒级时间码精确走字 |
| **双语卡点字幕** | 错别字直接烧死在底片画面里 | **`TimedSubtitleScene`** 直接吃入 Whisper JSON / SRT，支持逐词高亮与自动偏移对齐 |
| **切镜仓促 / 断崖结尾** | 刚开场 0.1 秒就张嘴、尾音被硬切 | **智能 `tpad` 呼吸补帧** 首尾克隆静止帧，并同步偏移音频时间轴（`adelay`）防止音画错位 |
| **配音像贴脸旁白** | 棚录干音贴进大殿或监控镜头非常假 | **`AudioProcessor`** 提供大殿/教堂/走廊/监控扬声器声学滤镜 + 房间底噪自动合成 |
| **CSS 动画帧率漂移** | 截图耗时导致动效快慢不一 | **逐帧锁步动画引擎**（`document.getAnimations()` + `--hf-progress`）确保每一帧绝对确定 |

---

## 核心架构

```text
┌──────────────────────────────────────────────────────────────────────┐
│ 第一层 · Raw AI Video Layer（纯净底片层）                              │
│   无文字/无UI的纯净 AI 底片 + FFmpeg tpad 首尾智能克隆呼吸帧           │
├──────────────────────────────────────────────────────────────────────┤
│ 第二层 · Web Overlay Layer（透明网页包装层 - Playwright + CSS3/SVG）   │
│   CompositeScene 在隔离的全屏图层中同步叠放：                           │
│   - CCTVScene / CyberHUDScene / HUDScene（5 套配色，动态时间码）       │
│   - TimedSubtitleScene（Whisper 词级高亮 / SRT，自动对齐补帧时长）      │
├──────────────────────────────────────────────────────────────────────┤
│ 第三层 · Spatial Audio Layer（空间声学混音层 - FFmpeg）                │
│   场景早期反射混响（hall/cathedral/corridor/cctv_speaker/radio）       │
│   + 自动合成环境底噪（Room Tone）+ 切镜静电音效                         │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 安装

> **前置依赖**：请确保系统中已安装 [FFmpeg](https://ffmpeg.org/download.html)（`ffmpeg` 与 `ffprobe` 在环境变量 `PATH` 中）。

```bash
git clone https://github.com/liusc007/web-video-creator.git
cd web-video-creator
pip install -e .
playwright install chromium
```

---

## 快速上手

### 1. 命令行工具（`wvc`）

```bash
# 将本地 HTML 文件或文字卡片直接渲染为 1080p MP4
wvc render examples/sample.html -o sample.mp4 -d 5.0
wvc --text "你好，网页视频" -o hello.mp4 -d 3.0

# 第一层：为 AI 原生视频首尾智能克隆呼吸静止帧
wvc pad --video raw_ai_clip.mp4 -o padded.mp4 --start 0.35 --stop 0.50

# 第二层：在底片上叠加透明安防监控 / 赛博扫描 HUD（支持同步叠加 SRT 字幕）
wvc overlay --video padded.mp4 --type cctv --theme emerald \
  --title "CAM-07 [SANCTUARY]" --srt dialogue.srt -o overlaid.mp4

# 第三层：为干音配音添加大殿空间混响与尾音淡出保护
wvc audio --input dry_voice.mp3 --preset hall --fade-out 0.08 -o hall_voice.aac

# 一键全流程：通过声明式 JSON/YAML 配置自动跑完三层合成
wvc build examples/project_example.json -o final_cut.mp4

# 查看全部内置预设
wvc presets
```

### 2. Python API

参考完整示例 [`examples/cctv_ai_post_production.py`](examples/cctv_ai_post_production.py)，支持自动探测底片分辨率（横屏 16:9 / 竖屏 9:16 / 4K 均自适应铺满）。

---

## 开源协议

本项目基于 [MIT License](LICENSE) 开源，欢迎提交 Issue 与 Pull Request！
