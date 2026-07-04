import { ZoomIn, ZoomOut, RefreshRight, Close, Menu, Help, EditPen } from '@element-plus/icons-vue'
import { computed, h } from 'vue'
import { ElButton, ElButtonGroup, ElCheckboxButton, ElIcon } from 'element-plus'
import { useMapStore } from '@/stores/mapStore'

interface InteractiveOption {
  label: string
  value: string
  icon: string
  // 这个选项的类型，是单选按钮，还是选中状态？
  type: string
}

/**
 * 地图的交互操作按钮的选项，比如放大缩小等
 */
export const mapInteractiveOption: InteractiveOption[] = [
  {
    label: '条目',
    icon: 'items',
    value: 'items',
    type: 'button',
  },
  {
    label: '放大',
    icon: 'zoomIn',
    value: 'zoomIn',
    type: 'button',
  },
  {
    label: '缩小',
    icon: 'zoomOut',
    value: 'zoomOut',
    type: 'button',
  },
  {
    label: '框选',
    icon: 'editPen',
    value: 'editPen',
    type: 'checkboxButton',
  },
  {
    label: '重置',
    icon: 'reset',
    value: 'reset',
    type: 'button',
  },

  {
    label: '关闭',
    icon: 'close',
    value: 'close',
    type: 'button',
  },
]

/**
 * 按钮中的内容插槽
 * @param iconName
 */
export const mapInteractiveRadioButtonSlot = (iconName: string) => {
  switch (iconName) {
    case 'zoomIn':
      return h(ElIcon, {}, { default: () => h(ZoomIn) })
    case 'zoomOut':
      return h(ElIcon, {}, { default: () => h(ZoomOut) })
    case 'items':
      return h(ElIcon, {}, { default: () => h(Menu) })
    case 'reset':
      return h(ElIcon, {}, { default: () => h(RefreshRight) })
    case 'close':
      return h(ElIcon, {}, { default: () => h(Close) })
    case 'editPen':
      return h(ElIcon, {}, { default: () => h(EditPen) })
    default:
      return h(ElIcon, {}, { default: () => h(Help) })
  }
}

/**
 * 交互按钮组group
 * 根据按钮的不同交互逻辑形成不同的组件
 * 比如单选功能的放大缩小是button类型
 * 比如框选功能的选中和未选中是checkbox类型
 */
export const mapInteractiveRadioButtons = () => {
  const buttonsVNodes = []

  mapInteractiveOption.forEach((opt) => {
    const buttonClickEvent = buttonClickEventFactory(opt.value);
    // 如果是单选的按钮
    if (opt.type === 'button') {
      buttonsVNodes.push(
        h(
          ElButton,
          {
            onClick: () => {
              // 不同按钮的点击事件，根据opt.value传入一个工厂函数中得到
              buttonClickEvent()
            },
          },
          { default: () => mapInteractiveRadioButtonSlot(opt.icon) },
        ),
      )
    } else if (opt.type === 'checkboxButton') {
      // 如果是需要有选中状态的checkbox
      // 使用普通按钮模拟checkbox行为
      buttonsVNodes.push(
        h(
          ElButton,
          {
            onClick: () => {
              buttonClickEvent()
            },
            type: isPenSelected.value ? 'primary' : 'default', // 根据状态设置按钮类型
          },
          { default: () => mapInteractiveRadioButtonSlot(opt.icon) },
        ),
      )
    }
  })
  return h(
    ElButtonGroup,
    {},
    {
      default: () => buttonsVNodes,
    },
  )
}

/**
 * 工厂函数，根据传递值返回点击事件
 * @param optValue
 */
const buttonClickEventFactory = (optValue: string) => {
  switch (optValue) {
    case 'zoomIn':
      return zoomIn
    case 'zoomOut':
      return zoomOut
    case 'items':
      return itemsClick
    case 'editPen':
      return penSelected
    case 'reset':
      return reset
    case 'close':
      return close
    default:
      return () => {
        console.log('点击事件未知')
      }
  }
}

const zoomIn = () => {
  console.log('点击了放大按钮')
  mapStore.zoomInClick = !mapStore.zoomInClick;
}

const zoomOut = () => {
  console.log('点击了缩小按钮')
  mapStore.zoomOutClick = !mapStore.zoomOutClick;
}

const itemsClick = () => {
  console.log('点击了items按钮')
}

const mapStore = useMapStore()
// 框选是否选中，从mapStore中获取统一的状态管理
const isPenSelected = computed(() => {
  return mapStore.isPenSelected
})
// 当点击框选的时候触发的事件
const penSelected = () => {
  mapStore.isPenSelected = !mapStore.isPenSelected
}

const reset = () => {
  const mapRef = mapStore.mapRef;
  mapRef.cleanPolygon()
  console.log('clicked 重置')
  mapStore.$reset()
}

const close = () => {
  console.log('clicked 关闭')
}
