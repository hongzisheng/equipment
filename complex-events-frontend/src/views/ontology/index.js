import { ElMessage } from 'element-plus'

export function getTableHeaderStyle() {
  return {
    background: '#f5f7fa',
    color: '#606266',
  }
}

export const NOT_IMPL_WARN = (message) => {
  console.warn('功能暂未实现'+(message? '：'+message: ''))
  ElMessage.warning('功能暂未实现'+(message? '：'+message: ''))
}
