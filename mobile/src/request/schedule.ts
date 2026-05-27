import request,{baseURL} from '@/request/index';
import Taro from "@tarojs/taro";

/**
 * 获取员工工单信息
 * @param userId 需要获取的员工的id
 */
export function getSchedule(userId: number = 5) {
  return request({
    method: 'GET',
    url: `/worker-workorders/${userId}`,
  }).then((response) => {
    if (response.success && Array.isArray(response.data)) {
      // 根据时间先后顺序排序
      return  [...response.data].sort((a, b) => {
        const startDiff =
          new Date(a.scheduled_start_time.replace(' ', 'T')).getTime() -
          new Date(b.scheduled_start_time.replace(' ', 'T')).getTime()

        if (startDiff !== 0) return startDiff

        return (
          new Date(a.scheduled_end_time.replace(' ', 'T')).getTime() -
          new Date(b.scheduled_end_time.replace(' ', 'T')).getTime()
        )
      })
    }else{
      return Promise.reject(response)
    }

  })
}
type UpdateProgressPayload = {
  taskId: number
  description: string
  status?: string
  imagePath?: string // 小程序 chooseImage 返回的临时路径
}

export async function updateProgress(payload: UpdateProgressPayload) {
  const { taskId, description, status, imagePath } = payload
  const token = Taro.getStorageSync('token')

  // 页面层是“一个逻辑”，这里内部兜底处理不同传输方式
  if (imagePath) {
    return Taro.uploadFile({
      url: `${baseURL}/work-order-tasks/${taskId}/update-status`,
      filePath: imagePath,
      name: 'photo',
      formData: {
        description,
        ...(status ? { status } : {})
      },
      header: token ? { Authorization: `Bearer ${token}` } : {}
    }).then((res) => {
      console.log("imageUpload",res)
      const data = JSON.parse(res.data || '{}')
      if (res.statusCode >= 200 && res.statusCode < 300) return res
      return Promise.reject(data)
    })
  }

  return request({
    url: `/work-order-tasks/${taskId}/update-status`,
    method: 'PUT',
    data: {
      description,
      ...(status ? { status } : {})
    }
  })
}

/**
 * 获取工序所需的材料清单
 * @param taskId 任务ID
 */
export function getProcessMaterials(taskId: number) {
  return request({
    method: 'GET',
    url: `/work-order-tasks/${taskId}/suggestions`,
  })
}
