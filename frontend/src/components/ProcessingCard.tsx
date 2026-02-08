/**
 * Processing Card Component
 * Shows a placeholder card while an agent is processing
 */

import React from 'react';
import { Loader2, Activity, ShieldAlert, FileText, DollarSign } from 'lucide-react';
import { ExpandableLogPanel } from './ExpandableLogPanel';
import { ProgressLog } from '@/types/agui';

interface ProcessingCardProps {
  stage: 'medical' | 'fraud' | 'policy' | 'cost';
  message?: string;
  progressLogs?: ProgressLog[];
}

const stageConfig = {
  medical: {
    icon: Activity,
    title: 'Medical Necessity Assessment',
    color: 'blue',
    defaultMessage: 'Analyzing clinical necessity and treatment appropriateness...',
    steps: [
      'Loading claim and medical records',
      'Evaluating treatment necessity',
      'Checking clinical guidelines',
      'Analyzing supporting documentation',
    ],
  },
  fraud: {
    icon: ShieldAlert,
    title: 'Fraud Detection Analysis',
    color: 'red',
    defaultMessage: 'Analyzing patterns and checking for fraud indicators...',
    steps: [
      'Loading claim history and patterns',
      'Running ML fraud detection model',
      'Checking provider patterns',
      'Analyzing temporal anomalies',
    ],
  },
  policy: {
    icon: FileText,
    title: 'Policy Coverage Verification',
    color: 'green',
    defaultMessage: 'Verifying coverage, exclusions, and authorization...',
    steps: [
      'Loading policy details',
      'Checking coverage and exclusions',
      'Verifying authorization requirements',
      'Analyzing policy limits',
    ],
  },
  cost: {
    icon: DollarSign,
    title: 'Cost Reasonableness Analysis',
    color: 'yellow',
    defaultMessage: 'Evaluating cost reasonableness and benchmarks...',
    steps: [
      'Loading cost benchmarks',
      'Comparing claimed vs expected costs',
      'Analyzing regional variations',
      'Evaluating cost reasonableness',
    ],
  },
};

export const ProcessingCard: React.FC<ProcessingCardProps> = ({ stage, message, progressLogs = [] }) => {
  const config = stageConfig[stage];
  const Icon = config.icon;

  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 text-blue-800',
    red: 'bg-red-50 border-red-200 text-red-800',
    green: 'bg-green-50 border-green-200 text-green-800',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  };

  const iconColorClasses = {
    blue: 'text-blue-600',
    red: 'text-red-600',
    green: 'text-green-600',
    yellow: 'text-yellow-600',
  };

  return (
    <div className={`rounded-lg border-2 p-6 ${colorClasses[config.color as keyof typeof colorClasses]} transition-all duration-300 animate-pulse`}>
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="relative">
          <Icon className={`w-8 h-8 ${iconColorClasses[config.color as keyof typeof iconColorClasses]}`} />
          <Loader2 className="w-4 h-4 absolute -top-1 -right-1 animate-spin text-gray-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold">{config.title}</h3>
          <p className="text-sm opacity-80">In Progress...</p>
        </div>
      </div>

      {/* Processing Message */}
      <div className="mb-4 p-3 bg-white/60 rounded">
        <div className="flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin" />
          <p className="text-sm font-medium">
            {message || config.defaultMessage}
          </p>
        </div>
      </div>

      {/* Processing Steps */}
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wide opacity-70">Agent Tasks:</p>
        <ul className="space-y-1">
          {config.steps.map((step, index) => (
            <li key={index} className="text-sm flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-current opacity-50"></span>
              {step}
            </li>
          ))}
        </ul>
      </div>

      {/* Progress Indicator */}
      <div className="mt-4">
        <div className="h-1 bg-white/40 rounded-full overflow-hidden">
          <div className="h-full bg-current animate-progress-bar w-full"></div>
        </div>
      </div>

      {/* Expandable Log Panel - Shows real-time reasoning */}
      {progressLogs.length > 0 && (
        <ExpandableLogPanel
          stage={stage}
          logs={progressLogs}
          isComplete={false}
        />
      )}
    </div>
  );
};
