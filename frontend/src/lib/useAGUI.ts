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

export function useAGUI() {
  const [state, setState] = useState<WorkflowState>({
    claim_id: null,
    session_id: null,
    status: 'idle',
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

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

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
        break;

      case 'workflow_completed':
        setState((prev) => ({
          ...prev,
          status: 'completed',
          stages: {
            ...prev.stages,
            decision: 'completed' as StageStatus,
          },
          finalDecision: {
            claim_id: event.data.claim_id,
            decision: event.data.decision,
            approved_amount: event.data.approved_amount,
            denial_reason: null,
            investigation_required: false,
            key_factors: event.data.key_factors || [],
            reasoning: event.data.reasoning,
            confidence: event.data.confidence,
          },
        }));
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

  const startAdjudication = useCallback((claimId: string, intentType: 'full' | 'medical' | 'fraud' | 'policy' | 'cost' = 'full') => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return;
    }

    // Reset state
    setState((prev) => ({
      ...prev,
      claim_id: claimId,
      status: 'running',
      stages: {
        medical: intentType === 'full' || intentType === 'medical' ? 'pending' : 'pending',
        fraud: intentType === 'full' || intentType === 'fraud' ? 'pending' : 'pending',
        policy: intentType === 'full' || intentType === 'policy' ? 'pending' : 'pending',
        cost: intentType === 'full' || intentType === 'cost' ? 'pending' : 'pending',
        decision: intentType === 'full' ? 'pending' : 'pending',
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

    // Send start message with intent type
    wsRef.current.send(
      JSON.stringify({
        type: 'start_adjudication',
        claim_id: claimId,
        intent_type: intentType,
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
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
  };
}
