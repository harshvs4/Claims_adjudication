/**
 * AG-UI WebSocket Client Hook
 * Manages WebSocket connection to the AG-UI adapter server
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import type {
  AGUIEvent,
  WorkflowState,
  StageStatus,
  MedicalAssessment,
  FraudAssessment,
  PolicyAssessment,
  CostAssessment
} from '@/types/agui';

const WS_URL = 'ws://localhost:8000/ws';

// Generate human-readable summary from assessment results
function generateAssessmentSummary(stage: string, assessment: any): string | null {
  if (!assessment) return null;

  switch (stage) {
    case 'medical':
      return `✅ **Medical Assessment Complete**\n\n` +
        `**Medical Necessity:** ${assessment.is_medically_necessary ? 'Approved ✓' : 'Not Approved ✗'}\n` +
        `**Appropriateness:** ${assessment.is_appropriate ? 'Yes ✓' : 'No ✗'}\n` +
        `**Confidence:** ${(assessment.confidence * 100).toFixed(0)}%\n\n` +
        `**Clinical Rationale:** ${assessment.clinical_rationale}\n\n` +
        (assessment.red_flags?.length > 0
          ? `⚠️ **Red Flags:** ${assessment.red_flags.join(', ')}\n`
          : '');

    case 'fraud':
      const riskLevel = assessment.fraud_score > 0.7 ? 'HIGH ⚠️' :
                       assessment.fraud_score > 0.4 ? 'MEDIUM ⚡' : 'LOW ✓';
      return `✅ **Fraud Detection Complete**\n\n` +
        `**Risk Level:** ${riskLevel}\n` +
        `**Fraud Score:** ${(assessment.fraud_score * 100).toFixed(0)}%\n` +
        `**Confidence:** ${(assessment.confidence * 100).toFixed(0)}%\n\n` +
        `**Analysis:** ${assessment.risk_analysis}\n\n` +
        (assessment.red_flags?.length > 0
          ? `🚩 **Red Flags Detected:**\n${assessment.red_flags.map((f: string) => `• ${f}`).join('\n')}\n`
          : '✓ No red flags detected\n');

    case 'policy':
      return `✅ **Policy Coverage Complete**\n\n` +
        `**Coverage Status:** ${assessment.is_covered ? 'Covered ✓' : 'Not Covered ✗'}\n` +
        `**Requires Authorization:** ${assessment.requires_authorization ? 'Yes' : 'No'}\n` +
        `**Confidence:** ${(assessment.confidence * 100).toFixed(0)}%\n\n` +
        `**Policy Analysis:** ${assessment.policy_analysis}\n\n` +
        (assessment.exclusions?.length > 0
          ? `⚠️ **Exclusions Found:**\n${assessment.exclusions.map((e: string) => `• ${e}`).join('\n')}\n`
          : '');

    case 'cost':
      const variance = assessment.cost_variance_percentage || 0;
      const varianceStatus = Math.abs(variance) < 10 ? 'Within Range ✓' :
                            variance > 0 ? `${variance.toFixed(0)}% Over Benchmark ⚠️` :
                            `${Math.abs(variance).toFixed(0)}% Under Benchmark`;
      return `✅ **Cost Assessment Complete**\n\n` +
        `**Claimed Amount:** $${assessment.claimed_amount?.toLocaleString() || 0}\n` +
        `**Expected Range:** $${assessment.expected_cost_min?.toLocaleString() || 0} - $${assessment.expected_cost_max?.toLocaleString() || 0}\n` +
        `**Variance:** ${varianceStatus}\n` +
        `**Reasonableness:** ${assessment.is_reasonable ? 'Reasonable ✓' : 'Questionable ⚠️'}\n\n` +
        `**Cost Analysis:** ${assessment.cost_analysis}\n`;

    default:
      return null;
  }
}

// Generate summary for final decision
function generateDecisionSummary(decision: any, claimId: string): string {
  const decisionLabel = decision.decision === 'APPROVE' ? '✅ APPROVED' :
                       decision.decision === 'APPROVE_WITH_REVIEW' ? '✅ APPROVED (Review Required)' :
                       decision.decision === 'INVESTIGATE' ? '🔍 INVESTIGATION REQUIRED' :
                       decision.decision === 'DENY' ? '❌ DENIED' : '❓ UNKNOWN';

  return `🎯 **Final Decision for ${claimId}**\n\n` +
    `**Decision:** ${decisionLabel}\n` +
    `**Approved Amount:** $${decision.approved_amount?.toLocaleString() || 0}\n` +
    `**Confidence:** ${(decision.confidence * 100).toFixed(0)}%\n\n` +
    (decision.denial_reason ? `**Denial Reason:** ${decision.denial_reason}\n\n` : '') +
    `**Summary:** ${decision.reasoning}\n\n` +
    (decision.key_factors?.length > 0
      ? `**Key Factors:**\n${decision.key_factors.map((f: string, i: number) => `${i + 1}. ${f}`).join('\n')}`
      : '');
}

export function useAGUI() {
  const [state, setState] = useState<WorkflowState>({
    claim_id: null,
    session_id: null,
    status: 'idle',
    requestedAssessments: [],
    stages: {
      medical: 'pending',
      fraud: 'pending',
      policy: 'pending',
      cost: 'pending',
      decision: 'pending',
    },
    assessments: {
      medical: null,
      fraud: null,
      policy: null,
      cost: null,
    },
    finalDecision: null,
    error: null,
  });

  const [intentType, setIntentType] = useState<'full' | 'medical' | 'fraud' | 'policy' | 'cost' | 'multi'>('full');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const onSummaryCallbackRef = useRef<((summary: string) => void) | null>(null);

  const connect = useCallback((sessionId: string) => {
    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = new WebSocket(`${WS_URL}/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ WebSocket connected');
      setState((prev) => ({ ...prev, session_id: sessionId, status: 'idle' }));
    };

    ws.onmessage = (event) => {
      try {
        const agEvent: AGUIEvent = JSON.parse(event.data);
        handleEvent(agEvent);
      } catch (error) {
        console.error('Failed to parse event:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setState((prev) => ({ ...prev, error: 'Connection error' }));
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Attempt to reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        if (wsRef.current?.readyState === WebSocket.CLOSED) {
          console.log('Attempting to reconnect...');
          connect(sessionId);
        }
      }, 3000);
    };
  }, []);

  const handleEvent = useCallback((event: AGUIEvent) => {
    console.log('📨 AG-UI Event:', event.type, event.data);

    switch (event.type) {
      case 'session_started':
        setState((prev) => ({
          ...prev,
          claim_id: event.data.claim_id,
        }));
        break;

      case 'workflow_started':
        setState((prev) => ({
          ...prev,
          status: 'running',
          claim_id: event.data.claim_id,
          requestedAssessments: event.data.requested_assessments || [],
        }));
        break;

      case 'stage_started':
        const stage = event.data.stage as keyof WorkflowState['stages'];
        setState((prev) => ({
          ...prev,
          stages: {
            ...prev.stages,
            [stage]: 'in_progress' as StageStatus,
          },
        }));
        break;

      case 'stage_completed':
        const completedStage = event.data.stage as keyof WorkflowState['stages'];
        const assessment = event.data.assessment;

        setState((prev) => ({
          ...prev,
          stages: {
            ...prev.stages,
            [completedStage]: 'completed' as StageStatus,
          },
          assessments: {
            ...prev.assessments,
            [completedStage]: assessment,
          },
        }));

        // Generate summary for individual assessments (non-full workflows)
        if (onSummaryCallbackRef.current && completedStage !== 'decision') {
          const summary = generateAssessmentSummary(completedStage, assessment);
          if (summary) {
            onSummaryCallbackRef.current(summary);
          }
        }
        break;

      case 'workflow_completed':
        // Check if this is a full workflow with a final decision
        const hasFinalDecision = event.data.decision !== undefined && event.data.decision !== null;

        if (hasFinalDecision) {
          // Full workflow - create and set final decision
          const finalDecision = {
            claim_id: event.data.claim_id,
            decision: event.data.decision,
            approved_amount: event.data.approved_amount,
            denial_reason: event.data.denial_reason || null,
            investigation_required: event.data.investigation_required || false,
            key_factors: event.data.key_factors || [],
            reasoning: event.data.reasoning,
            confidence: event.data.confidence,
          };

          setState((prev) => ({
            ...prev,
            status: 'completed',
            stages: {
              ...prev.stages,
              decision: 'completed' as StageStatus,
            },
            finalDecision,
          }));

          // Generate summary for full workflow completion
          if (onSummaryCallbackRef.current) {
            const summary = generateDecisionSummary(finalDecision, event.data.claim_id);
            onSummaryCallbackRef.current(summary);
          }
        } else {
          // Individual assessment - just mark as completed, no final decision
          setState((prev) => ({
            ...prev,
            status: 'completed',
          }));
        }
        break;

      case 'error':
        setState((prev) => ({
          ...prev,
          status: 'error',
          error: event.data.error,
        }));
        break;

      case 'pong':
        // Handle ping/pong for connection health
        break;

      default:
        console.warn('Unknown event type:', event.type);
    }
  }, []);

  const startAdjudication = useCallback((claimId: string, intent: 'full' | 'medical' | 'fraud' | 'policy' | 'cost' | 'multi' = 'full', requestedAssessments: string[] = []) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return;
    }

    // Track the intent type
    setIntentType(intent as any);

    // Reset state
    setState((prev) => ({
      ...prev,
      claim_id: claimId,
      status: 'running',
      requestedAssessments: requestedAssessments,
      stages: {
        medical: intent === 'full' || intent === 'medical' || requestedAssessments.includes('medical') ? 'pending' : 'pending',
        fraud: intent === 'full' || intent === 'fraud' || requestedAssessments.includes('fraud') ? 'pending' : 'pending',
        policy: intent === 'full' || intent === 'policy' || requestedAssessments.includes('policy') ? 'pending' : 'pending',
        cost: intent === 'full' || intent === 'cost' || requestedAssessments.includes('cost') ? 'pending' : 'pending',
        decision: intent === 'full' ? 'pending' : 'pending',
      },
      assessments: {
        medical: null,
        fraud: null,
        policy: null,
        cost: null,
      },
      finalDecision: null,
      error: null,
    }));

    // Send start message with intent type and requested assessments
    wsRef.current.send(
      JSON.stringify({
        type: 'start_adjudication',
        claim_id: claimId,
        intent_type: intent,
        requested_assessments: requestedAssessments,
      })
    );
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const registerSummaryCallback = useCallback((callback: (summary: string) => void) => {
    onSummaryCallbackRef.current = callback;
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    state,
    connect,
    disconnect,
    startAdjudication,
    registerSummaryCallback,
    intentType,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
  };
}
