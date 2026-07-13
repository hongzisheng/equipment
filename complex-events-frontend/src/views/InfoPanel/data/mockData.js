export const mockWorkers = [
  {
    worker_id: 'W001',
    worker_name: '张三',
    worker_type: '钳工',
    status: '工作中',
    tasks: [
      {
        task_id: 'T001',
        task_name: '空冷器1检修',
        status: '进行中',
        equipment: '空冷器1',
        start_time: '第1天 08:00',
        end_time: '第1天 12:00'
      },
      {
        task_id: 'T002',
        task_name: '离心泵1检修',
        status: '未开始',
        equipment: '离心泵1',
        start_time: '第2天 08:00',
        end_time: '第2天 16:00'
      }
    ]
  },
  {
    worker_id: 'W002',
    worker_name: '李四',
    worker_type: '焊工',
    status: '工作中',
    tasks: [
      {
        task_id: 'T003',
        task_name: '轴流式通风机1检修',
        status: '进行中',
        equipment: '轴流式通风机1',
        start_time: '第1天 09:00',
        end_time: '第1天 17:00'
      }
    ]
  },
  {
    worker_id: 'W003',
    worker_name: '王五',
    worker_type: '起重工',
    status: '空闲中',
    tasks: []
  },
  {
    worker_id: 'W004',
    worker_name: '赵六',
    worker_type: '电工',
    status: '工作中',
    tasks: [
      {
        task_id: 'T004',
        task_name: '空冷器1检修',
        status: '进行中',
        equipment: '空冷器1',
        start_time: '第1天 10:00',
        end_time: '第1天 15:00'
      },
      {
        task_id: 'T005',
        task_name: '离心泵1检修',
        status: '未开始',
        equipment: '离心泵1',
        start_time: '第3天 08:00',
        end_time: '第3天 12:00'
      }
    ]
  },
  {
    worker_id: 'W005',
    worker_name: '钱七',
    worker_type: '管工',
    status: '已完成',
    tasks: [
      {
        task_id: 'T006',
        task_name: '空冷器1检修',
        status: '已完成',
        equipment: '空冷器1',
        start_time: '第1天 08:00',
        end_time: '第1天 11:00'
      }
    ]
  },
  {
    worker_id: 'W006',
    worker_name: '孙八',
    worker_type: '仪表工',
    status: '工作中',
    tasks: [
      {
        task_id: 'T007',
        task_name: '轴流式通风机1检修',
        status: '进行中',
        equipment: '轴流式通风机1',
        start_time: '第1天 08:00',
        end_time: '第1天 16:00'
      }
    ]
  },
  {
    worker_id: 'W007',
    worker_name: '周九',
    worker_type: '车工',
    status: '空闲中',
    tasks: []
  },
  {
    worker_id: 'W008',
    worker_name: '吴十',
    worker_type: '铣工',
    status: '工作中',
    tasks: [
      {
        task_id: 'T008',
        task_name: '离心泵1检修',
        status: '进行中',
        equipment: '离心泵1',
        start_time: '第1天 13:00',
        end_time: '第1天 18:00'
      }
    ]
  },
  {
    worker_id: 'W009',
    worker_name: '郑一',
    worker_type: '钻工',
    status: '空闲中',
    tasks: []
  },
  {
    worker_id: 'W010',
    worker_name: '王二',
    worker_type: '刨工',
    status: '工作中',
    tasks: [
      {
        task_id: 'T009',
        task_name: '空冷器1检修',
        status: '进行中',
        equipment: '空冷器1',
        start_time: '第1天 14:00',
        end_time: '第1天 20:00'
      }
    ]
  }
]

export const mockOrders = [
  {
    work_order_id: 'WO001',
    order_number: 'WO-2024-001',
    process_name: '空冷器1检修',
    status: 'construction_confirmed',
    work_order_status: 'construction_confirmed',
    equipment_id: 'E001',
    equipment_name: '空冷器1',
    priority: '高',
    workers: {
      '钳工': ['张三'],
      '电工': ['赵六'],
      '管工': ['钱七'],
      '刨工': ['王二']
    }
  },
  {
    work_order_id: 'WO002',
    order_number: 'WO-2024-002',
    process_name: '轴流式通风机1检修',
    status: 'process_closed',
    work_order_status: 'process_closed',
    equipment_id: 'E002',
    equipment_name: '轴流式通风机1',
    priority: '中',
    workers: {
      '焊工': ['李四'],
      '仪表工': ['孙八']
    }
  },
  {
    work_order_id: 'WO003',
    order_number: 'WO-2024-003',
    process_name: '离心泵1检修',
    status: 'eng_approved',
    work_order_status: 'eng_approved',
    equipment_id: 'E003',
    equipment_name: '离心泵1',
    priority: '高',
    workers: {
      '钳工': ['张三'],
      '电工': ['赵六'],
      '铣工': ['吴十']
    }
  },
  {
    work_order_id: 'WO004',
    order_number: 'WO-2024-004',
    process_name: '换热器1清洗',
    status: 'released',
    work_order_status: 'released',
    equipment_id: 'E004',
    equipment_name: '换热器1',
    priority: '低',
    workers: {
      '管工': ['钱七']
    }
  },
  {
    work_order_id: 'WO005',
    order_number: 'WO-2024-005',
    process_name: '压缩机1检修',
    status: 'construction_signed',
    work_order_status: 'construction_signed',
    equipment_id: 'E005',
    equipment_name: '压缩机1',
    priority: '高',
    workers: {
      '钳工': ['张三', '王五'],
      '电工': ['赵六'],
      '焊工': ['李四']
    }
  },
  {
    work_order_id: 'WO006',
    order_number: 'WO-2024-006',
    process_name: '阀门组更换',
    status: 'equipment_closed',
    work_order_status: 'equipment_closed',
    equipment_id: 'E006',
    equipment_name: '阀门组A',
    priority: '中',
    workers: {
      '管工': ['钱七'],
      '钳工': ['周九']
    }
  }
]

export const mockMaterials = [
  {
    material_name: '不锈钢管',
    initial_stock: 100,
    current_stock: 35,
    unit: '米'
  },
  {
    material_name: '法兰盘',
    initial_stock: 50,
    current_stock: 40,
    unit: '个'
  },
  {
    material_name: '螺栓螺母',
    initial_stock: 500,
    current_stock: 200,
    unit: '套'
  },
  {
    material_name: '密封垫片',
    initial_stock: 200,
    current_stock: 50,
    unit: '片'
  },
  {
    material_name: '钢材',
    initial_stock: 2000,
    current_stock: 1500,
    unit: '公斤'
  },
  {
    material_name: '密封胶',
    initial_stock: 50,
    current_stock: 30,
    unit: '支'
  },
  {
    material_name: '电缆',
    initial_stock: 500,
    current_stock: 450,
    unit: '米'
  },
  {
    material_name: '仪表配件',
    initial_stock: 100,
    current_stock: 80,
    unit: '件'
  },
  {
    material_name: '泵体密封件',
    initial_stock: 30,
    current_stock: 10,
    unit: '套'
  },
  {
    material_name: '管道弯头',
    initial_stock: 200,
    current_stock: 180,
    unit: '个'
  }
]

export const mockTools = [
  {
    tool_id: 'TL001',
    tool_name: '电动葫芦',
    tool_type: '起重设备',
    usage_status: '占用',
    usage_tasks: [{ task_name: '空冷器1检修' }]
  },
  {
    tool_id: 'TL002',
    tool_name: '叉车',
    tool_type: '运输设备',
    usage_status: '空闲',
    usage_tasks: []
  },
  {
    tool_id: 'TL003',
    tool_name: '电焊机',
    tool_type: '焊接设备',
    usage_status: '占用',
    usage_tasks: [{ task_name: '轴流式通风机1检修' }]
  },
  {
    tool_id: 'TL004',
    tool_name: '氩弧焊机',
    tool_type: '焊接设备',
    usage_status: '空闲',
    usage_tasks: []
  },
  {
    tool_id: 'TL005',
    tool_name: '通风机',
    tool_type: '通风设备',
    usage_status: '占用',
    usage_tasks: [{ task_name: '空冷器1检修' }]
  },
  {
    tool_id: 'TL006',
    tool_name: '加热器',
    tool_type: '加热设备',
    usage_status: '空闲',
    usage_tasks: []
  },
  {
    tool_id: 'TL007',
    tool_name: '桥式起重机',
    tool_type: '起重设备',
    usage_status: '占用',
    usage_tasks: [{ task_name: '压缩机1检修' }]
  },
  {
    tool_id: 'TL008',
    tool_name: '搬运车',
    tool_type: '运输设备',
    usage_status: '空闲',
    usage_tasks: []
  },
  {
    tool_id: 'TL009',
    tool_name: '切割机',
    tool_type: '焊接设备',
    usage_status: '占用',
    usage_tasks: [{ task_name: '离心泵1检修' }]
  },
  {
    tool_id: 'TL010',
    tool_name: '送风设备',
    tool_type: '通风设备',
    usage_status: '空闲',
    usage_tasks: []
  }
]