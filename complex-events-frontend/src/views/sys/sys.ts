import systemApi from '@/api/systemApi';
import { number } from 'echarts';


export interface PerformanceData {
  MongoDBUnExtract: number;
  MongoDBExtract: number;
  redis:number;
  Users: number;
  ChromaDB: number;
  cpu_freq: number;
  cpu_usage: number;
  gpu_temp: number;
  gpu_usage: number;
  neo4j_count: number;
  memory_usage: number;
  memory_percent:[];
}

async function fetchPerformanceData(): Promise<PerformanceData> {
  const res = await systemApi.getPerformanceData();
  return res.data as PerformanceData;
}

export const getPerformanceData = async (): Promise<PerformanceData> => {
  return await fetchPerformanceData();
};
