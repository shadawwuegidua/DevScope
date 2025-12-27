# Gravity Graph (D3 + React) 指南

> 面向少量节点场景的力导向“引力图”，强调样式与动画。无需区分用户/仓库，不包含“游离节点”。

## 概览
- 技术栈：React + D3（`d3-selection`、`d3-zoom`、`d3-force`、`d3-drag`）
- 目标：以少量节点展示分层关系与相似度，通过半径/颜色/布局体现层级，同时具备缩放、拖拽、悬停高亮、点击波纹、连线描边动画
- 适用：Next.js 或任意 React 项目

## 数据结构
```ts
export type NodeType = 'center' | 'mentor' | 'peer';

export interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  nodeType: NodeType;
  metrics: { size: number };
  similarity?: number; // 0~1，可选：影响颜色/距离/半径
}

export interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  source: GraphNode | string;
  target: GraphNode | string;
  value: number; // 0~1 相似度/权重
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  center: GraphNode; // 作为布局参考的中心节点
}
```

## 核心组件（样式与动画版）
> 简化版 TSX：强调视觉映射与交互动画；不区分用户/仓库、无“游离节点”。

```tsx
'use client';

import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

type NodeType = 'center' | 'mentor' | 'peer';

interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  nodeType: NodeType;
  metrics: { size: number };
  similarity?: number; // 0~1
}

interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  source: GraphNode | string;
  target: GraphNode | string;
  value: number; // 0~1
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  center: GraphNode;
}

interface GraphProps {
  data: GraphData;
  onNodeClick?: (node: GraphNode) => void;
}

const Graph: React.FC<GraphProps> = ({ data, onNodeClick }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current || !data) return;

    const nodes = data.nodes;
    const links = data.links;
    const center = data.center;

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    const svg = d3.select(svgRef.current)
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', [0, 0, width, height].join(' '))
      .style('display', 'block')
      .style('background', 'transparent');

    svg.selectAll('*').remove();

    const g = svg.append('g').attr('width', width).attr('height', height);

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform.toString());
      });
    svg.call(zoom);

    // 半径映射：中心固定大圆；导师/同伴按 size 指数映射
    const getNodeRadius = (d: GraphNode) => {
      if (d.nodeType === 'center') return 45;
      const s = Math.min(Math.max(d.metrics.size || 20, 10), 50); // clamp
      const base = d.nodeType === 'mentor' ? 26 : 20;
      const range = d.nodeType === 'mentor' ? 12 : 10;
      return base + Math.pow(s / 50, 0.5) * range; // 指数放缩，差异更柔和
    };

    // 颜色映射：单色系渐变（蓝系），随节点类型与相似度加深
    const getNodeColor = (d: GraphNode) => {
      const sim = d.similarity ?? 0.5; // 默认居中
      if (d.nodeType === 'center') return '#1E40AF'; // indigo-900
      if (d.nodeType === 'mentor') return sim > 0.7 ? '#1D4ED8' : sim > 0.4 ? '#2563EB' : '#3B82F6';
      return sim > 0.7 ? '#60A5FA' : sim > 0.4 ? '#7DD3FC' : '#93C5FD';
    };

    // 文本颜色：中心白字，其余深灰
    const getTextColor = (d: GraphNode) => (d.id === center.id ? '#fff' : '#333');

    // 力仿真：多力组合，少量节点更稳定
    const simulation = d3.forceSimulation<GraphNode>(nodes)
      .force('link', d3.forceLink<GraphNode, GraphLink>(links)
        .id(d => d.id)
        .distance(link => {
          const sim = link.value || 0;
          const min = 100, max = 320;
          const s = link.source as GraphNode;
          const t = link.target as GraphNode;
          const mentorExtra = (s.nodeType === 'mentor' || t.nodeType === 'mentor') ? 40 : 0;
          return min + Math.pow(1 - sim, 3) * (max - min) + mentorExtra;
        }))
      .force('charge', d3.forceManyBody()
        .strength((d: any) => {
          const n = d as GraphNode;
          if (n.nodeType === 'center') return -1600;
          if (n.nodeType === 'mentor') return -1000;
          return -700; // peer
        }))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide()
        .radius(d => (d.nodeType === 'mentor' ? getNodeRadius(d) + 12 : getNodeRadius(d) + 8))
        .strength(0.8))
      .force('radial', d3.forceRadial(
        (d: GraphNode) => {
          if (d.nodeType === 'center') return 0;
          const sim = d.similarity ?? 0.5;
          const base = d.nodeType === 'mentor' ? 180 : 140;
          const maxD = 360;
          return base + Math.pow(1 - sim, 2.5) * (maxD - base);
        },
        width / 2,
        height / 2
      ).strength((d: GraphNode) => {
        if (d.nodeType === 'mentor') return 0.35 + Math.pow(d.similarity ?? 0.5, 2) * 0.25;
        if (d.nodeType === 'peer') return 0.2 + Math.pow(d.similarity ?? 0.5, 2) * 0.2;
        return 0.1;
      }));

    // 连线
    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#E5E5E5')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', function(this: SVGLineElement | null) {
        const L = this?.getTotalLength?.() ?? 0;
        return `${L} ${L}`;
      } as any)
      .attr('stroke-dashoffset', function(this: SVGLineElement | null) {
        return this?.getTotalLength?.() ?? 0;
      } as any);

    // 节点分组
    const node = g.append('g')
      .selectAll<SVGGElement, GraphNode>('g')
      .data(nodes)
      .join<SVGGElement>('g')
      .attr('class', 'node');

    // 拖拽
    const drag = d3.drag<SVGGElement, GraphNode>()
      .on('start', (event) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      })
      .on('drag', (event) => {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      })
      .on('end', (event) => {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
      });
    node.call(drag);

    // 节点：主圆
    node.append('circle')
      .attr('r', getNodeRadius)
      .attr('fill', getNodeColor)
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .attr('opacity', d => (d.nodeType === 'peer' ? 0.92 : 1))
      .style('transform-origin', 'center')
      .style('transition', 'all 0.25s ease')
      .on('mouseover', function(event, d) {
        // 放大 & 阴影
        d3.select(this)
          .transition().duration(180)
          .attr('r', dd => getNodeRadius(dd) * 1.18)
          .style('filter', 'drop-shadow(0 0 6px rgba(0,0,0,0.2))');

        // tooltip（原生div）
        const tooltip = d3.select('body').append('div')
          .attr('class', 'tooltip')
          .style('position', 'absolute')
          .style('background', 'white')
          .style('padding', '8px 12px')
          .style('border', '1px solid #ccc')
          .style('border-radius', '6px')
          .style('pointer-events', 'none')
          .style('box-shadow', '0 2px 8px rgba(0,0,0,0.15)')
          .style('z-index', '1000')
          .style('opacity', '0')
          .style('font-size', '12px');

        const content = `
          <div style="font-weight:600;color:${getNodeColor(d)}">${d.id}</div>
          <div style="color:#666">size: <span style="color:#000">${d.metrics.size.toFixed?.(1) ?? d.metrics.size}</span></div>
          ${d.similarity !== undefined ? `<div style="color:#666">similarity: <span style="color:#000">${(d.similarity*100).toFixed(1)}%</span></div>` : ''}
          <div style="color:#888;font-size:11px;margin-top:4px">${d.nodeType === 'mentor' ? '导师' : d.nodeType === 'peer' ? '同伴' : '中心'}</div>
        `;
        tooltip.html(content)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px')
          .transition().duration(160).style('opacity', '1');

        // 高亮相邻
        const connected = new Set<string>();
        link.each(function(l) {
          const s = l.source as GraphNode; const t = l.target as GraphNode;
          if (s === d || t === d || s.id === d.id || t.id === d.id) {
            connected.add(s.id); connected.add(t.id);
            d3.select(this).transition().duration(160)
              .attr('stroke', '#666').attr('stroke-width', 2).attr('stroke-opacity', 1);
          }
        });
        node.selectAll('circle').style('opacity', n => connected.has(n.id) ? 1 : 0.3);
      })
      .on('mousemove', (event) => {
        d3.select('.tooltip')
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px');
      })
      .on('mouseout', function() {
        d3.select('.tooltip').remove();
        d3.select(this).transition().duration(160)
          .attr('r', getNodeRadius)
          .style('filter', null);
        link.transition().duration(160)
          .attr('stroke', '#E5E5E5').attr('stroke-width', 1).attr('stroke-opacity', 0.6);
        node.selectAll('circle').style('opacity', d => (d.nodeType === 'peer' ? 0.92 : 1));
      })
      .on('click', (event, d) => {
        onNodeClick?.(d);
        // 点击波纹
        const ripple = d3.select(event.currentTarget.parentNode as SVGGElement)
          .select('.ripple');
        ripple.attr('stroke', getNodeColor(d)).attr('stroke-width', 2).attr('stroke-opacity', 1)
          .transition().duration(650)
          .attr('r', getNodeRadius(d) * 2).attr('stroke-opacity', 0)
          .on('end', function() { d3.select(this).attr('r', 0); });
      });

    // 波纹层
    node.append('circle')
      .attr('class', 'ripple')
      .attr('r', 0)
      .attr('fill', 'none')
      .attr('stroke', 'none')
      .style('pointer-events', 'none');

    // 文本标签：中心居中，其余靠右
    node.append('text')
      .text(d => d.id)
      .attr('x', d => d.nodeType === 'center' ? 0 : 30)
      .attr('y', d => d.nodeType === 'center' ? 0 : 4)
      .attr('dominant-baseline', d => d.nodeType === 'center' ? 'middle' : 'auto')
      .attr('text-anchor', d => d.nodeType === 'center' ? 'middle' : 'start')
      .attr('font-size', d => d.nodeType === 'center' ? '14px' : '12px')
      .attr('fill', getTextColor)
      .attr('opacity', 0.85);

    // tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as GraphNode).x!)
        .attr('y1', d => (d.source as GraphNode).y!)
        .attr('x2', d => (d.target as GraphNode).x!)
        .attr('y2', d => (d.target as GraphNode).y!);
      node.attr('transform', (d: GraphNode) => `translate(${d.x},${d.y})`);
    });

    // 连线描边入场
    link
      .attr('stroke-dasharray', function(this: SVGLineElement) {
        const L = this?.getTotalLength?.() ?? 0; return `${L} ${L}`;
      })
      .attr('stroke-dashoffset', function(this: SVGLineElement) {
        return this?.getTotalLength?.() ?? 0;
      })
      .transition().duration(900)
      .attr('stroke-dashoffset', 0);

    // 节点淡入
    node.style('opacity', 0)
      .transition().duration(750)
      .delay((d, i) => i * 50)
      .style('opacity', d => (d.nodeType === 'peer' ? 0.92 : 1));

    return () => { simulation.stop(); };
  }, [data, onNodeClick]);

  return (
    <div ref={containerRef} style={{ width: '100%', height: 'calc(100vh - 6rem)' }}>
      <svg ref={svgRef} style={{ width: '100%', height: '100%', display: 'block' }} />
    </div>
  );
};

export default Graph;
```

## 最小数据示例
```ts
import type { GraphData } from './Graph';

export const sampleData: GraphData = {
  nodes: [
    { id: 'Center', nodeType: 'center', metrics: { size: 50 }, similarity: 1 },
    { id: 'Mentor A', nodeType: 'mentor', metrics: { size: 38 }, similarity: 0.75 },
    { id: 'Peer X', nodeType: 'peer', metrics: { size: 26 }, similarity: 0.6 },
    { id: 'Peer Y', nodeType: 'peer', metrics: { size: 22 }, similarity: 0.4 },
  ],
  links: [
    { source: 'Center', target: 'Mentor A', value: 0.8 },
    { source: 'Center', target: 'Peer X', value: 0.6 },
    { source: 'Center', target: 'Peer Y', value: 0.45 },
    { source: 'Mentor A', target: 'Peer X', value: 0.5 },
  ],
  center: { id: 'Center', nodeType: 'center', metrics: { size: 50 }, similarity: 1 },
};
```

## 使用方法
1. 安装依赖

```bash
npm install d3
```

2. 在页面中引入并渲染

```tsx
import Graph from './Graph';
import { sampleData } from './sampleData';

export default function Page() {
  return (
    <div style={{ height: '100vh' }}>
      <Graph data={sampleData} onNodeClick={(n) => console.log('clicked:', n)} />
    </div>
  );
}
```

## 样式与动画要点
- 半径：中心固定大圆；导师/同伴用 `size` 指数放缩，避免极端大小
- 颜色：单色系（蓝系）按 `nodeType/similarity` 分层加深，白色描边突出
- 布局：`forceLink` 距离随相似度缩短；导师节点额外疏散；`forceRadial` 将导师/同伴分布到不同环距
- 交互：悬停放大 + 阴影、邻接高亮、原生 `div` tooltip；点击波纹动画（圆环扩散且透明度递减）
- 动画：连线入场使用 `stroke-dasharray + stroke-dashoffset`；节点淡入与顺序延迟
- 可探索性：支持缩放（0.3~4x）与拖拽固定/释放位置

## 适配少量节点的建议
- 提高 `charge` 斥力与 `collide` 半径，防止节点重叠
- 适度增加 `link.distance` 的最大值，让布局更通透
- `radial.strength` 按层级区分（导师略强、同伴适中），增强层次感

## 可选扩展
- 改用紫系或青系配色；或按业务类型映射不同色盘
- 以 `similarity` 控制节点透明度（低相似度更淡）
- 为节点添加图标或头像：在 `g` 下追加 `image` 并与圆形同位

---
如需我将该组件抽成独立文件（含 `Graph.tsx` 与示例数据），我可以直接生成到你的项目目录中。