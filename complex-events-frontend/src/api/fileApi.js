import request from '@/utils/request'

export const uploadFileApi = import.meta.env.VITE_APP_BASE_API + '/file/upload'
export default {
  // 展示文件列表
  getFileList(searchModel) {
    return request({
      url: '/file',
      method: 'get',
      params: {
        pageNo: searchModel.pageNo,
        pageSize: searchModel.pageSize,
      },
    })
  },
  // 删除文件
  deleteFilesById(reportIdList) {
    return request({
      url: `/file/deleteReports`,
      method: 'delete',
      data: reportIdList,
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },
  // 新增文件
  addFile(file) {
    return request({
      url: '/file',
      method: 'post',
      data: file,
    })
  },
  getFileById(id) {
    return request({
      url: `/file/${id}`,
      method: 'get',
    })
  },

  // 展示文件id对应的分块
  showContent(file_id) {
    return request({
      url: `/file/show_content/${file_id}`,
      method: 'get',
    })
  },
  // 根据文件id查找对应的所有的块进行信息抽取
  extractByFileid(file_id) {
    return request({
      url: `/file/extract_by_fileid/${file_id}`,
      method: 'get',
    })
  },
  // 不带分页展示文件列表
  getFileListNoPage() {
    return request({
      url: '/file/list',
      method: 'get',
    })
  },
  // 下載文件
  downloadFile(file_id) {
    return request({
      url: `/file/base64/${file_id}`,
      method: 'get',
    })
  },
  search(keyword, onlyId = false) {
    return request({
      url: `/file/search`,
      method: 'get',
      params: {
        keyword: keyword,
        onlyId: onlyId,
      },
    })
  },
  searchById(reportId) {
    return request({
      url: `/file/searchById`,
      method: 'get',
      params: {
        reportId: reportId,
      },
    })
  },
}
