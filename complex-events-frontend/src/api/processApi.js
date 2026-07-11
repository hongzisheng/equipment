import { mockProcessList, mockEquipmentInfo } from './mockData';
export function getProcessList(params) {
 let list = mockProcessList.list.map(p => ({ ...p }));
 if (params) {
 if (params.equipment_category) {
 list = list.filter(p => p.equipment_category === params.equipment_category);
 }
 if (params.equipment_type) {
 list = list.filter(p => p.equipment_type_name === params.equipment_type);
 }
 if (params.equipment_id) {
 list = list.filter(p => p.equipment_id === parseInt(params.equipment_id));
 }
 if (params.status) {
 list = list.filter(p => p.status === params.status);
 }
 }
 return Promise.resolve({
 code: 20000,
 message: '查询成功',
 data: {
 total: list.length,
 list
 }
 });
}
export function getProcessDetail(id) {
 const process = mockProcessList.list.find(p => p.id === id);
 if (process) {
 return Promise.resolve({
 code: 20000,
 message: '查询成功',
 data: process
 });
 }
 return Promise.resolve({
 code: 50000,
 message: '未找到该流程'
 });
}
export function updateProcess(data) {
 const { id, status, approval_comments } = data;
 const process = mockProcessList.list.find(p => p.id === parseInt(id));
 if (process) {
 process.status = status;
 if (approval_comments) {
 process.approval_comments = approval_comments;
 }
 }
 return Promise.resolve({
 code: 20000,
 message: '更新成功',
 data: {}
 });
}
export function getEquipmentInfo() {
 return Promise.resolve({
 code: 20000,
 message: '查询成功',
 data: mockEquipmentInfo
 });
}
