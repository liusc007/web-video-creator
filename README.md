# web-video-creator

将 HTML 文档转换为视频的 Python 工具。基于 Playwright 截图 + FFmpeg 编码。

## 安装

```bash
git clone https://github.com/liusc007/web-video-creator.git
cd web-video-creator
pip install -e .
playwright install chromium
```

## 快速使用

```bash
# 文字场景
python -m web_video_creator.cli --text "你好世界" -o hello.mp4

# 图片场景
python -m web_video_creator.cli --image https://example.com/img.png -o img.mp4

# API 方式
python examples/demo.py
```

## 项目结构

```
web-video-creator/
├── web_video_creator/    # 核心库
│   ├── converter.py      # 视频渲染引擎
│   ├── scene.py          # 场景定义（文字/图片）
│   └── cli.py           # 命令行入口
├── examples/             # 示例
├── tests/                # 测试
└── .github/workflows/    # CI
```

## 技术栈

- **Playwright** — 无头浏览器截图
- **FFmpeg** — 视频编码
- **Python 3.10+**
