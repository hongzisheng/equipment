/**
 * 文本预处理工具类
 * 提供常见的文本清理和格式化功能
 */
export class TextPreprocessor {
  /**
   * 去除文本中的所有空格
   * @param text 输入文本
   * @returns 处理后的文本
   */
  static removeAllSpaces(text: string): string {
    return text.replace(/\s+/g, '');
  }

  /**
   * 将空格替换为换行符
   * @param text 输入文本
   * @returns 处理后的文本
   */
  static spacesToNewlines(text: string): string {
    return text.replace(/\s+/g, '\n');
  }

  /**
   * 去除多余的空格，只保留单个空格
   * @param text 输入文本
   * @returns 处理后的文本
   */
  static removeExtraSpaces(text: string): string {
    return text.replace(/\s+/g, ' ').trim();
  }

  /**
   * 去除文本首尾空格
   * @param text 输入文本
   * @returns 处理后的文本
   */
  static trimSpaces(text: string): string {
    return text.trim();
  }

  /**
   * 去除文本中的换行符
   * @param text 输入文本
   * @returns 处理后的文本
   */
  static removeNewlines(text: string): string {
    return text.replace(/[\r\n]+/g, '');
  }

  /**
   * 将多个连续换行符合并为单个换行符
   * @param text 输入文本
   * @returns 处理后的文本
   */
  static normalizeNewlines(text: string): string {
    return text.replace(/[\r\n]+/g, '\n').trim();
  }

  /**
   * 综合预处理文本
   * 1. 去除首尾空格
   * 2. 合并多余空格
   * 3. 合并换行符
   * @param text 输入文本
   * @returns 处理后的文本
   */
  static preprocess(text: string): string {
    return text
      .trim()
      .replace(/\s+/g, ' ')
      .replace(/[\r\n]+/g, '\n');
  }
}

// 导出便捷函数
export const removeAllSpaces = TextPreprocessor.removeAllSpaces;
export const spacesToNewlines = TextPreprocessor.spacesToNewlines;
export const removeExtraSpaces = TextPreprocessor.removeExtraSpaces;
export const trimSpaces = TextPreprocessor.trimSpaces;
export const removeNewlines = TextPreprocessor.removeNewlines;
export const normalizeNewlines = TextPreprocessor.normalizeNewlines;
export const preprocess = TextPreprocessor.preprocess;

export default TextPreprocessor;
