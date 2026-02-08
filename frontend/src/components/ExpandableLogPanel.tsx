/**
 * Expandable Log Panel Component
 * Shows real-time agent reasoning and progress logs
 */

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Terminal, CheckCircle2, Loader2 } from 'lucide-react';
import { ProgressLog } from '@/types/agui';

interface ExpandableLogPanelProps {
  stage: string;
  logs: ProgressLog[];
  isComplete: boolean;
}

export const ExpandableLogPanel: React.FC<ExpandableLogPanelProps> = ({
  stage,
  logs,
  isComplete
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Filter logs for this specific stage
  const stageLogs = logs.filter(log => log.stage === stage);

  if (stageLogs.length === 0) return null;

  const latestLog = stageLogs[stageLogs.length - 1];
  const progressPercentage = (latestLog.progress * 100).toFixed(0);

  return (
    <div className="mt-3">
      {/* Expandable Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-3 bg-white/60 hover:bg-white/80 rounded-lg transition-all"
      >
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4" />
          <span className="text-sm font-medium">
            {isComplete ? 'Agent Execution Logs' : 'Live Agent Reasoning'}
          </span>
          <span className="text-xs bg-white/80 px-2 py-0.5 rounded-full">
            {stageLogs.length} steps
          </span>
        </div>

        <div className="flex items-center gap-2">
          {!isComplete && (
            <span className="text-xs text-gray-600">{progressPercentage}%</span>
          )}
          {isExpanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </div>
      </button>

      {/* Expandable Content */}
      {isExpanded && (
        <div className="mt-2 p-4 bg-gray-900 rounded-lg text-gray-100 max-h-64 overflow-y-auto">
          <div className="space-y-2 font-mono text-xs">
            {stageLogs.map((log, index) => (
              <div
                key={index}
                className="flex items-start gap-2 pb-2 border-b border-gray-700 last:border-0"
              >
                <div className="flex-shrink-0 mt-0.5">
                  {index === stageLogs.length - 1 && !isComplete ? (
                    <Loader2 className="w-3 h-3 text-blue-400 animate-spin" />
                  ) : (
                    <CheckCircle2 className="w-3 h-3 text-green-400" />
                  )}
                </div>

                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-gray-400">
                      Step {log.step}/{log.total_steps}
                    </span>
                    <span className="text-gray-500 text-[10px]">
                      {log.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-gray-200">{log.message}</p>

                  {/* Progress bar for this step */}
                  <div className="mt-1 h-1 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 transition-all duration-300"
                      style={{ width: `${log.progress * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Summary at bottom */}
          <div className="mt-3 pt-3 border-t border-gray-700 text-center">
            {isComplete ? (
              <span className="text-green-400 text-xs">
                ✓ Agent execution completed successfully
              </span>
            ) : (
              <span className="text-blue-400 text-xs flex items-center justify-center gap-2">
                <Loader2 className="w-3 h-3 animate-spin" />
                Processing... {progressPercentage}% complete
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
