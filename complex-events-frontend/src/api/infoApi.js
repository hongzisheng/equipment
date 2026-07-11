import { mockWorkers, mockOrders, mockMaterials, mockTools } from './mockData';

export function getWorkerStatus(data) {
  return Promise.resolve({
    code: 20000,
    message: '查询成功',
    data: mockWorkers
  });
}

export function getOrders() {
  return Promise.resolve({
    code: 20000,
    message: '查询成功',
    data: mockOrders
  });
}

export function getMaterialInventory(data) {
  return Promise.resolve({
    code: 20000,
    message: '查询成功',
    data: mockMaterials
  });
}

export function getMaintenanceTools(data) {
  return Promise.resolve({
    code: 20000,
    message: '查询成功',
    data: mockTools
  });
}
