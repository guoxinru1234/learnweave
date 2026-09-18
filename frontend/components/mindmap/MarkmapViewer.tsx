"use client";

import { useMemo } from "react";
import { normalizeToTree, MindmapNode } from "./treeToMarkdown";

interface Props {
  data: any;
  height?: string | number;
  className?: string;
  onNodeClick?: (node: MindmapNode) => void;
}

const PALETTE = [
  "#6366f1","#ec4899","#10b981","#f59e0b",
  "#8b5cf6","#06b6d4","#ef4444","#84cc16",
];

// 递归计算每个节点的子树高度（叶子节点数）
function countLeaves(node: MindmapNode): number {
  if (!node.children || node.children.length === 0) return 1;
  return node.children.reduce((s, c) => s + countLeaves(c), 0);
}

// 最大深度
function maxDepth(node: MindmapNode): number {
  if (!node.children || node.children.length === 0) return 1;
  return 1 + Math.max(...node.children.map(maxDepth));
}

// 递归布局：返回 {x, y, w(子树宽), h(子树高), nodeW, nodeH}
function layout(
  node: MindmapNode, x: number, y: number, levelHeight: number, levelWidth: number
): { x: number; y: number; w: number; h: number; nodeW: number; nodeH: number } {
  const children = node.children || [];
  if (children.length === 0) {
    const nw = 180, nh = 28;
    return { x, y, w: nw, h: nh, nodeW: nw, nodeH: nh };
  }

  // 先布局子节点
  const childLayouts = children.map(c => layout(c, x + levelWidth, 0, levelHeight, levelWidth));

  // 子节点垂直排列
  let cy = y - (childLayouts.reduce((s, l) => s + l.h, 0) + (children.length - 1) * levelHeight) / 2;
  const positionedChildren: { layout: typeof childLayouts[0]; childY: number }[] = [];

  for (const cl of childLayouts) {
    positionedChildren.push({ layout: cl, childY: cy });
    cy += cl.h + levelHeight;
  }

  const totalH = childLayouts.reduce((s, l) => s + l.h, 0) + (children.length - 1) * levelHeight;
  const maxChildW = Math.max(...childLayouts.map(l => l.w));
  const nw = 220, nh = 44;

  // Attach child info to node for rendering
  (node as any)._layout = { children: positionedChildren, x, totalH, nw, nh };

  return { x, y: y, w: nw + levelWidth + maxChildW, h: Math.max(nh, totalH), nodeW: nw, nodeH: nh };
}

// 递归SVG渲染
function renderNode(
  node: MindmapNode, x: number, y: number, depth: number, totalLeaves: number, totalDepth: number
): React.ReactNode {
  const children = node.children || [];
  const color = PALETTE[depth % 8];
  const fontSize = depth === 0 ? 26 : depth === 1 ? 15 : depth === 2 ? 13 : 11;
  const fontWeight = depth === 0 ? 700 : depth === 1 ? 600 : 500;
  const nw = depth === 0 ? 240 : depth === 1 ? 220 : depth === 2 ? 200 : 180;
  const hasNote = !!node.note;
  const baseNh = depth === 0 ? 50 : depth === 1 ? 36 : depth === 2 ? 30 : 26;
  const nh = hasNote ? baseNh + 16 : baseNh;
  const rx = depth === 0 ? 14 : depth === 1 ? 8 : 6;
  const isRoot = depth === 0;

  const gap = depth === 0 ? 70 : depth === 1 ? 55 : 45;
  const spacing = depth === 0 ? 30 : depth === 1 ? 20 : depth === 2 ? 14 : 10;
  const childNh = depth === 0 ? 36 : depth === 1 ? 30 : 26;
  const totalChildH = children.reduce((s, c) => s + countLeaves(c), 0) * (childNh + spacing) - spacing;
  const startY = y - totalChildH / 2 + nh / 2;

  let childY = startY;
  let childRender: React.ReactNode[] = [];

  for (const child of children) {
    const leaves = countLeaves(child);
    const childH = leaves * (childNh + spacing) - spacing;
    const childCenterY = childY + childH / 2;

    childRender.push(
      <g key={child.id || Math.random()}>
        {/* 贝塞尔曲线连接线 */}
        <path
          d={`M${x + nw} ${y + nh/2} C${x + nw + gap/2} ${y + nh/2}, ${x + nw + gap/2} ${childCenterY}, ${x + nw + gap} ${childCenterY}`}
          stroke={PALETTE[(depth + 1) % 8] + "50"}
          strokeWidth={depth === 0 ? 2 : 1.2}
          fill="none"
        />
        {renderNode(child, x + nw + gap, childCenterY, depth + 1, totalLeaves, totalDepth)}
      </g>
    );

    childY += childH + spacing;
  }

  return (
    <g>
      {/* 连线先渲染（在节点下面） */}
      {childRender}

      {/* 节点 */}
      <g style={{ cursor: "pointer" }}>
        <rect
          x={x} y={y}
          width={nw} height={nh}
          rx={rx}
          fill={isRoot ? `url(#rootGradient)` : "white"}
          stroke={isRoot ? "none" : color}
          strokeWidth={isRoot ? 0 : 1.8}
          filter={isRoot ? "url(#glowRoot)" : "url(#glowNode)"}
        />
        <text
          x={x + nw / 2} y={y + (hasNote ? nh / 2 - 6 : nh / 2 + fontSize * 0.33)}
          textAnchor="middle"
          fill={isRoot ? "white" : "#1e293b"}
          fontSize={fontSize}
          fontWeight={fontWeight}
          fontFamily="system-ui, -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif"
        >
          {node.label}
        </text>
        {hasNote && (
          <text
            x={x + nw / 2} y={y + nh / 2 + 11}
            textAnchor="middle"
            fill={isRoot ? "rgba(255,255,255,0.85)" : "#64748b"}
            fontSize={Math.max(fontSize - 3, 9)}
            fontFamily="system-ui, -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif"
          >
            {node.note}
          </text>
        )}
      </g>
    </g>
  );
}

export function MarkmapViewer({ data, height = "550px", className = "", onNodeClick }: Props) {
  const nodes = useMemo(() => normalizeToTree(data), [data]);

  if (!nodes?.length) return null;

  const root = nodes[0];
  const totalLeaves = countLeaves(root);
  const totalDepth = maxDepth(root);
  const totalLeafNodes = totalLeaves;

  // 计算画布尺寸
  const canvasW = Math.max(1200, 800 + totalDepth * 250);
  const canvasH = Math.max(800, totalLeafNodes * 55);

  return (
    <div className={`rounded-2xl border border-gray-100 ${className}`}
      style={{
        height: typeof height === "number" ? `${height}px` : height,
        overflow: "auto",
        background: "linear-gradient(160deg, #fafbff 0%, #f0f0ff 40%, #faf5ff 100%)",
      }}>
      <svg
        viewBox={`0 0 ${canvasW} ${canvasH}`}
        className="w-full"
        style={{ minWidth: 900, minHeight: Math.max(canvasH, 500) }}
        preserveAspectRatio="xMinYMin meet"
      >
        <defs>
          <linearGradient id="rootGradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#6366f1" />
            <stop offset="50%" stopColor="#4f46e5" />
            <stop offset="100%" stopColor="#7c3aed" />
          </linearGradient>
          <filter id="glowRoot">
            <feDropShadow dx="0" dy="3" stdDeviation="10" floodColor="#6366f1" floodOpacity="0.5" />
          </filter>
          <filter id="glowNode">
            <feDropShadow dx="0" dy="1" stdDeviation="3" floodColor="#000000" floodOpacity="0.06" />
          </filter>
          {/* 网格背景 */}
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <circle cx="20" cy="20" r="0.5" fill="#c7d2fe" opacity="0.15" />
          </pattern>
        </defs>

        {/* 背景网格 */}
        <rect width={canvasW} height={canvasH} fill="url(#grid)" />

        {/* 开始渲染 */}
        <g transform={`translate(60, ${canvasH / 2 + 80})`}>
          {renderNode(root, 0, 0, 0, totalLeaves, totalDepth)}
        </g>
      </svg>
    </div>
  );
}
