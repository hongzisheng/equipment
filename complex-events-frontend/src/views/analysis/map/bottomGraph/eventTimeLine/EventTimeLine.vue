<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, useTemplateRef, watch } from 'vue'
import dataApi from '@/api/dataApi'
import { useMapStore } from '@/stores/mapStore'
import * as d3 from 'd3'
import { ElMessageBox, ElMessage } from 'element-plus';
import ResizeObserveChartContainer from '@/commomComponents/ResizeObserveChartContainer.vue'

// 定义数据类型
interface EventPoint {
  time: Date
  name: string
}

const timelineRef = useTemplateRef('timelineRef')
const mapStore = useMapStore()
const eventsList = computed(() => mapStore.eventsListTableData)

//获取数据，并进行一定的处理
const data = computed(() => {
  return eventsList.value.map((eventRow, index) => {
    let time = eventRow.time
    const name = eventRow.eventName
    const action = eventRow.action
    const reportId = eventRow.reportId
    // 如果只有年份，补1月1日
    if (time.length === 4) {
      time += '-01-01'
    }
    // 如果只有月份，补1
    if (time.length === 7) {
      time += '-01'
    }
    return {
      index: index,
      time: new Date(time),
      name: name, //.slice(0, 2),
      action: action,
      reportId: reportId
    }
  })
})

let chart

const options = {
  formatAxis: (axis) => {
    // 设置时间格式化函数
    const timeFormat = d3.timeFormat('%Y-%m-%d') // 年-月-日格式
    axis.tickFormat(timeFormat)
    // 获取默认刻度值并过滤重复项
    const originalTickValues = axis.scale().ticks()
    const seenDates = new Set()
    const uniqueTickValues = originalTickValues.filter((tick) => {
      const dateStr = timeFormat(tick)
      if (seenDates.has(dateStr)) {
        return false
      }
      seenDates.add(dateStr)
      return true
    })

    axis.tickValues(uniqueTickValues)
    return axis
  },

  //获取文本颜色，觉得黑/白
  labelTextColor: function (d) {
    return mapStore.getContrastColorByIndex(d.index)
  },
  //根据index获取背景颜色
  labelBgColor: function (d) {
    return mapStore.getColor(d.index)
  },

  dotColor: (d) => {
    return mapStore.getColor(d.index)
  },
  linkColor: function (d) {
    return mapStore.getColor(d.index)
  },
  // 层与层之间的gap
  layerGap: 10,
  textFn: function (d) {
    return d.name.length > 10 ? d.name.slice(0, 10) + '...' : d.name
  },
}
// 获取容器的宽高
const containerWidth = ref(0)
const containerHeight = ref(0)

function textLenLimit(text: string, maxLen: number = 7): string {
  return text.length <= maxLen ? text : text.slice(0, maxLen) + '...';
}

function draw() {
  if (!timelineRef.value || data.value.length === 0) return;

  const container = d3.select(timelineRef.value)
    .style("overflow-x", "auto")
    .style("overflow-y", "hidden");

  container.selectAll("*").remove();

  const margin = { top: 1, right: 40, bottom: 50, left: 40 };
  const outerWidth = Math.max(1200, container.node()!.getBoundingClientRect().width);
  const width = outerWidth - margin.left - margin.right;
  const height = containerHeight.value - margin.top - margin.bottom;
  const timeAxisY = height;

  const svgEl = container.append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom);

  const svg = svgEl.append("g")
    .attr("transform", `translate(${margin.left}, ${margin.top})`);

  // Tooltip layer
  const tooltipLayer = svgEl.append('g')
    .attr('class', 'tooltip-layer')
    .style('pointer-events', 'none')
    .style('opacity', 0);

  const tooltipBg = tooltipLayer.append('rect')
    .attr('fill', 'rgba(0,0,0,0.75)')
    .attr('rx', 4).attr('ry', 4);

  const tooltipText = tooltipLayer.append('text')
    .attr('x', 6).attr('y', 14)
    .attr('fill', '#fff')
    .style('font-size', '11px');

  tooltipLayer.raise();

  // 时间比例尺
  const [minTime, maxTime] = d3.extent(data.value, d => d.time) as [Date, Date];
  const x = d3.scaleTime()
    .domain([d3.timeMonth.offset(minTime, -1), d3.timeMonth.offset(maxTime, 1)])
    .range([50, width - 50]);

  // 时间轴线
  svg.append('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', timeAxisY).attr('y2', timeAxisY)
    .attr('stroke', '#aaa').attr('stroke-width', 2);

  // 构造节点
  const labelWidth = 110;
  const labelHeight = 30;
  const minGap = 15;
  const nodes = data.value
    .map((d, i) => ({
      ...d,
      name: textLenLimit(d.name),
      reportId: d.reportId,
      originName: d.name,
      originalX: x(d.time),
      x: x(d.time),
      y: timeAxisY - 60,
      width: labelWidth,
      height: labelHeight,
      layer: 0
    }))
    .sort((a, b) => a.originalX - b.originalX);

  layoutLabels(nodes, labelWidth, labelHeight * 0.4, minGap, height * 0.6, 30, width - 30, timeAxisY - 10);

  // 连线
  svg.selectAll('.link').data(nodes).enter().append('path')
    .attr('class', 'link')
    .attr('fill', 'none')
    .attr('stroke', d => mapStore.getColor(d.index))
    .attr('stroke-width', 1.5)
    .attr('opacity', 0.8)
    .attr('d', d => curvePath(d, timeAxisY, labelHeight));

  // 时间点
  svg.selectAll('.dot').data(nodes).enter().append('circle')
    .attr('class', 'dot')
    .attr('cx', d => d.originalX)
    .attr('cy', timeAxisY)
    .attr('r', 4)
    .attr('fill', d => mapStore.getColor(d.index));

  // 标签组
  const labelGroup = svg.selectAll('.label').data(nodes).enter().append('g')
    .attr('class', 'label')
    .attr('transform', d => `translate(${d.x - labelWidth / 2}, ${d.y})`)
    .style('cursor', 'pointer');

  labelGroup.append('rect')
    .attr('width', labelWidth)
    .attr('height', labelHeight)
    .attr('rx', 6)
    .attr('fill', d => mapStore.getColor(d.index))
    .attr('stroke', '#333')
    .attr('stroke-width', 1);

  labelGroup.append('text')
    .attr('x', labelWidth / 2)
    .attr('y', labelHeight / 2)
    .attr('text-anchor', 'middle')
    .attr('fill', d => mapStore.getContrastColorByIndex(d.index))
    .style('font-size', '12px')
    .style('pointer-events', 'none')
    .text(d => d.name.length > 14 ? d.name.slice(0, 14) + '...' : d.name);

  labelGroup
    .on('mousemove', function (event, d) {
      tooltipText.text(d.originName);

      // 获取文本尺寸
      const bbox = tooltipText.node()!.getBBox();
      tooltipBg
        .attr('width', bbox.width + 12)
        .attr('height', bbox.height + 8);

      const [px, py] = d3.pointer(event, svg.node());
      tooltipLayer
        .attr('transform', `translate(${px + 10}, ${py - 25})`)
        .style('opacity', 1)
        .raise();
    })
    .on('mouseleave', () => {
      tooltipLayer.style('opacity', 0);
    });

  labelGroup.append('circle')
    .attr('cx', 8)
    .attr('cy', 8)
    .attr('r', 3)
    .attr('fill', d => d.layer === 0 ? '#0f0' : '#f00')
    .style('opacity', 0.5);

  labelGroup.on('click', function (event, d) {

    const colorList = ["#F8F9FA", "#F0F8FF", "#F0FFF0", "#FFFAF0", "#F8F8FF", "#FFF8F0", "#F0FFFF", "#FFFBF0", "#F8FFF8", "#FAF8FF", "#FFF0F5", "#F0F8F0", "#FFFAF8", "#F0F4F8", "#F8F0FF"];
    const originLabel = d.action.split(',\n');
    const timelinePadding = 80;
    const labelSpacing = 20; // 标签间固定间距
    const detailTitleList = originLabel.map((item, index) => ({
      detail: item,
      color: colorList[index % colorList.length],
      width: item.length * 12 + 20,
    }));
    const container = d3.select(timelineRef.value);
    const oldSvg = container.select('svg');
    const totalWidth = detailTitleList.reduce((sum, d) => sum + d.width, 0) + labelSpacing * (detailTitleList.length - 1);
    const containerHeight = timelineRef.value.clientHeight;
    const containerWidth = totalWidth + timelinePadding * 2;
    // 旧 SVG 左移
    oldSvg
      .style('position', 'absolute')
      .style('left', '0px')
      .transition()
      .duration(800)
      .ease(d3.easeCubicInOut)
      .styleTween('left', () => d3.interpolate('0px', `-${containerWidth + 50}px`))
      .on('end', () => oldSvg.style('display', 'none'));


    const newSvg = svg.append('svg')
      .attr('class', 'detail')
      .attr('width', containerWidth)
      .attr('height', containerHeight)
      .style('position', 'absolute')
      .style('top', '0px')
      .style('left', `${containerWidth}px`)
      .style('background-color', '#f9f9f9')
      .style('box-shadow', '0 0 10px rgba(0,0,0,0.1)');

    const labelSvg = renderDetailSvg(d, true);
    // timeline 直线
    d3.select(timelineRef.value).selectAll('.detail-add-button').remove();

    renderAddButton(d, containerHeight);

  });


  svg.append('g')
    .attr('transform', `translate(0,${timeAxisY})`)
    .call(d3.axisBottom(x)
      .ticks(d3.timeMonth.every(1))
      .tickFormat(d3.timeFormat('%Y-%m') as any))
    .selectAll('text')
    .style('font-size', '11px')
    .style('fill', '#666');

  addHoverEffect(labelGroup, svg, nodes, timeAxisY);
  addGlowFilter(svg);
}

function renderDetailSvg(d: any, move = false) {
  const colorList = ["#F8F9FA", "#F0F8FF", "#F0FFF0", "#FFFAF0", "#F8F8FF", "#FFF8F0", "#F0FFFF", "#FFFBF0", "#F8FFF8", "#FAF8FF"];
  const originLabel = d.action.split(',\n');
  const labelHeight = 30;
  const timelinePadding = 80;
  const labelSpacing = 20;

  const detailTitleList = originLabel.map((item, index) => ({
    detail: item,
    color: colorList[index % colorList.length],
    width: item.length * 12 + 20,
  }));

  const lableLength = detailTitleList.length;
  const container = d3.select(timelineRef.value);
  const containerHeight = timelineRef.value.clientHeight;
  const totalWidth = detailTitleList.reduce((sum, d) => sum + d.width, 0) + labelSpacing * (lableLength - 1);
  const containerWidth = totalWidth + timelinePadding * 2;

  // 1️⃣ 删除旧的 detail-svg（防止重复）
  container.selectAll('svg.detail-svg').remove();

  // 2️⃣ 判断是否需要动画进入
  const initialLeft = move ? `${containerWidth + 50}px` : '0px';

  const newSvg = container.append('svg')
    .attr('class', 'detail-svg')
    .attr('width', containerWidth)
    .attr('height', containerHeight)
    .style('position', 'absolute')
    .style('top', '0px')
    .style('left', initialLeft)
    .style('background-color', '#f9f9f9')
    .style('box-shadow', '0 0 10px rgba(0,0,0,0.1)');

  // 3️⃣ 绘制内容（先静态渲染完毕）
  const labelsY = containerHeight * 0.3;
  let currentX = timelinePadding;

  const labelGroup = newSvg.selectAll('.detail-label')
    .data(detailTitleList)
    .enter()
    .append('g')
    .attr('class', 'detail-label')
    .attr('transform', (_, i) => {
      const x = currentX;
      currentX += detailTitleList[i].width + labelSpacing;
      return `translate(${x}, ${labelsY})`;
    })
    .style('cursor', 'pointer');

  labelGroup.append('rect')
    .attr('width', d => d.width)
    .attr('height', labelHeight)
    .attr('rx', 5)
    .attr('fill', d => d.color)
    .attr('stroke', '#D3D3D3');

  labelGroup.append('text')
    .attr('x', d => d.width / 2)
    .attr('y', labelHeight / 2)
    .attr('text-anchor', 'middle')
    .attr('dominant-baseline', 'middle')
    .attr('fill', '#333')
    .style('font-size', '12px')
    .text(d => d.detail);

  const timelineY = containerHeight * 0.7;
  newSvg.append('line')
    .attr('x1', timelinePadding)
    .attr('x2', timelinePadding + totalWidth)
    .attr('y1', timelineY)
    .attr('y2', timelineY)
    .attr('stroke', '#999')
    .attr('stroke-width', 2);

  newSvg.selectAll('.timeline-dot')
    .data(detailTitleList)
    .enter()
    .append('circle')
    .attr('class', 'timeline-dot')
    .attr('cx', (_, i) => {
      let cx = timelinePadding;
      for (let j = 0; j <= i - 1; j++) {
        cx += detailTitleList[j].width + labelSpacing;
      }
      cx += detailTitleList[i].width / 2;
      return cx;
    })
    .attr('cy', timelineY)
    .attr('r', 6)
    .attr('fill', '#D3D3D3');

  // 4️⃣ 添加返回箭头
  const arrowWidth = 30, arrowHeight = 30;
  const arrow = newSvg.append('g')
    .attr('class', 'back-arrow')
    .style('cursor', 'pointer')
    .attr('transform', `translate(20, 20)`);

  arrow.append('text')
    .attr('x', arrowWidth / 2 - 20)
    .attr('y', arrowHeight * 2)
    .attr('text-anchor', 'middle')
    .attr('dominant-baseline', 'middle')
    .attr('fill', '#D3D3D3')
    .style('font-size', '30px')
    .text('<');

  // 5️⃣ 如果需要动画，执行滑入
  if (move) {
    newSvg.transition()
      .duration(800)
      .ease(d3.easeCubicInOut)
      .styleTween('left', () => d3.interpolate(`${containerWidth + 50}px`, '0px'));
  }

  // 6️⃣ 返回按钮动画
  arrow.on('click', () => {
    const cw = +newSvg.attr('width');
    newSvg.transition()
      .duration(800)
      .ease(d3.easeCubicInOut)
      .styleTween('left', () => d3.interpolate('0px', `${cw + 50}px`))
      .on('end', () => {
        newSvg.remove();
        d3.select(timelineRef.value).selectAll('.detail-add-button').remove();
      });


    const oldSvg = d3.select(timelineRef.value).select('svg:not(.detail-svg)');
    oldSvg
      .style('display', 'block')
      .style('position', 'absolute')
      .style('left', `-${cw + 50}px`)
      .transition()
      .duration(800)
      .ease(d3.easeCubicInOut)
      .styleTween('left', () => d3.interpolate(`-${cw + 50}px`, '0px'));
  });

  if (!move) {
    renderAddButton(d, containerHeight);
  }
  return newSvg;
}

function renderAddButton(d: any, containerHeight: number) {
  d3.select(timelineRef.value).selectAll('.detail-add-button').remove();

  const fixedButton = d3.select(timelineRef.value)
    .append('button')
    .attr('class', 'detail-add-button')
    .text('新增')
    .style('position', 'fixed')
    .style('bottom', containerHeight)
    .style('left', '30px')
    .style('padding', '8px 15px')
    .style('background-color', '#409EFF')
    .style('color', '#fff')
    .style('border', 'none')
    .style('border-radius', '5px')
    .style('cursor', 'pointer')
    .on('click', () => {
      ElMessageBox({
        title: '新增事件',
        message: `
          <div style="display:flex;flex-direction:column;gap:10px">
            <select id="actionPosition" style="width:100%;padding:5px"></select>
            <input id="actionName" placeholder="事件名" style="width:100%;padding:5px"/>
            <input id="relatedPerson" placeholder="关联人员" style="width:100%;padding:5px"/>
            <input id="relatedOrganization" placeholder="关联组织" style="width:100%;padding:5px"/>
            <input id="relatedPlace" placeholder="关联地址" style="width:100%;padding:5px"/>
          </div>
        `,
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        dangerouslyUseHTMLString: true,
      }).then(() => {
        const actionPosition = document.getElementById('actionPosition').value;
        const actionName = document.getElementById('actionName').value.trim();
        const relatedPerson = document.getElementById('relatedPerson').value.trim();
        const relatedOrganization = document.getElementById('relatedOrganization').value.trim();
        const relatedPlace = document.getElementById('relatedPlace').value.trim();

        if (!actionName) {
          ElMessage.error('事件名不能为空');
          return;
        }

        dataApi.postAddAction(d.reportId, actionPosition, {
          actionName,
          relatedPerson,
          relatedOrganization,
          relatedPlace
        }).then((response) => {
          if (response.code === 20000) {
            ElMessage.success('新增成功！');
            const newActionStr = actionName;
            const currentActions = d.action.split(',\n');
            currentActions.splice(actionPosition, 0, newActionStr);
            d.action = currentActions.join(',\n');

            // 🧹 清除旧 detail 画布并重绘（无动画）
            d3.select(timelineRef.value).selectAll('svg.detail-svg').remove();
            renderDetailSvg(d, false);
          } else {
            ElMessage.error('新增失败：' + (response.message || '未知错误'));
          }
        }).catch((err) => {
          console.error('新增请求失败:', err);
          ElMessage.error('新增请求失败，请查看控制台');
        });
      });

      // 延迟填充 select
      setTimeout(() => {
        const labelLength = d.action.split(',\n').length;
        const select = document.getElementById('actionPosition');
        if (!select) return;

        select.innerHTML = '';
        for (let i = 0; i <= labelLength; i++) {
          const option = document.createElement('option');
          option.value = i.toString();
          option.textContent = i.toString();
          select.appendChild(option);
        }
      }, 0);
    });

  return fixedButton;
}

// 辅助函数
function layoutLabels(
  nodes, labelWidth, labelHeight, minGap, maxHeight, minX, maxX, timeAxisY
) {
  const layerHeight = labelHeight + minGap;
  const effectiveHeight = maxHeight;  // 或者 maxHeight - bottomPadding
  const baseY = timeAxisY - effectiveHeight + 10;  // 给 10px 顶部缓冲

  const layerCount = Math.max(1, Math.floor(effectiveHeight / layerHeight));
  const layersY = Array.from({ length: layerCount }, (_, i) => baseY + i * layerHeight);

  nodes.forEach((d, i) => {
    d.layer = i % layerCount;
    d.y = layersY[d.layer];
    d.vx = d.vy = 0;
  });

  const simulation = d3.forceSimulation(nodes)
    .force('x', d3.forceX(d => d.originalX).strength(0.2))
    .force('y', d3.forceY(d => d.y).strength(0.5))
    .force('collide', d3.forceCollide(labelWidth / 2 + minGap))
    .force('boundary', () => {
      nodes.forEach(d => {
        if (d.y < 0) d.y = 0;

        const minY = 0;
        const maxYForNode = timeAxisY - d.height - 10;  // 底部距离轴 10px
        if (d.y > maxYForNode) d.y = maxYForNode;

        const halfW = d.width / 2;
        if (d.x < minX + halfW) d.x = minX + halfW;
        if (d.x > maxX - halfW) d.x = maxX - halfW;
      });
    })
    .stop();

  for (let i = 0; i < 300; i++) simulation.tick();

  nodes.forEach(d => {
    if (d.y < 0) d.y = 0;
    const maxYForNode = timeAxisY - d.height - 10;
    if (d.y > maxYForNode) d.y = maxYForNode;
    const halfW = d.width / 2;
    if (d.x < minX + halfW) d.x = minX + halfW;
    if (d.x > maxX - halfW) d.x = maxX - halfW;
  });

  return nodes;
}

function curvePath(d: any, timeAxisY: number, labelHeight: number): string {
  const x0 = d.x;
  const y0 = d.y + labelHeight;
  const x1 = d.originalX;
  const y1 = timeAxisY;
  const dx = (x1 - x0) / 2;
  const dy = (y1 - y0) / 2;
  return `M${x0},${y0} C${x0},${y0 + dy} ${x0 + dx},${y1 - dy} ${x1},${y1}`;
}

function addHoverEffect(labelGroup: any, svg: any, nodes: any[], timeAxisY: number) {
  labelGroup.on('mouseover', function (event: any, d: any) {
    d3.select(this).raise().select('rect')
      .attr('stroke-width', 3)
      .attr('filter', 'url(#glow)');
    svg.selectAll('.link').filter((l: any) => l.index === d.index)
      .attr('stroke-width', 3).raise();
    svg.selectAll('.dot').filter((dot: any) => dot.index === d.index)
      .attr('r', 6).raise();
  }).on('mouseout', function (event: any, d: any) {
    d3.select(this).select('rect')
      .attr('stroke-width', 1)
      .attr('filter', null);
    svg.selectAll('.link').filter((l: any) => l.index === d.index)
      .attr('stroke-width', 1.5);
    svg.selectAll('.dot').filter((dot: any) => dot.index === d.index)
      .attr('r', 4);
  });
}

function addGlowFilter(svg: any) {
  const defs = svg.append('defs');
  const filter = defs.append('filter')
    .attr('id', 'glow')
    .attr('x', '-50%').attr('y', '-50%')
    .attr('width', '200%').attr('height', '200%');
  filter.append('feGaussianBlur')
    .attr('stdDeviation', '2.5')
    .attr('result', 'coloredBlur');
  const feMerge = filter.append('feMerge');
  feMerge.append('feMergeNode').attr('in', 'coloredBlur');
  feMerge.append('feMergeNode').attr('in', 'SourceGraphic');
}


function clean() {
  if (chart && timelineRef.value) {
    timelineRef.value.innerHTML = ''
  }
}

function redraw() {
  clean()
  draw()
}

watch(
  data,
  () => {
    console.log("eventsList:", eventsList.value)
    console.log("data:", data.value)
    redraw()
  },
  { immediate: true, deep: true },
)


function handleSizeChanged(hw){
  containerWidth.value  = hw.width
  containerHeight.value = hw.height
  redraw()
}
</script>

<template>
  <ResizeObserveChartContainer @size-changed="handleSizeChanged">
    <div id="timeline" ref="timelineRef" />
  </ResizeObserveChartContainer>

</template>

<style scoped lang="scss">
#timeline {
  width: 100%;
  height: 100%;
  overflow-x: auto;
  position: relative;
  overflow: hidden;
  padding-top: 0.5em;
}
</style>
