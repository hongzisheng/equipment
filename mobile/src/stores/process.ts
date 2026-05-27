import { reactive } from 'vue'
import Taro from '@tarojs/taro'
import type { WorkOrderProcess } from '@/utils'

const STORAGE_KEY = 'current_process'

const loadCurrentProcess = (): WorkOrderProcess | null => {
  const cached = Taro.getStorageSync(STORAGE_KEY)
  return cached || null
}

const state = reactive<{ currentProcess: WorkOrderProcess | null }>({
  currentProcess: loadCurrentProcess()
})

const setCurrentProcess = (process: WorkOrderProcess) => {
  state.currentProcess = process
  Taro.setStorageSync(STORAGE_KEY, process)
}

const clearCurrentProcess = () => {
  state.currentProcess = null
  Taro.removeStorageSync(STORAGE_KEY)
}

const store = {
  get currentProcess() {
    return state.currentProcess
  },
  setCurrentProcess,
  clearCurrentProcess
}

export const useProcessStore = () => store
