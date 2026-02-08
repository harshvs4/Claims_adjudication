/**
 * AG-UI Event Types for Claims Adjudication
 */

export interface AGUIEvent {
  type: string;
  session_id: string;
  timestamp: string;
  data: Record<string, any>;
}

export interface SessionStartedEvent extends AGUIEvent {
  type: 'session_started';
  data: {
    claim_id: string;
    message: string;
  };
}

export interface WorkflowStartedEvent extends AGUIEvent {
  type: 'workflow_started';
  data: {
    claim_id: string;
    workflow: string;
    stages: string[];
  };
}

export interface StageStartedEvent extends AGUIEvent {
  type: 'stage_started';
  data: {
    stage: string;
    agent: string;
    message: string;
  };
}

export interface StageProgressEvent extends AGUIEvent {
  type: 'stage_progress';
  data: {
    stage: string;
    message: string;
    progress: number;  // 0.0 to 1.0
    step: number;
    total_steps: number;
  };
}

export interface AgentCommunicationEvent extends AGUIEvent {
  type: 'agent_communication';
  data: {
    from_agent: string;
    to_agents: string[];
    message: string;
    workflow_type: 'parallel' | 'sequential';
  };
}

export interface StageCompletedEvent extends AGUIEvent {
  type: 'stage_completed';
  data: {
    stage: string;
    assessment: MedicalAssessment | FraudAssessment | PolicyAssessment | CostAssessment;
  };
}

export interface WorkflowCompletedEvent extends AGUIEvent {
  type: 'workflow_completed';
  data: {
    claim_id: string;
    decision: string;
    approved_amount: number;
    confidence: number;
    reasoning: string;
    key_factors: string[];
    full_result: AdjudicationResult;
  };
}

export interface ErrorEvent extends AGUIEvent {
  type: 'error';
  data: {
    error: string;
    details?: string;
  };
}

// Assessment Types
export interface MedicalAssessment {
  is_medically_necessary: boolean;
  treatment_appropriate: boolean;
  alternative_treatments_available: boolean;
  supporting_documentation_adequate: boolean;
  confidence: number;
  reasoning: string;
  red_flags: string[];
}

export interface FraudAssessment {
  fraud_risk_score: number;
  red_flags: string[];
  similar_fraud_cases_found: number;
  pattern_analysis: string;
  recommendation: string;
  reasoning: string;
}

export interface PolicyAssessment {
  covered_under_policy: boolean;
  exclusions_apply: string[];
  coverage_limits_exceeded: boolean;
  prior_authorization_required: boolean;
  prior_authorization_obtained: boolean;
  reasoning: string;
}

export interface CostAssessment {
  cost_reasonable: boolean;
  expected_range_min: number;
  expected_range_max: number;
  variance_percentage: number;
  reasoning: string;
}

export interface FinalDecision {
  claim_id: string;
  decision: 'APPROVE' | 'APPROVE_WITH_REVIEW' | 'INVESTIGATE' | 'DENY';
  approved_amount: number;
  denial_reason: string | null;
  investigation_required: boolean;
  key_factors: string[];
  reasoning: string;
  confidence: number;
}

export interface AdjudicationResult {
  claim_id: string;
  final_decision: FinalDecision;
  medical_assessment: MedicalAssessment;
  fraud_assessment: FraudAssessment;
  policy_assessment: PolicyAssessment;
  cost_assessment: CostAssessment;
  processing_time_ms: number;
  agents_consulted: string[];
}

// Workflow State
export type StageStatus = 'pending' | 'in_progress' | 'completed' | 'error';

export interface ProgressLog {
  stage: string;
  message: string;
  progress: number;
  step: number;
  total_steps: number;
  timestamp: Date;
}

export interface AgentCommunication {
  from_agent: string;
  to_agents: string[];
  message: string;
  workflow_type: 'parallel' | 'sequential';
  timestamp: Date;
}

export interface WorkflowState {
  claim_id: string | null;
  session_id: string | null;
  status: 'idle' | 'running' | 'completed' | 'error';
  requestedAssessments: string[];  // List of assessments requested for this workflow
  stages: {
    medical: StageStatus;
    fraud: StageStatus;
    policy: StageStatus;
    cost: StageStatus;
    decision: StageStatus;
  };
  assessments: {
    medical: MedicalAssessment | null;
    fraud: FraudAssessment | null;
    policy: PolicyAssessment | null;
    cost: CostAssessment | null;
  };
  finalDecision: FinalDecision | null;
  error: string | null;
  progressLogs: ProgressLog[];  // Real-time agent reasoning/progress logs
  agentCommunications: AgentCommunication[];  // Agent-to-agent communications
}
