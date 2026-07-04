import { ElMessage } from 'element-plus'
import dataApi from '@/api/dataApi.js'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

// ------------------------------
// 1. 类型定义（集中管理所有接口类型）
// ------------------------------

/** 提示词 */
interface PromptItem {
  key: string
  name: string
  prompt: string
}

export interface OntologyPromptOption {
  label: string
  value: string
  field?: string
  promptList?: PromptItem[]
  // 节点类型
  type?: string
  // 映射到表格的时候的属性名
  prop?: string
  // 是否固定列
  fixed?: boolean
  // 抽取提示词的key
  promptKey?: string
}

/** 本体配置项类型 */
interface ExtractFieldItem {
  field: string
  SelectedStrategy: number
}

export interface OntologyConfigurationItem {
  label: string // 配置名称
  extract_fields_list: ExtractFieldItem[] // 提取字段列表
}

/** 关系数据类型 */
export interface Relation {
  source: string // 源节点
  target: string // 目标节点
  type: string // 关系类型
}

/** 本体系统数据（事件、人物等字段） */
export interface OntologySystemData {
  eventName: string
  person: string
  role: string
  time: string
  place: string
  action: string
  organization: string
  reportId: string
}

// ------------------------------
// 2. 缓存管理（按数据类型分组）
// ------------------------------

/** 本体系统选项缓存（字段+提示词列表） */
let ontologyPromptCache: OntologyPromptOption[] = []

/** 关系数据缓存 */
let relationsCache: Relation[] = []

/** 本体配置缓存（从后端获取的配置列表） */
let ontologyConfigurationCache: OntologyConfigurationItem[] = []

/**
 * 获取本体系统选项（字段+提示词列表）
 * 优先从缓存获取，无缓存则请求接口
 */
export function getOntologyPromptOptions(): Promise<OntologyPromptOption[]> {
  return new Promise((resolve, reject) => {
    if (ontologyPromptCache.length > 0) {
      resolve([...ontologyPromptCache])
      return
    }

    dataApi
      .getFieldsPrompt()
      .then((response) => {
        const rawData = response.data.prompt || []

        if (!Array.isArray(rawData)) {
          ElMessage.error('获取本体数据格式错误')
          return reject(new Error('返回数据不是数组'))
        }

        const options: OntologyPromptOption[] = rawData.map((item) => ({
          ...item,
          promptList: Array.isArray(item.promptList) ? item.promptList : [],
        }))

        ontologyPromptCache = [...options]
        resolve(options)
      })
      .catch((error) => {
        ElMessage.error('获取本体数据失败')
        console.error('获取本体系统选项失败:', error)
        reject(error)
      })
  })
}

/**
 * 获取本体配置列表（从后端接口）
 */
export async function getOntologyConfigurationCache(): Promise<OntologyConfigurationItem[]> {
  try {
    const response = await dataApi.getOntologyConfiguration()

    if (response && response.data && Array.isArray(response.data.configurations)) {
      ontologyConfigurationCache = [...response.data.configurations]
      return [...ontologyConfigurationCache]
    } else {
      console.warn('后端返回的数据格式不符合预期，没有 configurations 数组')
      return []
    }
  } catch (error) {
    console.error('获取本体配置数据失败:', error)
    ElMessage.error('获取本体配置失败')
    return []
  }
}

/**
 * 获取所有关系数据
 * 优先从缓存获取，无缓存则请求接口
 */
export function getAllRelations(): Promise<Relation[]> {
  return new Promise((resolve, reject) => {
    if (relationsCache.length > 0) {
      console.log('✅ 从缓存获取关系数据')
      resolve([...relationsCache])
      return
    }

    dataApi
      .getEventsLinkConfiguration()
      .then((response) => {
        const rawRelations = response.data?.eventsLink || []

        if (!Array.isArray(rawRelations)) {
          ElMessage.error('获取关系数据格式错误（非数组）')
          return reject(new Error('关系数据格式异常，需为数组'))
        }

        // 过滤并转换有效关系数据
        const validRelations: Relation[] = rawRelations
          .filter((item) => {
            const hasRequiredFields = item.source && item.target && item.type
            if (!hasRequiredFields) {
              console.warn('过滤无效关系数据（字段缺失）:', item)
              return false
            }
            return true
          })
          .map((item) => ({
            source: item.source,
            target: item.target,
            type: item.type,
          }))

        relationsCache = [...validRelations]
        // console.log('✅ 从接口获取并缓存关系数据:', validRelations)
        resolve(validRelations)
      })
      .catch((error) => {
        ElMessage.error('获取关系数据失败')
        console.error('调用 getEventsLinkConfiguration 接口失败:', error)
        reject(error)
      })
  })
}

/**
 * 根据字段名搜索相关关系
 * @param fieldName 字段名（源或目标）
 */
export function searchRelations(fieldName: string): Promise<Relation[]> {
  return getAllRelations().then((allRelations) => {
    const matchedRelations = allRelations.filter(
      (item) => item.source === fieldName || item.target === fieldName,
    )
    console.log(`✅ 筛选字段 ${fieldName} 的关系数据:`, matchedRelations)
    return matchedRelations
  })
}

// ------------------------------
// 4. Pinia Store（本体配置相关状态管理）
// ------------------------------

export const useOntologyStore = defineStore(
  'ontology',
  () => {
    // state
    const ontologyConfigurations = ref<OntologyConfigurationItem[]>([])
    const ontologyPrompt = ref<OntologyPromptOption[]>([])
    const relations = ref<Relation[]>([])
    const isLoading = ref<boolean>(false)

    // actions
    const initData = async () => {
      isLoading.value = true
      try {
        const [configs, options, relationsData] = await Promise.all([
          getOntologyConfigurationCache(),
          getOntologyPromptOptions(),
          getAllRelations(),
        ])
        ontologyConfigurations.value = configs
        ontologyPrompt.value = options
        relations.value = relationsData
      } catch (error) {
        console.error('初始化本体数据失败:', error)
        ElMessage.error('重新获取数据失败，请稍后重试')
      } finally {
        isLoading.value = false
      }
    }

    const updateOntologyConfiguration = (
      newItem: OntologyConfigurationItem[] | OntologyConfigurationItem,
      editItem: string = "extract_list"
    ) => {
      //传入修改提取列表的单项
      if (editItem === "extract_list") {
        if (!newItem || typeof newItem !== "object" || Array.isArray(newItem)) {
          console.error("传入的配置格式错误 — 应为单个配置对象", newItem)
          return
        }
        const singleItem = newItem as OntologyConfigurationItem

        const updatedConfigurations = ontologyConfigurations.value.map(oldItem => {
          if (oldItem.label === singleItem.label) {
            return { ...oldItem, extract_fields_list: singleItem.extract_fields_list || [] }
          }
          return oldItem
        })

        const isNewItem = !ontologyConfigurations.value.some(oldItem => oldItem.label === singleItem.label)
        if (isNewItem) {
          updatedConfigurations.push(singleItem)
        }
        ontologyConfigurations.value = updatedConfigurations
        ontologyConfigurationCache = [...updatedConfigurations]

      } else if (editItem === "label") {
        //传入整个修改后的列表
        if (!Array.isArray(newItem)) {
          console.error("传入的数据格式错误 — 当 editItem 为 'label' 时，应传入配置项数组", newItem)
          return
        }
        const newArray = newItem as OntologyConfigurationItem[]
        ontologyConfigurations.value = newArray
        ontologyConfigurationCache = [...newArray]

      } else {
        console.warn(`未识别的 editItem 类型: ${editItem}`)
      }
    }

    /** 更新本体系统选项 */
    const updateOntologyPromptOptions = (newPromptOptions: OntologyPromptOption[]) => {
      ontologyPrompt.value = newPromptOptions
      ontologyPromptCache = [...newPromptOptions]
    }

    /** 更新关系数据 */
    const updateRelations = (newRelations: Relation[]) => {
      relations.value = newRelations
      relationsCache = [...newRelations]
    }

    /** 重置所有状态 + 重新从数据库获取数据 */
    const resetState = async () => {
      isLoading.value = true
      try {
        // 清空状态（与state属性名保持一致）
        ontologyConfigurations.value = []
        ontologyPrompt.value = []
        relations.value = []
        // 清空缓存
        ontologyConfigurationCache = []
        ontologyPromptCache = []
        relationsCache = []

        await initData()
        // ElMessage.success('已重置并重新获取最新数据');
      } catch (error) {
        console.error('重置并获取数据失败:', error)
        ElMessage.error('重置失败，请稍后重试')
      } finally {
        isLoading.value = false
      }
    }

    // getters
    const currentOntologyConfig = computed(() => {
      return ontologyConfigurations.value[0] || null
    })

    const promptListSimplified = computed(() => {
      return ontologyPrompt.value.map((option) => ({
        value: option.value,
        promptList: option.promptList?.map((p) => p.prompt) || [],
      }))
    })

    const getAllOntologyObject = computed(() => {
      return ontologyPrompt.value
    })

    const getAllOntoConfigs = computed(() => {
      return ontologyConfigurations.value
    })

    // 根据配置名称获取其中的字段
    const getConfigFields = (configName: string): ExtractFieldItem[] => {
      return (
        ontologyConfigurations.value.find((item) => item.label == configName)
          ?.extract_fields_list ?? []
      )
    }

    return {
      // state
      ontologyConfigurations,
      ontologyPrompt,
      relations,
      isLoading,

      // actions
      initData,
      updateOntologyConfiguration,
      updateOntologyPromptOptions,
      updateRelations,
      resetState,
      getConfigFields,

      // getters
      currentOntologyConfig,
      promptListSimplified,
      getAllOntologyObject,
      getAllOntoConfigs,
    }
  },
  {
    persist: {
      key: 'ontology-store',
      storage: typeof localStorage !== 'undefined' ? localStorage : undefined,
    },
  } as any,
)
