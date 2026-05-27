// src/utils/markdown.ts
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
  // 小程序 rich-text 仅识别 HTML 换行，先把后端常见换行格式归一化。
  const normalized = (source || '')
    .replace(/\\r\\n/g, '\n')
    .replace(/\\r/g, '\n')
    .replace(/\\n/g, '\n')
    .replace(/↵/g, '\n')

  return md.render(normalized)
}
