/**
 * Workflow Graph Component
 * Visualizes agent-to-agent communication and workflow structure
 */

import React from 'react';
import { ArrowRight, Network, Activity, ShieldAlert, FileText, DollarSign, Sparkles } from 'lucide-react';
import { AgentCommunication } from '@/types/agui';

interface WorkflowGraphProps {
  communications: AgentCommunication[];
  requestedAssessments: string[];
}

const agentConfig: Record<string, { icon: any; color: string; label: string }> = {
  'workflow-orchestrator': {
    icon: Network,
    color: 'purple',
    label: 'Orchestrator',
  },
  'medical-reasoner': {
    icon: Activity,
    color: 'blue',
    label: 'Medical',
  },
  'fraud-detector': {
    icon: ShieldAlert,
    color: 'red',
    label: 'Fraud',
  },
  'policy-checker': {
    icon: FileText,
    color: 'green',
    label: 'Policy',
  },
  'cost-analyzer': {
    icon: DollarSign,
    color: 'yellow',
    label: 'Cost',
  },
};

const colorClasses = {
  purple: 'bg-purple-100 border-purple-300 text-purple-700',
  blue: 'bg-blue-100 border-blue-300 text-blue-700',
  red: 'bg-red-100 border-red-300 text-red-700',
  green: 'bg-green-100 border-green-300 text-green-700',
  yellow: 'bg-yellow-100 border-yellow-300 text-yellow-700',
};

export const WorkflowGraph: React.FC<WorkflowGraphProps> = ({
  communications,
  requestedAssessments
}) => {
  if (communications.length === 0) return null;

  const latestComm = communications[communications.length - 1];

  // Map assessment types to agent IDs
  const assessmentToAgent: Record<string, string> = {
    medical: 'medical-reasoner',
    fraud: 'fraud-detector',
    policy: 'policy-checker',
    cost: 'cost-analyzer',
  };

  const activeAgents = requestedAssessments.map(
    (assessment) => assessmentToAgent[assessment]
  ).filter(Boolean);

  return (
    <div className="mb-6 p-6 bg-white rounded-lg border-2 border-purple-200">
      <div className="flex items-center gap-2 mb-4">
        <Network className="w-5 h-5 text-purple-600" />
        <h3 className="text-lg font-semibold text-gray-900">
          Multi-Agent Workflow
        </h3>
      </div>

      {/* Communication Flow */}
      <div className="flex flex-col gap-4">
        {/* Orchestrator (Top) */}
        <div className="flex justify-center">
          <AgentNode
            agentId={latestComm.from_agent}
            config={agentConfig[latestComm.from_agent]}
          />
        </div>

        {/* Arrow Down */}
        <div className="flex justify-center">
          <div className="flex flex-col items-center">
            <div className="h-8 w-0.5 bg-purple-300"></div>
            <ArrowRight className="w-5 h-5 text-purple-500 transform rotate-90" />
          </div>
        </div>

        {/* Message */}
        <div className="flex justify-center">
          <div className="max-w-md p-3 bg-purple-50 border border-purple-200 rounded-lg text-center">
            <p className="text-sm text-purple-800">{latestComm.message}</p>
            <p className="text-xs text-purple-600 mt-1">
              {latestComm.workflow_type === 'parallel' ? '↔️ Parallel Execution' : '→ Sequential Execution'}
            </p>
          </div>
        </div>

        {/* Arrow Down */}
        <div className="flex justify-center">
          <div className="flex flex-col items-center">
            <ArrowRight className="w-5 h-5 text-purple-500 transform rotate-90" />
            <div className="h-8 w-0.5 bg-purple-300"></div>
          </div>
        </div>

        {/* Child Agents (Bottom) */}
        <div className="flex justify-center gap-4 flex-wrap">
          {activeAgents.map((agentId) => (
            <div key={agentId} className="flex flex-col items-center">
              <AgentNode agentId={agentId} config={agentConfig[agentId]} />
            </div>
          ))}
        </div>

        {/* Execution Flow Description */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-600 text-center">
            <strong>Workflow:</strong> Orchestrator delegates {requestedAssessments.length} assessment{requestedAssessments.length > 1 ? 's' : ''} to specialized agents
            {latestComm.workflow_type === 'parallel' && ' (running in parallel)'}
          </p>
        </div>
      </div>
    </div>
  );
};

interface AgentNodeProps {
  agentId: string;
  config: { icon: any; color: string; label: string };
}

const AgentNode: React.FC<AgentNodeProps> = ({ agentId, config }) => {
  const Icon = config.icon;

  return (
    <div
      className={`
        flex flex-col items-center gap-2 p-4 rounded-lg border-2 min-w-[100px]
        ${colorClasses[config.color as keyof typeof colorClasses]}
        shadow-sm hover:shadow-md transition-all
      `}
    >
      <Icon className="w-6 h-6" />
      <span className="text-sm font-semibold">{config.label}</span>
      <span className="text-[10px] opacity-70 font-mono">{agentId}</span>
    </div>
  );
};
