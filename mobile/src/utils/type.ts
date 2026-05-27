
export interface WorkOrderProcess {
  process_id: string
  process_name: string
  equipment_id: number
  equipment_name: string
  description: string
  estimated_hours: number

  task_id: number
  task_code: string
  task_status: string
  is_milestone: boolean
  assignment_status: string

  scheduled_start_time: string // "YYYY-MM-DD HH:mm:ss"
  scheduled_end_time: string
  actual_start_time: string | null
  actual_end_time: string | null

  work_order_id: number
  order_number: string
  work_order_title: string
  work_order_status: string
  priority: string
  worker_name: string
  worker_type: string
  // 手动格式化选项，选项需要展示的内容
  option: string
}

// 工单类型
export interface WorkOrder {
  work_order_id: number
  work_order_title: string
  order_number: string
  work_order_status: string
  priority: string
  work_order_created_at: string // "YYYY-MM-DD HH:mm:ss"
  worker_name: string
  worker_type: string
  processes: WorkOrderProcess[]
  // 手动格式化选项，选项需要展示的内容
  option: string
}
