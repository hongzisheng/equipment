// 纬度在前，经度在后，为适应leaflet坐标绘制
import { WestMarkerBound } from '@/views/analysis/map/map'

// 地理坐标点
export interface Coordinate {
  center: [number, number] // [经度, 纬度]
  centroid: [number, number]   //簇的中心点坐标
  cluster:number   //所属簇
  id: string
  place_name: string
}

export class Marker {
  // ID标识marker的唯一性
  id: string
  // 颜色
  color: string
  // title
  name: string
  // 纬度
  latitude: number
  // 经度
  longitude: number

  constructor(id: string, name: string, latitude: number, longitude: number, color: string) {
    this.id = id
    this.name = name
    this.latitude = latitude
    if (longitude < WestMarkerBound) {
      // 小于西边界，地图边界，画到地图右边来
      this.longitude = longitude + 360
    } else {
      this.longitude = longitude
    }
    this.color = color
  }

  // 纬度经度
  getLatLng(): Coordinate['center'] {
    return [this.latitude, this.longitude]
  }

  /**
   * 从地理编码接口返回的文档中提取有用的信息，形成一个新的Marker对象
   * @param item
   */
  static parse(item: Coordinate, color: string) {
    try {
      return new Marker(item.id, item.place_name, item.center[1], item.center[0], color)
    } catch (e) {
      console.log('Marker解析出错:', item, e)
      return null
    }
  }
}
