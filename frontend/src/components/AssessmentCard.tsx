/**
 * Assessment Card Components
 * Display detailed results from each specialist agent
 */

import React from 'react';
import type {
  MedicalAssessment,
  FraudAssessment,
  PolicyAssessment,
  CostAssessment,
} from '@/types/agui';
import { CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import { clsx } from 'clsx';

interface AssessmentCardProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

function AssessmentCard({ title, icon, children }: AssessmentCardProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4 flex items-center gap-3">
        <div className="text-white">{icon}</div>
        <h3 className="text-lg font-semibold text-white">{title}</h3>
      </div>
      <div className="p-6">{children}</div>
    </div>
  );
}

function StatusBadge({ value, label }: { value: boolean; label?: string }) {
  return (
    <div className="flex items-center gap-2">
      {value ? (
        <CheckCircle2 className="w-5 h-5 text-green-600" />
      ) : (
        <XCircle className="w-5 h-5 text-red-600" />
      )}
      <span className={clsx('font-medium', value ? 'text-green-700' : 'text-red-700')}>
        {label || (value ? 'Yes' : 'No')}
      </span>
    </div>
  );
}

export function MedicalAssessmentCard({ assessment }: { assessment: MedicalAssessment }) {
  return (
    <AssessmentCard title="Medical Assessment" icon={<span className="text-2xl">🏥</span>}>
      <div className="space-y-4">
        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Medically Necessary</p>
          <StatusBadge value={assessment.is_medically_necessary} />
        </div>

        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Treatment Appropriate</p>
          <StatusBadge value={assessment.treatment_appropriate} />
        </div>

        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Documentation Adequate</p>
          <StatusBadge value={assessment.supporting_documentation_adequate} />
        </div>

        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Confidence</p>
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${assessment.confidence != null ? assessment.confidence * 100 : 0}%` }}
              />
            </div>
            <span className="text-sm font-semibold text-gray-700">
              {assessment.confidence != null ? (assessment.confidence * 100).toFixed(0) : '0'}%
            </span>
          </div>
        </div>

        {assessment.red_flags && assessment.red_flags.length > 0 && (
          <div>
            <p className="text-sm font-medium text-gray-600 mb-2">Red Flags</p>
            <div className="space-y-1">
              {assessment.red_flags.map((flag, idx) => (
                <div key={idx} className="flex items-start gap-2 text-sm text-red-600">
                  <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <span>{flag}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Reasoning</p>
          <p className="text-sm text-gray-700 leading-relaxed">{assessment.reasoning}</p>
        </div>
      </div>
    </AssessmentCard>
  );
}

export function FraudAssessmentCard({ assessment }: { assessment: FraudAssessment }) {
  const getRiskColor = (score: number) => {
    if (score < 0.3) return 'text-green-600';
    if (score < 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRiskLabel = (score: number) => {
    if (score < 0.3) return 'Low Risk';
    if (score < 0.7) return 'Medium Risk';
    return 'High Risk';
  };

  return (
    <AssessmentCard title="Fraud Assessment" icon={<span className="text-2xl">🔍</span>}>
      <div className="space-y-4">
        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Fraud Risk Score</p>
          <div className="flex items-center gap-3">
            <div className="flex-1 bg-gray-200 rounded-full h-3">
              <div
                className={clsx(
                  'h-3 rounded-full transition-all duration-500',
                  assessment.fraud_risk_score < 0.3 ? 'bg-green-500' :
                  assessment.fraud_risk_score < 0.7 ? 'bg-yellow-500' : 'bg-red-500'
                )}
                style={{ width: `${assessment.fraud_risk_score * 100}%` }}
              />
            </div>
            <span className={clsx('text-sm font-bold', getRiskColor(assessment.fraud_risk_score))}>
              {getRiskLabel(assessment.fraud_risk_score)}
            </span>
          </div>
        </div>

        {assessment.red_flags && assessment.red_flags.length > 0 && (
          <div>
            <p className="text-sm font-medium text-gray-600 mb-2">Red Flags Detected</p>
            <div className="space-y-1">
              {assessment.red_flags.map((flag, idx) => (
                <div key={idx} className="flex items-start gap-2 text-sm text-orange-700 bg-orange-50 p-2 rounded">
                  <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <span>{flag}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Similar Cases Found</p>
          <p className="text-2xl font-bold text-gray-900">{assessment.similar_fraud_cases_found}</p>
        </div>

        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Pattern Analysis</p>
          <p className="text-sm text-gray-700 leading-relaxed">{assessment.pattern_analysis}</p>
        </div>

        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Recommendation</p>
          <p className="text-sm font-semibold text-blue-700">{assessment.recommendation}</p>
        </div>

        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Reasoning</p>
          <p className="text-sm text-gray-700 leading-relaxed">{assessment.reasoning}</p>
        </div>
      </div>
    </AssessmentCard>
  );
}

export function PolicyAssessmentCard({ assessment }: { assessment: PolicyAssessment }) {
  return (
    <AssessmentCard title="Policy Assessment" icon={<span className="text-2xl">📄</span>}>
      <div className="space-y-4">
        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Covered Under Policy</p>
          <StatusBadge value={assessment.covered_under_policy} />
        </div>

        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Coverage Limits Exceeded</p>
          <StatusBadge value={!assessment.coverage_limits_exceeded} label={assessment.coverage_limits_exceeded ? 'Yes' : 'No'} />
        </div>

        {assessment.exclusions_apply && assessment.exclusions_apply.length > 0 && (
          <div>
            <p className="text-sm font-medium text-gray-600 mb-2">Exclusions Apply</p>
            <div className="space-y-1">
              {assessment.exclusions_apply.map((exclusion, idx) => (
                <div key={idx} className="flex items-start gap-2 text-sm text-red-600 bg-red-50 p-2 rounded">
                  <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <span>{exclusion}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Prior Authorization Required</p>
          <StatusBadge value={!assessment.prior_authorization_required} label={assessment.prior_authorization_required ? 'Yes' : 'No'} />
        </div>

        {assessment.prior_authorization_required && (
          <div>
            <p className="text-sm font-medium text-gray-600 mb-1">Prior Authorization Obtained</p>
            <StatusBadge value={assessment.prior_authorization_obtained} />
          </div>
        )}

        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Reasoning</p>
          <p className="text-sm text-gray-700 leading-relaxed">{assessment.reasoning}</p>
        </div>
      </div>
    </AssessmentCard>
  );
}

export function CostAssessmentCard({ assessment }: { assessment: CostAssessment }) {
  return (
    <AssessmentCard title="Cost Assessment" icon={<span className="text-2xl">💰</span>}>
      <div className="space-y-4">
        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Cost Reasonable</p>
          <StatusBadge value={assessment.cost_reasonable} />
        </div>

        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Expected Range</p>
          <p className="text-lg font-semibold text-gray-900">
            ${assessment.expected_range_min != null ? assessment.expected_range_min.toLocaleString() : '0'} - ${assessment.expected_range_max != null ? assessment.expected_range_max.toLocaleString() : '0'}
          </p>
        </div>

        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Variance</p>
          <div className="flex items-center gap-2">
            <span className={clsx(
              'text-xl font-bold',
              assessment.variance_percentage != null && Math.abs(assessment.variance_percentage) < 10 ? 'text-green-600' :
              assessment.variance_percentage != null && Math.abs(assessment.variance_percentage) < 25 ? 'text-yellow-600' : 'text-red-600'
            )}>
              {assessment.variance_percentage != null ? (assessment.variance_percentage > 0 ? '+' : '') + assessment.variance_percentage.toFixed(1) + '%' : '0%'}
            </span>
            <span className="text-sm text-gray-600">from expected</span>
          </div>
        </div>

        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Reasoning</p>
          <p className="text-sm text-gray-700 leading-relaxed">{assessment.reasoning}</p>
        </div>
      </div>
    </AssessmentCard>
  );
}
