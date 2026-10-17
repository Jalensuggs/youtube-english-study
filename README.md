# youtube-english-study

一个 [Claude Code](https://claude.com/claude-code) skill：给它一个 YouTube 链接，自动生成单文件的「英语精读本」HTML，双击就能在浏览器里学英语。

## 生成的页面有什么

- 英文字幕重新按完整句子排好，按场景分段，每段有中文导读
- 有用的短语、生词、口语俚语、文化点直接在原文里高亮，旁边是中文意思和用法提示
- 美式音标，点一下朗读（用设备自带的英语语音，可切慢速）
- 每句话带时间戳，点击跳到 YouTube 原视频对应位置听原声
- 三种模式：中英标注 / 遮住中文自测 / 纯英文；浅色、深色主题；手机可读
- 文末短语总表，可以给已掌握的打勾，进度存在浏览器里
- 字幕里的错字、品牌名会被更正并标出来

中文部分只有场景导读和短语释义，没有逐句翻译。

## 安装

需要 [Claude Code](https://claude.com/claude-code)、Python 3 和 [yt-dlp](https://github.com/yt-dlp/yt-dlp)（`brew install yt-dlp`）。

```bash
git clone https://github.com/Jalensuggs/youtube-english-study.git
cp -R youtube-english-study/youtube-english-study ~/.claude/skills/
```

## 使用

在 Claude Code 里说：

> 英文学习 https://www.youtube.com/watch?v=xxxxxxxxxxx

Claude 会下载字幕、划分场景、标注短语和音标，校验后生成 `<视频标题>-英语精读本.html`，并自动上传到本仓库的 `pages/`。

不想自动上传就删掉 `SKILL.md` 里的第 7 步；想传到自己的仓库，改 `scripts/publish.py` 顶部的 `REPO`。

视频需要有英文字幕（官方字幕最好，自动字幕也行，但可能有识别错误）。

## 目录

| 路径 | 说明 |
|---|---|
| `youtube-english-study/SKILL.md` | skill 的工作流程 |
| `youtube-english-study/references/annotation-guide.md` | 场景、标注、音标的写作规范 |
| `youtube-english-study/scripts/` | `fetch.py` 取字幕，`check.py` 校验，`build.py` 生成页面，`drop.py` 去掉字幕杂质，`publish.py` 上传 |
| `youtube-english-study/assets/template.html` | 页面模板 |
| `pages/` | 生成的精读本页面 |

## 关于示例页和版权

`pages/` 里的页面是用 YouTube 上的视频生成的，例如 Volka English 的视频 [LTVk3yUb5Mg](https://www.youtube.com/watch?v=LTVk3yUb5Mg)。页面中的英文台词归各视频作者所有，仅作学习与功能演示。原作者或版权方如要求移除，请提 issue，会立即删除。

自己生成的页面请只用于个人学习，不要公开转载别人视频的台词。

## 许可证

代码和 skill 以 MIT 许可证发布，不包含 `pages/` 中的第三方台词。
