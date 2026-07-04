import { ElMessageBox, ElMessage } from 'element-plus';
// 自定義的封裝的下載文件的方法
export function downloadFileWithConfirmation({
  apiCall,
  id,
  fileName,
  confirmMessage,
  fileType = 'application/octet-stream',
  fileExtension = 'pdf',
  filePrefix = 'file'
}) {
  // 显示确认框
  ElMessageBox.confirm(`您确认下载： ${fileName} ${confirmMessage} 文件吗?`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
    dangerouslyUseHTMLString: true
  }).then(() => {
    // 调用API获取文件的Base64编码
    apiCall(id).then(response => {
      // 显示成功提示
      ElMessage({
        type: 'success',
        message: response.message
      });

      const fileContentBase64 = response.data;
      const fileContent = atob(fileContentBase64);
      const byteNumbers = new Uint8Array(fileContent.length);

      // 将Base64编码的内容解码为二进制数据
      for (let i = 0; i < fileContent.length; i++) {
        byteNumbers[i] = fileContent.charCodeAt(i);
      }

      // 创建 Blob 对象，指定不同类型
      const blob = new Blob([byteNumbers], { type: fileType });

      // 创建下载链接并触发下载
      const uuid = crypto.randomUUID();
      const down_file_name = `${id}_${filePrefix}_${uuid}.${fileExtension}`; // 文件名可以灵活配置
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.setAttribute('download', down_file_name);
      document.body.appendChild(link);
      link.click();

      // 移除链接
      document.body.removeChild(link);
    }).catch(error => {
      // 显示错误提示
      ElMessage.error('提交失败，请重试');
    });
  }).catch(() => {
    // 用户取消下载时的提示
    ElMessage({
      type: 'info',
      message: `已取消下载：${fileName}`
    });
  });
}
