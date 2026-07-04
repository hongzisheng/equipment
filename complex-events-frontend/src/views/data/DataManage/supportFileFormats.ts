interface FileFormat {
  // 展示出来的文件格式
  label: string
  // 文件格式的值
  value: string
  // 展示时候用到的颜色
  color: string
}

/**
 * 文件上传的时候支持的文件类型的列表
 */
const supportFileFormats: FileFormat[] = [
  {
    label: 'HTML',
    value: 'html',
    color: '#E44D26',
  },
  {
    label: 'XML',
    value: 'xml',
    color: '#0075AF', // 蓝色，科技感
  },
  {
    label: 'TXT',
    value: 'txt',
    color: '#4A90E2', // 天蓝色，简洁清新
  },
  {
    label:"JSON",
    value: 'json',
    color: '#a54ae2',
  },
  {
    label: 'JPG',
    value: 'jpg',
    color: '#7ED321', // 青绿色，图像处理常用色
  },
  {
    label: 'PNG',
    value: 'png',
    color: '#FF9500', // 橙色，与JPG区分
  },
  {
    label: 'DOCX',
    value: 'docx',
    color: '#2B579A', // 深蓝色，Microsoft Word官方色
  },
  {
    label: 'PPTX',
    value: 'pptx',
    color: '#FF7F00', // 橙色，Microsoft PowerPoint官方色
  },
  {
    label: 'PDF',
    value: 'pdf',
    color: '#E51400',
  },
  {
    label:'MP3',
    value: 'mp3',
    color: '#FF5722', // 深橙色，适合音频文件
  },
  {
    label:'WAV',
    value: 'wav',
    color: '#FF9800', // 橙色，与MP3区分
  },
  {
    label:'MP4',
    value: 'mp4',
    color: '#2196F3', // 蓝色，适合视频文件
  },
  {
    label:'AVI',
    value: 'avi',
    color: '#03A9F4', // 浅蓝色，与MP4区分
  },
  {
    label:'MOV',
    value: 'mov',
    color: '#3F51B5', // 靛蓝色，Apple格式特色色
  }

]
export const supportFileValues = supportFileFormats.map(file=>file.value)
export default supportFileFormats
