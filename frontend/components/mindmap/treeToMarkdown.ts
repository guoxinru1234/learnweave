/** 将 MindmapAgent 输出的树形 JSON 转换为 Markdown 层级列表 */

export interface MindmapNode {
  id: string;
  label: string;
  note?: string;
  children?: MindmapNode[];
}

/**
 * 将嵌套节点树转换为 Markdown 无序列表
 * 例: [{id:"1", label:"RDD", children:[{id:"2", label:"缓存"}]}]
 *   → "- RDD\n  - 缓存"
 */
export function treeToMarkdown(nodes: MindmapNode[]): string {
  if (!nodes || nodes.length === 0) return "";

  const lines: string[] = [];
  for (const node of nodes) {
    _nodeToLines(node, 0, lines);
  }
  return lines.join("\n");
}

function _nodeToLines(node: MindmapNode, depth: number, lines: string[]): void {
  const indent = "  ".repeat(depth);
  const label = node.label || node.id || "未命名";
  // Markdown 列表项，转义特殊字符
  const safeLabel = label.replace(/\n/g, " ").trim();
  lines.push(`${indent}- ${safeLabel}`);

  if (node.children && node.children.length > 0) {
    for (const child of node.children) {
      _nodeToLines(child, depth + 1, lines);
    }
  }
}

/**
 * 将旧版平面数组格式转为树形
 * 旧格式: [{t: "标题", s: "副标题"}, ...]
 */
export function flatArrayToTree(
  items: { t?: string; s?: string; id?: string; label?: string }[]
): MindmapNode[] {
  if (!items || items.length === 0) return [];

  // 第一个元素作为根节点
  const root: MindmapNode = {
    id: "root",
    label: items[0].t || items[0].label || "知识导图",
    children: items.slice(1).map((item, i) => ({
      id: `node-${i + 1}`,
      label: (item.t || item.label || item.s || "").trim(),
    })),
  };

  return [root];
}

/**
 * 检测数据格式并统一转为树形
 */
export function normalizeToTree(data: any): MindmapNode[] {
  if (!data) return [];

  // 已经是树形格式
  if (Array.isArray(data) && data.length > 0 && data[0].children) {
    return data as MindmapNode[];
  }

  // 对象格式 {nodes: [...]}
  if (data.nodes && Array.isArray(data.nodes)) {
    if (data.nodes.length > 0 && data.nodes[0].children) {
      return data.nodes as MindmapNode[];
    }
    return flatArrayToTree(data.nodes);
  }

  // 平面数组 [{t, s}, ...]
  if (Array.isArray(data) && data.length > 0 && (data[0].t || data[0].label)) {
    return flatArrayToTree(data);
  }

  return [];
}
