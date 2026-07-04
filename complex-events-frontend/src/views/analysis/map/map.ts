import L from 'leaflet'

// 定义地图矩形的两个斜对角（值是经纬度，[纬度，经度]），以中国—太平洋为中心，即地图的边界（世界地图是循环的，因为是球形？）
const corner1 = L.latLng(-85, -60)
const corner2 = L.latLng(85, 350)
// maxBounds 主要限制地图不可以随意被拖动的很远，限制地图拖动范围
export const maxBounds = L.latLngBounds(corner1, corner2)
// 西边界向东偏移多少是真正的边界，标点的边界，主要将标点西边界限制在大西洋上，防止有的标点绘制在南美洲的东部
const eastOffset = 30
// 标点等覆盖物的西边界
export const WestMarkerBound = maxBounds.getWest() + eastOffset

export const NORMAL_MAP_LAYER = 'map'
export const HEATMAP_LAYER = 'heatmap'

/**
 * 地图图层展示选项
 */
export const mapLayerRadioOptions = [
  {
    label: '地图',
    value: NORMAL_MAP_LAYER,
  },
  {
    label: '热力图',
    value: HEATMAP_LAYER,
  },
]

/**
 * 常规地图配置
 */
export const mapOptions = {
  center: [39.9, 105], // 中国地理中心附近
  zoom: 3,
  minZoom: 3,
  maxZoom: 18,
  zoomControl: false, // 自定义缩放控件位置
  maxBounds: maxBounds,
  subdomains: ['0', '1', '2', '3', '4', '5', '6', '7'],
  // 到达边界的时候拉动的阻力 1最大，完全稳固
  maxBoundsViscosity: 0.9,
  worldCopyJump: false,
  noWrap: false, // 允许世界复制，但限制显示范围
}
/**
 * 热力图配置
 */
export const heatLayerOptions = {
  radius: 40, // 进一步增大半径
  blur: 30, // 增加模糊度
  maxZoom: 18,
  minOpacity: 0.15, // 增加最小不透明度
  gradient: {
    0.0: 'rgba(0, 0, 255, 0)', // 透明到蓝色的过渡
    0.2: 'blue',
    0.4: 'cyan',
    0.6: 'lime',
    0.8: 'yellow',
    1.0: 'red',
  },
}
