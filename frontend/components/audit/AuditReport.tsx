"use client";

import { useMemo } from "react";
import { Shield, AlertTriangle, CheckCircle, XCircle, BarChart3 } from "lucide-react";

interface AuditIssue {
  location: string;
  problem: string;
  severity: "critical" | "major" | "minor";
  fix: string;
}

interface AuditDetail {
  type: string;
  audit_result: "pass" | "needs_fix" | "reject";
  confidence: number;
  score: { accuracy: number; consistency: number; completeness: number; difficulty_match: number };
  issues?: AuditIssue[];
}

interface AuditReport {
  overall_confidence: number;
  passed: boolean;
  total_issues: number;
  critical_issues: number;
  items_audited: number;
  details: AuditDetail[];
}

/**
 * 赛题B核心：审核报告可视化
 * 展示多Agent交叉验证结果、置信度评分、幻觉检测
 */
export function AuditReportView({ report, compact = false }: { report: AuditReport; compact?: boolean }) {
  const typeLabel: Record<string, string> = {
    lecture_doc: "📝 讲义", mindmap: "🧠 导图", code: "💻 代码", quiz: "📋 题库",
  };

  const severityColor: Record<string, string> = {
    critical: "bg-red-100 text-red-700 border-red-300",
    major: "bg-amber-100 text-amber-700 border-amber-300",
    minor: "bg-blue-100 text-blue-700 border-blue-300",
  };

  return (
    <div className="space-y-4">
      {/* 总览卡片 */}
      <div className={`grid ${compact ? "grid-cols-2" : "grid-cols-4"} gap-3`}>
        <div className={`rounded-xl ${report.passed ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"} border p-4`}>
          <div className="flex items-center gap-2 mb-1">
            {report.passed ? <CheckCircle className="w-4 h-4 text-green-600" /> : <XCircle className="w-4 h-4 text-red-500" />}
            <span className={`text-xs font-semibold ${report.passed ? "text-green-700" : "text-red-700"}`}>审核结果</span>
          </div>
          <div className={`text-2xl font-bold ${report.passed ? "text-green-700" : "text-red-600"}`}>
            {report.passed ? "通过" : "需修正"}
          </div>
        </div>

        <div className="rounded-xl bg-indigo-50 border border-indigo-200 p-4">
          <div className="flex items-center gap-2 mb-1">
            <BarChart3 className="w-4 h-4 text-indigo-500" />
            <span className="text-xs font-semibold text-indigo-700">置信度</span>
          </div>
          <div className="text-2xl font-bold text-indigo-700">{report.overall_confidence}%</div>
        </div>

        <div className={`rounded-xl border p-4 ${report.critical_issues > 0 ? "bg-red-50 border-red-200" : "bg-gray-50 border-gray-200"}`}>
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle className={`w-4 h-4 ${report.critical_issues > 0 ? "text-red-500" : "text-gray-400"}`} />
            <span className="text-xs font-semibold">问题数</span>
          </div>
          <div className="text-2xl font-bold">{report.total_issues}
            {report.critical_issues > 0 && <span className="text-sm text-red-500 ml-1">({report.critical_issues}严重)</span>}
          </div>
        </div>

        <div className="rounded-xl bg-gray-50 border border-gray-200 p-4">
          <div className="flex items-center gap-2 mb-1">
            <Shield className="w-4 h-4 text-gray-400" />
            <span className="text-xs font-semibold text-gray-600">审核项</span>
          </div>
          <div className="text-2xl font-bold text-gray-700">{report.items_audited}</div>
        </div>
      </div>

      {/* 逐项审核详情 */}
      {!compact && report.details?.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-gray-700">逐项审核详情</h4>
          {report.details.map((d, i) => (
            <div key={i} className="rounded-xl border border-gray-200 p-4 bg-white">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold">{typeLabel[d.type] || d.type}</span>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  d.audit_result === "pass" ? "bg-green-100 text-green-700" :
                  d.audit_result === "needs_fix" ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"
                }`}>
                  {d.audit_result === "pass" ? "✅ 通过" : d.audit_result === "reject" ? "❌ 驳回" : "⚠️ 需修正"}
                </span>
              </div>

              {/* 四维评分 */}
              {d.score && (
                <div className="grid grid-cols-4 gap-2 mb-3">
                  {Object.entries(d.score).map(([k, v]) => (
                    <div key={k} className="text-center">
                      <div className="text-lg font-bold text-indigo-600">{v}</div>
                      <div className="text-[10px] text-gray-400">
                        {k === "accuracy" ? "准确性" : k === "consistency" ? "一致性" : k === "completeness" ? "完整性" : "难度匹配"}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* 问题列表 */}
              {(d.issues?.length ?? 0) > 0 && (
                <div className="space-y-1.5">
                  {(d.issues ?? []).map((issue, j) => (
                    <div key={j} className={`text-xs px-3 py-2 rounded-lg border ${severityColor[issue.severity]}`}>
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <span className="font-semibold">[{issue.severity === "critical" ? "严重" : issue.severity === "major" ? "重要" : "轻微"}]</span>
                        <span>{issue.location}</span>
                      </div>
                      <div className="opacity-80">{issue.problem}</div>
                      {issue.fix && <div className="text-green-600 mt-0.5">💡 {issue.fix}</div>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
