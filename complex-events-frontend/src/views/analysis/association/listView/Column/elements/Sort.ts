import { FunctionalComponent, h } from 'vue'
import { ElIcon } from 'element-plus'
import { CaretBottom, CaretTop } from '@element-plus/icons-vue'
import linkDefaultSvg from '@/icons/sortIcons/link_default.svg'
import linkAscendSvg from '@/icons/sortIcons/link_ascend.svg'
import linkDescendSvg from '@/icons/sortIcons/link_descend.svg'

export const SortMethods = ['default', 'descending', 'ascending']

const DefaultSortIcon: FunctionalComponent = () => {
  return h('img', {
    src: linkDefaultSvg,
    alt: '连接强度默认排序',
  })
}

const AscendSortIcon: FunctionalComponent = () => {
  return h('img', {
    src: linkAscendSvg,
    alt: '连接强度升序排序',
  })
}

const DescendSortIcon: FunctionalComponent = () => {
  return h('img', {
    src: linkDescendSvg,
    alt: '连接强度降序排序',
  })
}

export function SortIcon(sortType: number) {
  switch (sortType) {
    case 0:
      return h(ElIcon, {}, () => h(DefaultSortIcon))
    case 1:
      return h(ElIcon, {}, () => h(DescendSortIcon))
    case 2:
      return h(ElIcon, {}, () => h(AscendSortIcon))
  }
}
