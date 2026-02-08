'use client';

/**
 * Claims Adjudication UI - Main Page with Chat Interface
 * Real-time multi-agent workflow visualization with conversational UI
 */

import React, { useState, useEffect, useRef } from 'react';
import { useAGUI } from '@/lib/useAGUI';
import { ChatInterface, ChatInterfaceHandle } from '@/components/ChatInterface';
import { StageIndicator } from '@/components/StageIndicator';
import {
  MedicalAssessmentCard,
  FraudAssessmentCard,
  PolicyAssessmentCard,
  CostAssessmentCard,
} from '@/components/AssessmentCard';
import { FinalDecisionCard } from '@/components/FinalDecisionCard';
import { ProcessingCard } from '@/components/ProcessingCard';
import {
  Activity,
  ShieldAlert,
  FileText,
  DollarSign,
  Sparkles,
} from 'lucide-react';

export default function ClaimsAdjudicationPage() {
  const { state, connect, startAdjudication, registerSummaryCallback, intentType, isConnected } = useAGUI();
  const [sessionId] = useState(() => `session-${Date.now()}`);
  const chatInterfaceRef = useRef<ChatInterfaceHandle>(null);

  // Connect on mount
  useEffect(() => {
    console.log('🔌 Connecting to AG-UI adapter...');
    connect(sessionId);
  }, [sessionId, connect]);

  // Register summary callback
  useEffect(() => {
    registerSummaryCallback((summary: string) => {
      if (chatInterfaceRef.current) {
        chatInterfaceRef.current.addSummaryMessage(summary);
      }
    });
  }, [registerSummaryCallback]);

  const handleClaimSubmit = (claimId: string, intentType: 'full' | 'medical' | 'fraud' | 'policy' | 'cost' | 'multi', requestedAssessments: string[]) => {
    console.log('🚀 Starting adjudication for:', claimId, 'Type:', intentType, 'Assessments:', requestedAssessments);
    startAdjudication(claimId, intentType, requestedAssessments);
  };

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 flex-shrink-0">
        <div className="px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Claims Adjudication AI</h1>
              <p className="text-sm text-gray-600">Multi-Agent System with Real-time Analysis</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - Split Layout */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left Side - Chat Interface */}
        <div className="w-1/3 min-w-[400px] p-6 flex flex-col">
          <ChatInterface
            ref={chatInterfaceRef}
            onClaimSubmit={handleClaimSubmit}
            isProcessing={state.status === 'running'}
            isConnected={isConnected}
          />
        </div>

        {/* Right Side - Results Display */}
        <div className="flex-1 p-6 overflow-y-auto">
          {/* Connection Error */}
          {!isConnected && (
            <div className="mb-6 p-6 bg-red-50 border-2 border-red-300 rounded-lg">
              <h3 className="text-lg font-semibold text-red-800 mb-2">
                ⚠️ Unable to Connect to Backend
              </h3>
              <p className="text-sm text-red-700 mb-4">
                The frontend cannot connect to the AG-UI adapter server. Please ensure:
              </p>
              <ol className="list-decimal list-inside text-sm text-red-700 space-y-1 mb-4">
                <li>AgentField server is running on port 8080</li>
                <li>All agents are running (via launch_all_agents.py)</li>
                <li>AG-UI adapter is running on port 8000</li>
              </ol>
              <div className="bg-red-100 p-3 rounded text-xs font-mono text-red-900">
                <p># Terminal 1:</p>
                <p>agentfield server start</p>
                <p className="mt-2"># Terminal 2:</p>
                <p>python launch_all_agents.py</p>
                <p className="mt-2"># Terminal 3:</p>
                <p>cd ag-ui-adapter && python server.py</p>
              </div>
            </div>
          )}

          {/* Workflow Status */}
          {state.status !== 'idle' && (
            <>
              {/* Stage Indicators - Dynamic based on requested assessments */}
              <div className="mb-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">🔄 Workflow Progress</h2>
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-3">
                  {/* Only show stage indicators for requested assessments */}
                  {state.requestedAssessments.includes('medical') && (
                    <StageIndicator
                      name="medical"
                      label="Medical"
                      status={state.stages.medical}
                      icon={<Activity className="w-6 h-6 text-blue-600" />}
                    />
                  )}
                  {state.requestedAssessments.includes('fraud') && (
                    <StageIndicator
                      name="fraud"
                      label="Fraud"
                      status={state.stages.fraud}
                      icon={<ShieldAlert className="w-6 h-6 text-red-600" />}
                    />
                  )}
                  {state.requestedAssessments.includes('policy') && (
                    <StageIndicator
                      name="policy"
                      label="Policy"
                      status={state.stages.policy}
                      icon={<FileText className="w-6 h-6 text-green-600" />}
                    />
                  )}
                  {state.requestedAssessments.includes('cost') && (
                    <StageIndicator
                      name="cost"
                      label="Cost"
                      status={state.stages.cost}
                      icon={<DollarSign className="w-6 h-6 text-yellow-600" />}
                    />
                  )}
                  {/* Show decision indicator only for full workflows */}
                  {state.finalDecision !== null && (
                    <StageIndicator
                      name="decision"
                      label="Decision"
                      status={state.stages.decision}
                      icon={<Sparkles className="w-6 h-6 text-purple-600" />}
                    />
                  )}
                </div>
              </div>

              {/* Error Message */}
              {state.error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-300 rounded-lg">
                  <p className="text-sm font-medium text-red-800">❌ Error: {state.error}</p>
                </div>
              )}

              {/* Assessment Results - Show processing cards and completed cards dynamically */}
              {state.requestedAssessments.length > 0 && (
                <div className="mb-6">
                  <h2 className="text-xl font-bold text-gray-900 mb-4">📊 Agent Assessments</h2>
                  <div className="grid grid-cols-1 gap-4">
                    {/* Medical Assessment */}
                    {state.requestedAssessments.includes('medical') && (
                      <>
                        {state.stages.medical === 'in_progress' && (
                          <ProcessingCard stage="medical" />
                        )}
                        {state.assessments.medical && (
                          <MedicalAssessmentCard assessment={state.assessments.medical} />
                        )}
                      </>
                    )}

                    {/* Fraud Assessment */}
                    {state.requestedAssessments.includes('fraud') && (
                      <>
                        {state.stages.fraud === 'in_progress' && (
                          <ProcessingCard stage="fraud" />
                        )}
                        {state.assessments.fraud && (
                          <FraudAssessmentCard assessment={state.assessments.fraud} />
                        )}
                      </>
                    )}

                    {/* Policy Assessment */}
                    {state.requestedAssessments.includes('policy') && (
                      <>
                        {state.stages.policy === 'in_progress' && (
                          <ProcessingCard stage="policy" />
                        )}
                        {state.assessments.policy && (
                          <PolicyAssessmentCard assessment={state.assessments.policy} />
                        )}
                      </>
                    )}

                    {/* Cost Assessment */}
                    {state.requestedAssessments.includes('cost') && (
                      <>
                        {state.stages.cost === 'in_progress' && (
                          <ProcessingCard stage="cost" />
                        )}
                        {state.assessments.cost && (
                          <CostAssessmentCard assessment={state.assessments.cost} />
                        )}
                      </>
                    )}
                  </div>
                </div>
              )}

              {/* Final Decision */}
              {state.finalDecision && (
                <div className="mb-6">
                  <h2 className="text-xl font-bold text-gray-900 mb-4">✅ Final Decision</h2>
                  <FinalDecisionCard decision={state.finalDecision} />
                </div>
              )}
            </>
          )}

          {/* Empty State */}
          {state.status === 'idle' && isConnected && (
            <div className="text-center py-16">
              <Sparkles className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-700 mb-2">
                Ready to Process Claims
              </h3>
              <p className="text-gray-600">
                Enter a claim ID in the chat to start the adjudication workflow
              </p>
              <div className="mt-6 p-4 bg-blue-50 rounded-lg inline-block">
                <p className="text-sm text-blue-800 font-medium mb-2">Try these test claims:</p>
                <div className="flex gap-2 justify-center">
                  <code className="px-3 py-1 bg-white rounded text-blue-600 text-sm">
                    CLM10001
                  </code>
                  <code className="px-3 py-1 bg-white rounded text-blue-600 text-sm">
                    CLM10002
                  </code>
                  <code className="px-3 py-1 bg-white rounded text-blue-600 text-sm">
                    CLM10003
                  </code>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
