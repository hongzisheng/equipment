import MarkdownIt from 'markdown-it'

// 初始化 markdown-it 实例
const md = new MarkdownIt({
  html: false,        // 禁用 HTML 标签，防止 XSS 攻击
  breaks: true,       // 将段落中的换行符转换为 <br>
  linkify: true,      // 自动将 URL 转换为链接
  typographer: true,  // 启用一些语言学的替换，如 (c) 转换为 ©
})

/**
 * 将 Markdown 字符串渲染为 HTML 字符串
 * @param source Markdown 源文本
 * @returns HTML 字符串
 */
export function renderMarkdown(source: string): string {
  // 更新思考消息为实际回复
  // 将文本中的“斜杠n”当作普通字符处理，避免被渲染成额外换行/空行。
  const normalized = (source || '')
    // 双重转义: "\\n" -> 空格
    .replace(/\\\\n/g, '')
    // 单层转义: "\n" -> 空格
    .replace(/\\n/g, '')
    // 真实换行统一
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')
    .replace(/↵/g, '\n')
    // 清理“带空格的空行”，避免空白行膨胀
    .replace(/\n[ \t]+\n/g, '')
    // 连续 3 个及以上换行压缩为 2 个，保留段落语义
    .replace(/\n{3,}/g, '')
    // 去掉首尾多余空行
    .replace(/^\n+|\n+$/g, '')
  return md.render(normalized)
}
