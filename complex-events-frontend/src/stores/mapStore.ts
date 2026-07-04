import { defineStore } from 'pinia'
import { computed, ComputedRef, ref, watch } from 'vue'
import { Coordinate, Marker } from '@/views/analysis/map/Marker'
import dataApi, { FilterObject } from '@/api/dataApi'
import { ExtractResultAction, formattedExtractResult, Person } from '@/views/ontology/extract/index'
import { ElMessage } from 'element-plus'
import * as L from 'leaflet'
import Map from '@/views/analysis/map/Map.vue'
import { OntologySystemData } from '@/views/ontology/ontologySystem'
import '@elfalem/leaflet-curve'

interface Option {
  value: string
  label: string
  disabled?: boolean
}

type MapRef = InstanceType<typeof Map>

interface FilterResultDoc {
  actions: ExtractResultAction[]
  eventName: string
  eventType: string
  keywords: string
  triggerWords: string
  id: string
  mainCoordinate: Coordinate
  organizations: string // 多个组织用逗号分隔的字符串
  person: Person[]
  places: string // 多个地点用逗号分隔的字符串
  relatedCoordinates: Coordinate[]
  time: string // ISO 日期字符串格式，如 "2024-11"
}

interface EventCoordinate {
  // 同一类事件使用同一种颜色
  color: string
  coordinate: Coordinate
}

/**
 * 在进行地图展示的时候用到的相关的状态管理
 * See @/views/analysis/map
 */
export const useMapStore = defineStore('map', () => {
  const loading = ref(false)
  const mapRef = ref(null)
  const setMapRef = (_mapRef: MapRef) => {
    mapRef.value = _mapRef
  }
  // 地图上要绘制的所有的items的坐标，可能有重复的
  const coordinates = ref<EventCoordinate[]>([])
  // 地图上要绘制markers
  const markers = computed<Marker[]>(() => {
    const result: Marker[] = []
    coordinates.value.forEach((item) => {
      if (Marker.parse(item.coordinate, item.color)) {
        // 可以被parse
        result.push(Marker.parse(item.coordinate, item.color))
      }
    })
    return result
  })
  const colors = [
    '#4B4B4B',
    '#708090',
    '#556B2F',
    '#9e4c14',
    '#2F4F4F',
    '#800000',
    '#483D8B',
    '#3CB371',
    '#4682B4',
    '#DAA520',
  ]

  // 根据索引获取颜色
  function getColor(index: number): string {
    return index >= colors.length ? colors[index % colors.length] : colors[index]
  }

  // 计算背景颜色的亮度，决定使用白色还是黑色字体
  const getContrastColor = (hexColor: string): string => {
    if (hexColor==undefined){
      return '#000000'
    }
    try {
      // 移除 # 符号
      const hex = hexColor.replace('#', '')
      // 计算RGB值
      const r = parseInt(hex.slice(0, 2), 16)
      const g = parseInt(hex.slice(2, 4), 16)
      const b = parseInt(hex.slice(4, 6), 16)

      // 计算亮度 (使用相对亮度公式)
      const brightness = (r * 299 + g * 587 + b * 114) / 1000

      // 如果亮度大于128，使用黑色字体，否则使用白色字体
      return brightness > 128 ? '#000000' : '#FFFFFF'
    } catch (e) {
      // console.trace(e, 'color', hexColor)
      return '#000000'
    }
  }
  const getContrastColorByIndex = (index: number) => {
    return getContrastColor(getColor(index))
  }

  // 标点之间的连线
  const markerPolylines = ref<L.Polyline[]>([])

  function addMarkerBezierCurve(markerStart: Marker, markerEnd: Marker) {
    if (markerStart && markerEnd) {
      const start = markerStart.getLatLng()
      const end = markerEnd.getLatLng()

      // 计算中点
      const midLat = (start[0] + end[0]) / 2
      const midLng = (start[1] + end[1]) / 2

      // 计算连接线段的方向向量
      const deltaLat = end[0] - start[0]
      const deltaLng = end[1] - start[1]

      // 计算垂直方向向量（旋转90度）
      // 垂直向量: (-deltaLng, deltaLat)
      const perpendicularLat = -deltaLng
      const perpendicularLng = deltaLat

      // 归一化垂直向量
      const length = Math.sqrt(
        perpendicularLat * perpendicularLat + perpendicularLng * perpendicularLng,
      )
      const unitPerpendicularLat = perpendicularLat / length
      const unitPerpendicularLng = perpendicularLng / length

      // 设置偏移量
      const offset = 10 // 根据需要调整此值

      // 控制点位于垂直平分线上，距离中点offset
      const ctrl1 = L.latLng(
        midLat + unitPerpendicularLat * offset,
        midLng + unitPerpendicularLng * offset,
      )

      // 使用Leaflet.curve绘制二次贝塞尔曲线
      const curve = L.curve(
        ['M', [start[0], start[1]], 'Q', [ctrl1.lat, ctrl1.lng], [end[0], end[1]]],
        {
          color: 'skyblue',
          weight: 4,
          opacity: 0.7,
        }
      )

      markerPolylines.value.push(curve)
    }
  }

  // 是否更新所有的数据，包括标记，地点，范围等，一般用于筛选
  const needUpdateAllData = ref(false)
  const triggerUpdateAllData = () => {
    needUpdateAllData.value = !needUpdateAllData.value
  }
  const searchText = ref('')
  // 选择展示的地图图层
  const mapLayer = ref<string>('map')
  const eventsListTableData = ref<OntologySystemData[]>([])

  // 最终选中的
  const placeSelectedValue = ref<string>(null)
  const placesSelectedOptions = computed<Option[]>(() => {
    const options: Option[] = []
    const uniquePlaces = new Set<string>() // 使用Set避免重复

    eventsListTableData.value.forEach((data) => {
      if (data.place) {
        // 添加空值检查
        data.place.split(',').forEach((p: string) => {
          const place = p.trim() // 去除空格
          if (place && !uniquePlaces.has(place)) {
            uniquePlaces.add(place)
            options.push({
              label: place,
              value: place,
            })
          }
        })
      }
    })

    return options
  })

  // 选择的日期范围
  const dateRangePicker = ref<[string, string]>(null)
  // 地图上框选的范围
  const coordinatesRange = ref<L.LatLng[]>([])
  // 现在的页面
  const currentPage = ref<number>(1)
  // 不分页，获取全部数据
  const unlimitedFlag = ref(false)
  const setUnlimitedFlag = (newFlag: boolean) => {
    unlimitedFlag.value = newFlag
  }

  function setCurrentPage(page: number) {
    currentPage.value = page
  }

  const total = ref<number>(0)
  const totalPages = computed(() => {
    return Math.ceil(total.value / 10)
  })

  // 构造过滤对象
  const filterObject: ComputedRef<FilterObject> = computed(() => {
    return {
      keyword: searchText.value ?? null,
      place: placeSelectedValue.value ?? null,
      startDate: dateRangePicker.value?.[0] ?? null,
      endDate: dateRangePicker.value?.[1] ?? null,
      coordinatesRange: coordinatesRange.value ?? null,
      // currentPage代表需要分页 ,从 limit 到 limit+10
      limit: !unlimitedFlag.value ? (currentPage.value - 1) * 10 : null,
    }
  })
  const filter = async () => {
    eventsListTableData.value = []
    coordinates.value = []
    markerPolylines.value = []
    loading.value = true
    await dataApi
      .filter(filterObject.value)
      .then((res: { data: { list: FilterResultDoc[]; total: number } }) => {
        total.value = res.data.total
        if (res.data.list && res.data.list.length > 0) {
          let index = 0
          res.data.list.forEach((doc: FilterResultDoc) => {
            const color = getColor(index++)
            eventsListTableData.value.push(formattedExtractResult(doc))
            if (doc.mainCoordinate)
              coordinates.value.push({
                color: color,
                coordinate: doc.mainCoordinate,
              })
            else console.log('坐标为空')

            // if (doc.relatedCoordinates) {
            //   //   addMarkerPolyline(Marker.parse(doc.mainCoordinate), Marker.parse(doc.relatedCoordinates[0]))
            //   doc.relatedCoordinates.forEach((coordinate) => {
            //     coordinates.value.push({
            //       color: color,
            //       coordinate: coordinate,
            //     })
            //   })
            // }
          })
          for (let i = 1; i < coordinates.value.length - 1 && i<5; i++) {
            try {
              addMarkerBezierCurve(
                Marker.parse(coordinates.value[i - 1].coordinate, coordinates.value[i - 1].color),
                Marker.parse(coordinates.value[i].coordinate, coordinates.value[i].color),
              )
            } catch (e) { }
          }
        } else {
          ElMessage.warning('没有找到数据')
        }
      })
      .finally(() => {
        // 数据更新完成了，可以准备更新了
        triggerUpdateAllData()
        loading.value = false
      })
  }

  watch(
    filterObject,
    () => {
      if (!unlimitedFlag.value) {
        // 无限制的时候需要手动执行，有限制的时候监听自动执行
        filter()
      }
    },
    {
      deep: true,
    },
  )
  // 地图交互按钮选择
  const interactOptionSelected = ref<string>(null)

  // 地图是否启动框选
  const isPenSelected = ref<boolean>(false)

  // 放大监听的目标，不管之前是true,false,修改的时候取反，监听的时候只要变了就触发
  const zoomInClick = ref<boolean>(false)
  // 缩小
  const zoomOutClick = ref<boolean>(false)

  const $reset = () => {
    searchText.value = ''
    placeSelectedValue.value = null
    dateRangePicker.value = null
    coordinatesRange.value = []
  }

  return {
    loading,
    mapRef,
    setMapRef,
    markers,
    markerPolylines,
    eventsListTableData,
    coordinates,
    mapLayer,
    searchText,
    placeSelectedValue,
    placesSelectedOptions,
    dateRangePicker,
    interactOptionSelected,
    isPenSelected,
    zoomInClick,
    zoomOutClick,
    needUpdateAllData,
    triggerUpdateAllData,
    coordinatesRange,
    filterObject,
    filter,
    setCurrentPage,
    setUnlimitedFlag,
    getColor,
    getContrastColor,
    getContrastColorByIndex,
    total,
    totalPages,
    $reset,
  }
})
