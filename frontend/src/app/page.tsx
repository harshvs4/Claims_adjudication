'use client';

/**
 * Claims Adjudication UI - Main Page
 * Real-time multi-agent workflow visualization
 */

import React, { useState, useEffect } from 'react';
import { useAGUI } from '@/lib/useAGUI';
import { StageIndicator } from '@/components/StageIndicator';
import {
  MedicalAssessmentCard,
  FraudAssessmentCard,
  PolicyAssessmentCard,
  CostAssessmentCard,
} from '@/components/AssessmentCard';
import { FinalDecisionCard } from '@/components/FinalDecisionCard';
import {
  Activity,
  ShieldAlert,
  FileText,
  DollarSign,
  Sparkles,
  Play,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { clsx } from 'clsx';

export default function ClaimsAdjudicationPage() {
  const { state, connect, startAdjudication, isConnected } = useAGUI();
  const [claimId, setClaimId] = useState('CLM10001');
  const [sessionId] = useState(() => `session-${Date.now()}`);

  // Connect on mount
  useEffect(() => {
    connect(sessionId);
  }, [sessionId, connect]);

  const handleStartAdjudication = () => {
    startAdjudication(claimId);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Claims Adjudication</h1>
                <p className="text-sm text-gray-600">AI-Powered Multi-Agent System</p>
              </div>
            </div>

            {/* Connection Status */}
            <div className="flex items-center gap-2">
              {isConnected ? (
                <>
                  <Wifi className="w-5 h-5 text-green-600" />
                  <span className="text-sm font-medium text-green-700">Connected</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-5 h-5 text-red-600" />
                  <span className="text-sm font-medium text-red-700">Disconnected</span>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Input Section */}
        <div className="mb-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Start Adjudication</h2>
            <div className="flex gap-4">
              <input
                type="text"
                value={claimId}
                onChange={(e) => setClaimId(e.target.value)}
                placeholder="Enter Claim ID (e.g., CLM10001)"
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={state.status === 'running'}
              />
              <button
                onClick={handleStartAdjudication}
                disabled={!isConnected || state.status === 'running' || !claimId}
                className={clsx(
                  'px-6 py-3 rounded-lg font-semibold flex items-center gap-2 transition-all',
                  !isConnected || state.status === 'running' || !claimId
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:shadow-lg hover:scale-105'
                )}
              >
                <Play className="w-5 h-5" />
                {state.status === 'running' ? 'Processing...' : 'Start Adjudication'}
              </button>
            </div>
          </div>
        </div>

        {/* Workflow Status */}
        {state.status !== 'idle' && (
          <>
            {/* Stage Indicators */}
            <div className="mb-8">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Workflow Progress</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <StageIndicator
                  name="medical"
                  label="Medical"
                  status={state.stages.medical}
                  icon={<Activity className="w-8 h-8 text-blue-600" />}
                />
                <StageIndicator
                  name="fraud"
                  label="Fraud Detection"
                  status={state.stages.fraud}
                  icon={<ShieldAlert className="w-8 h-8 text-red-600" />}
                />
                <StageIndicator
                  name="policy"
                  label="Policy Check"
                  status={state.stages.policy}
                  icon={<FileText className="w-8 h-8 text-green-600" />}
                />
                <StageIndicator
                  name="cost"
                  label="Cost Analysis"
                  status={state.stages.cost}
                  icon={<DollarSign className="w-8 h-8 text-yellow-600" />}
                />
                <StageIndicator
                  name="decision"
                  label="Final Decision"
                  status={state.stages.decision}
                  icon={<Sparkles className="w-8 h-8 text-purple-600" />}
                />
              </div>
            </div>

            {/* Error Message */}
            {state.error && (
              <div className="mb-8 p-4 bg-red-50 border border-red-300 rounded-lg">
                <p className="text-sm font-medium text-red-800">Error: {state.error}</p>
              </div>
            )}

            {/* Assessment Results */}
            {(state.assessments.medical ||
              state.assessments.fraud ||
              state.assessments.policy ||
              state.assessments.cost) && (
              <div className="mb-8">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Specialist Assessments</h2>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {state.assessments.medical && (
                    <MedicalAssessmentCard assessment={state.assessments.medical} />
                  )}
                  {state.assessments.fraud && (
                    <FraudAssessmentCard assessment={state.assessments.fraud} />
                  )}
                  {state.assessments.policy && (
                    <PolicyAssessmentCard assessment={state.assessments.policy} />
                  )}
                  {state.assessments.cost && (
                    <CostAssessmentCard assessment={state.assessments.cost} />
                  )}
                </div>
              </div>
            )}

            {/* Final Decision */}
            {state.finalDecision && (
              <div className="mb-8">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Final Decision</h2>
                <FinalDecisionCard decision={state.finalDecision} />
              </div>
            )}
          </>
        )}

        {/* Empty State */}
        {state.status === 'idle' && (
          <div className="text-center py-16">
            <Sparkles className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-700 mb-2">Ready to Adjudicate</h3>
            <p className="text-gray-600">Enter a claim ID and click "Start Adjudication" to begin</p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <p className="text-sm text-gray-600 text-center">
            Powered by AgentField Multi-Agent System • AG-UI Real-time Protocol
          </p>
        </div>
      </footer>
    </div>
  );
}
