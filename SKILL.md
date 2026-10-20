---
name: douyin-download
description: 从用户已登录的抖音网页定位指定视频或收藏列表中的视频，并下载到本地、核验文件。适用于下载抖音收藏第一条、指定收藏或给定视频链接。
---

# 抖音视频下载

使用可用的 `mcp__cua_repl` 浏览器控制接口操作用户的抖音页面。首次调用与 API 使用遵循工具返回的文档。优先复用用户已登录的浏览器；不要读取浏览器凭据或通过 shell 提取 cookies。

## 定位目标

- 通过浏览器清单找到抖音页面；没有页面时，在同一浏览器打开 `https://www.douyin.com`。
- 下载收藏内容时进入“我的”→“收藏”→“视频”。用户说“收藏夹第一条”且没有指定命名收藏夹时，可按收藏视频列表左上角第一条理解；若明确指定命名收藏夹，进入相应收藏夹。
- 根据可见页面的排列确认目标，记录作者、标题、视频链接。不要把 DOM 中任意第一个链接当作第一条视频。
- 如打开列表视频后出现连播，提取已确认目标的链接并进入独立的 `/video/<id>` 页面，避免等待期间自动切换到后续视频。
- 登录或验证码阻挡时，保留页面并按当前工具的确认规则处理，不声称已经下载。

## 下载真实媒体源

等待目标页播放器加载，检查播放器对应的 DOM。抖音播放器可能使用 blob 地址或 MediaSource，同时在 `<video>` 内保留多个 `<source src="https://…">`。

成功经验：直接对 `<video>` 调用 `downloadMedia()` 曾等待约两分钟后超时；在独立视频页对第一个真实 `<source>` 调用同一方法，成功保存 MP4。优先检查 source，避免先重复尝试 blob 下载。

以下为 `cua_repl` 中已绑定 `tab` 后的示例；选择器必须根据当前页面确认，多个播放器时先限定目标播放器：

```javascript
// 只读取当前媒体 DOM，不读取页面内部状态、凭据或存储。
nodeRepl.write(await tab.playwright.locator('video').evaluateAll(es =>
  es.map(e => ({
    currentSrc: e.currentSrc,
    sources: Array.from(e.querySelectorAll('source')).map(s => s.src),
    width: e.videoWidth,
    height: e.videoHeight
  }))
));

// 已确认此 source 属于目标视频，且 src 是非空 HTTPS 媒体地址。
let savedPath = await tab.playwright.locator('video source').first()
  .downloadMedia({timeoutMs: 60000});
nodeRepl.write(savedPath);
```

使用浏览器工具实际返回的路径，不假设文件名或下载目录。不要持久化带签名的源地址、账号标识或会话参数到 skill、日志报告或交付说明中。

没有 source 或下载失败时，可检查页面可见的保存/下载入口，或在浏览器支持时使用 `pageAssets` 的 `list()` 与 `bundle()` 保存已观察到的视频资源。不要把播放页 HTML、封面或未完成的下载当成视频；不要通过猜测接口或修改签名参数来替代已观察到的源。

## 验证与交付

拿到下载路径后，用文件工具核验文件存在、大小非零且类型为视频（例如 `file` 识别为 MP4）。可用媒体检查工具时检查时长与音视频流；如需重命名，避免覆盖已有文件。

只有下载成功且文件核验通过，才能报告“下载完成”。简短告知作者/标题、文件大小和可点击的绝对路径。失败时说明具体阻碍与已完成的定位结果，不谎报成功。
