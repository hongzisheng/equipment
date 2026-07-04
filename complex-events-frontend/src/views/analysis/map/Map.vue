<template>
  <div id="map-container" ref="mapContainer" />
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
// https://leafletjs.cn/
import * as L from 'leaflet'
import '@elfalem/leaflet-curve'
import 'leaflet.heat'
import 'leaflet/dist/leaflet.css'
import { Marker } from '@/views/analysis/map/Marker'
import {
  heatLayerOptions,
  HEATMAP_LAYER,
  mapOptions,
  NORMAL_MAP_LAYER,
} from '@/views/analysis/map/map'
import { useMapStore } from '@/stores/mapStore'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import * as d3 from 'd3'

const mapContainer = ref<HTMLElement | null>(null)
let map: L.Map | null = null
// 从环境变量获取天地图token
const token = import.meta.env.VITE_APP_TIANDITU_TOKEN
const markersLayerGroup: L.Layer = L.layerGroup()
const markerPolylinesLayerGroup: L.Layer = L.layerGroup()

onMounted(() => {
  if (!mapContainer.value) return

  // 正确初始化地图（纬度在前，经度在后）
  map = L.map(mapContainer.value, mapOptions)
  const attribution = map.attributionControl
  // setPrefix是替换默认的leaflet前缀改为自定义的logo和文字链接作为前缀
  attribution.setPrefix('')
  // addAttribution 是在前缀后添加附属信息
  attribution.addAttribution('<a href="https://leafletjs.cn/">Leaflet</a>')
  // 地形晕染
  L.tileLayer(
    `http://t{s}.tianditu.gov.cn/ter_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ter&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${token}`,
    {
      subdomains: ['0', '1', '2', '3', '4', '5', '6', '7'],
    },
  ).addTo(map)
  // 添加天地图矢量底图
  const vecLayer = L.tileLayer(
    `http://t{s}.tianditu.gov.cn/vec_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=vec&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${token}`,
    {
      attribution: '&copy; <a href="http://www.tianditu.gov.cn/">天地图</a>',
      subdomains: ['0', '1', '2', '3', '4', '5', '6', '7'],
      opacity: 0.8, // 设置透明度(0-1之间)
    },
  ).addTo(map)

  // 添加天地图标注
  const cvaLayer = L.tileLayer(
    `http://t{s}.tianditu.gov.cn/cva_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cva&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${token}`,
    {
      subdomains: ['0', '1', '2', '3', '4', '5', '6', '7'],
    },
  ).addTo(map)

  // 初始化绘制事件
  initDrawingEvents()
  markersLayerGroup.addTo(map)
  markerPolylinesLayerGroup.addTo(map)
})

onUnmounted(() => {
  if (map) {
    map.remove()
    if (mapClickHandler) map.off('click', mapClickHandler)
    if (mapDblClickHandler) map.off('dblclick', mapDblClickHandler)
    map = null
  }
})

const mapStore = useMapStore()
// 本地绘制的marker存储
let markersStoreDict = {}
watch(
  () => mapStore.markers,
  (val) => {
    // 更新marker绘制
    updateMarkers(val)
  },
)

const updateMarkers = (updateMarkers: Marker[]) => {
  updateMarkers.forEach((item: Marker) => {
    const pos = item.getLatLng()

    // ------- 圆点 Marker -------
    const circle = L.circleMarker(pos, {
      title: item.name,
      radius: 10,
      fillColor: item.color,
      weight: 0,
      opacity: 0.9,
      fillOpacity: 0.9,
      className: `marker-dynamic-glow`,
    })

    // ------- 文字 Marker -------
    const textIcon = L.divIcon({
      className: 'marker-label',
      html: `<div class="marker-label-text">${item.name}</div>`,
      iconSize: [0, 0],
      iconAnchor: [item.name.length * 10 / 2, -10],
    })

    const textMarker = L.marker(pos, { icon: textIcon, interactive: false })

    if (markersStoreDict[item.id]) {
      console.log('绘制过啦')
    } else {
      // 存储两个 marker（圆点 + 文本）
      markersStoreDict[item.id] = { circle, textMarker }
      circle.addTo(markersLayerGroup)
      textMarker.addTo(markersLayerGroup)
    }
  })

  addMarkerFilter()
}


// 增量更新地图标记，如果地图上已经有的不再重复绘制
// const updateMarkers = (updateMarkers: Marker[]) => {
//   updateMarkers.forEach((item: Marker) => {
//     const marker = L.circleMarker(item.getLatLng(), {
//       title: item.name,
//       radius: 10,
//       fillColor: item.color,
//       weight: 0,
//       opacity: 0.9,
//       fillOpacity: 0.9,
//       className: `marker-dynamic-glow`,
//     })

//     if (markersStoreDict[item.id]) {
//       console.log('绘制过啦')
//     } else {
//       // 还没有绘制过
//       markersStoreDict[item.id] = marker
//       marker.addTo(markersLayerGroup)
//     }
//   })
//   addMarkerFilter()
// }

let tmpMarkersLayerGroup = null
// 清除地图上现有的所有标记
const removeAllMarkers = () => {
  tmpMarkersLayerGroup = markersLayerGroup
  markersLayerGroup.clearLayers()
}

// 恢复地图上的标记
const recoverAllMarkers = () => {
  Object.keys(markersStoreDict).forEach((key) => {
    markersStoreDict[key].addTo(markersLayerGroup)
  })
  addMarkerFilter()
}

// 添加marker的滤镜
function addMarkerFilter() {
  nextTick(() => {
    // 地图上的marker是用svg绘制的，使用d3因为其可以选择svg
    d3.selectAll('path.marker-dynamic-glow').each(function () {
      const element = d3.select(this)
      const fillColor = element.attr('fill')
      if (fillColor) {
        element.style(
          'filter',
          `drop-shadow(0 0 10px ${fillColor}) drop-shadow(0 0 8px ${fillColor}) brightness(1.2)`,
        )
      }
    })
  })
}

// 绘制新的标记，旧的都不要了
const redrawNewMarkers = () => {
  removeAllMarkers()
  // 清空存储
  markersStoreDict = {}
  // 绘制新的
  updateMarkers(mapStore.markers)
  ElMessage.success('筛选成功')
  ElMessage("事件位置映射平均误差≤10公里")
}
const markerPolylines = computed(() => mapStore.markerPolylines)

// 绘制新的标记线
const redrawNewMarkerPolyline = () => {
  markerPolylinesLayerGroup.clearLayers()
  markerPolylines.value.forEach((line: L.Curve) => {
    line.addTo(markerPolylinesLayerGroup)
    // const arrowHead = L.polylineDecorator(line, {
    //   patterns: [
    //     {
    //       offset: '100%',   // 线段尾端
    //       repeat: 0,
    //       symbol: L.Symbol.arrowHead({
    //         pixelSize: 12,  // 箭头大小
    //         headAngle: 45,
    //         polygon: true,
    //         pathOptions: {
    //           color: 'blue',
    //           fillColor: 'blue',
    //           weight: 2,
    //           opacity: 0.9,
    //         },
    //       }),
    //     },
    //   ],
    // })
    // arrowHead.addTo(markerPolylinesLayerGroup)
  })
}
// 监听是否有新数据需要重新绘制
watch(
  () => mapStore.needUpdateAllData,
  () => {
    redrawNewMarkers()
    redrawNewMarkerPolyline()
  },
)

// 生成热力图数据，数据来源于MarkersStoreDict
const generateDataPoints = () => {
  const points: [number, number, number][] = []

  Object.keys(markersStoreDict).forEach((key) => {
    const marker: L.Marker = markersStoreDict[key]
    const latLng = marker.getLatLng() // 使用getLatLng()方法获取坐标
    points.push([latLng.lat, latLng.lng, 0.8])
  })

  return points
}

// 热力图图层
let heatLayer: L.HeatLayer | null = null
const removeHeatMap = () => {
  // 如果已有热力图图层，先移除
  if (heatLayer) {
    map.removeLayer(heatLayer)
  }
}
const drawHeatMap = () => {
  removeHeatMap()
  // 根据markers生成热力图 数据点
  const heatData = generateDataPoints()
  // 创建热力图层
  heatLayer = L.heatLayer(heatData, heatLayerOptions).addTo(map)
}
// 监听图层选择
watch(
  () => mapStore.mapLayer,
  (newVal) => {
    if (newVal === HEATMAP_LAYER) {
      removeAllMarkers()
      drawHeatMap()
    } else if (newVal === NORMAL_MAP_LAYER) {
      removeHeatMap()
      recoverAllMarkers()
    }
  },
)

// 监听是不是点击了放大和缩小
watch(
  () => mapStore.zoomInClick,
  () => {
    map.zoomIn()
  },
)
watch(
  () => mapStore.zoomOutClick,
  () => {
    map.zoomOut()
  },
)

// 多边形绘制相关变量
const { isPenSelected, coordinatesRange } = storeToRefs(mapStore)
let polygonPoints: L.Latlng[] = []
let tempPolygon: L.Polygon | null = null
let finalPolygon: L.Polygon | null = null
let polygonMarkers: L.Marker[] = []

// 开始绘制多边形
const startPolygonDrawing = () => {
  polygonPoints = []
  if (coordinatesRange.value.length > 0) {
    // 有内容的时候进行清空，防止误触发watch监听
    coordinatesRange.value = []
  }

  polygonMarkers = []

  // 清除之前的临时图形
  if (tempPolygon) {
    map.removeLayer(tempPolygon)
    tempPolygon = null
  }
  // 添加提示信息
  ElMessage.info('点击地图绘制多边形')
}

const cleanPolygon = () => {
  if (finalPolygon) {
    // 之前画过
    map.removeLayer(finalPolygon)
    finalPolygon = null
  }
}
/**
 * 暴露清除多边形函数
 */
defineExpose({ cleanPolygon })

watch(isPenSelected, (newVal) => {
  if (newVal) {
    cleanPolygon()
    startPolygonDrawing()
  } else {
    finishPolygonDrawing()
  }
})
// 监听地图点击事件
let mapClickHandler: L.LeafletEventHandlerFn | null = null
let mapDblClickHandler: L.LeafletEventHandlerFn | null = null

// 初始化绘制事件监听
const initDrawingEvents = () => {
  if (!map) return

  // 单击添加顶点
  mapClickHandler = (e: L.LeafletMouseEvent) => {
    if (!isPenSelected.value) return

    const latlng = e.latlng
    polygonPoints.push(latlng)

    // 添加标记点
    const marker = L.circleMarker(latlng, {
      draggable: true,
    }).addTo(map)
    polygonMarkers.push(marker)

    // 更新临时多边形
    if (tempPolygon) {
      map.removeLayer(tempPolygon)
    }

    if (polygonPoints.length >= 2) {
      tempPolygon = L.polygon([...polygonPoints], {
        color: 'blue',
        fillOpacity: 0.3,
      }).addTo(map)
    }
  }

  map.on('click', mapClickHandler)
  // map.on('dblclick', mapDblClickHandler)
}

// 完成多边形绘制
const finishPolygonDrawing = () => {
  if (polygonPoints.length < 3) {
    ElMessage.warning('多边形至少需要3个顶点')
    cancelPolygonDrawing()
    return
  }

  // 移除临时图形和标记
  polygonMarkers.forEach((marker) => map.removeLayer(marker))
  if (tempPolygon) {
    map.removeLayer(tempPolygon)
  }

  // 创建最终多边形
  finalPolygon = L.polygon([...polygonPoints], {
    color: 'red',
    fillOpacity: 0.4,
  })
  finalPolygon.addTo(map)
  // 确认完成的时候更新坐标范围
  coordinatesRange.value = polygonPoints

  polygonPoints = []
  polygonMarkers = []
  tempPolygon = null

  ElMessage.success('多边形绘制完成')
}

// 取消绘制
const cancelPolygonDrawing = () => {
  // 清除所有临时图形
  polygonMarkers.forEach((marker) => map.removeLayer(marker))
  if (tempPolygon) {
    map.removeLayer(tempPolygon)
  }

  isPenSelected.value = false
  polygonPoints = []
  polygonMarkers = []
  tempPolygon = null
}
</script>

<style>
#map-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.marker-label-text {
  position: relative;
  top: 10px;
  transform: translateX(-50%);

  left: 50%;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 600;
  color: #e59396;
  text-align: center;
  text-shadow: 0 0 3px #ffffff;
  pointer-events: none;
}


.grayscale-layer img {
  filter: grayscale(100%) opacity(0.8);
}
</style>
