import { h } from 'vue'
import { nodeLegendMap } from '@/views/ontology/graphManage/graph'
import { ElTag } from 'element-plus'

const nodeTypeTag = (group: string, content: string = null) => {
  try {
    const groupColor = nodeLegendMap[group].color.background
    return h(
      'div',
      {
        color: groupColor,
        effect: 'dark',
        type: 'info',
        'disable-transitions': true,
        style: {
          display: 'flex',
          alignItems: 'top',
          width: '90%',
          // 高度要能显示所有内容
          'min-height': '1em',
          height: 'auto',
          // 支持换行显示
          whiteSpace: 'pre-wrap',
        },
      },
      [
        h('img', {
          src: `/graphIcons/${group.toLowerCase()}/unselected.svg`,
          alt: `${group}的icon`,
          style: {
            height: '1em',
            width:'1em',
            marginRight:'4px',
          }
        }),
        h('span', {}, content??group),
      ],
    )
  } catch (e) {
    console.error(group)
  }
}
export default nodeTypeTag
