/**
 * Final Decision Card
 * Displays the final adjudication decision with all details
 */

import React from 'react';
import type { FinalDecision } from '@/types/agui';
import { CheckCircle2, XCircle, AlertTriangle, Search } from 'lucide-react';
import { clsx } from 'clsx';

interface FinalDecisionCardProps {
  decision: FinalDecision;
}

export function FinalDecisionCard({ decision }: FinalDecisionCardProps) {
  const getDecisionConfig = (type: string) => {
    switch (type) {
      case 'APPROVE':
        return {
          icon: <CheckCircle2 className="w-12 h-12" />,
          color: 'bg-green-600',
          textColor: 'text-green-600',
          borderColor: 'border-green-600',
          bgColor: 'bg-green-50',
          label: 'Approved',
        };
      case 'APPROVE_WITH_REVIEW':
        return {
          icon: <CheckCircle2 className="w-12 h-12" />,
          color: 'bg-blue-600',
          textColor: 'text-blue-600',
          borderColor: 'border-blue-600',
          bgColor: 'bg-blue-50',
          label: 'Approved with Review',
        };
      case 'INVESTIGATE':
        return {
          icon: <Search className="w-12 h-12" />,
          color: 'bg-yellow-600',
          textColor: 'text-yellow-700',
          borderColor: 'border-yellow-600',
          bgColor: 'bg-yellow-50',
          label: 'Investigation Required',
        };
      case 'DENY':
        return {
          icon: <XCircle className="w-12 h-12" />,
          color: 'bg-red-600',
          textColor: 'text-red-600',
          borderColor: 'border-red-600',
          bgColor: 'bg-red-50',
          label: 'Denied',
        };
      default:
        return {
          icon: <AlertTriangle className="w-12 h-12" />,
          color: 'bg-gray-600',
          textColor: 'text-gray-600',
          borderColor: 'border-gray-600',
          bgColor: 'bg-gray-50',
          label: 'Unknown',
        };
    }
  };

  const config = getDecisionConfig(decision.decision);

  return (
    <div className={clsx('rounded-lg border-4 overflow-hidden shadow-xl', config.borderColor)}>
      {/* Header */}
      <div className={clsx('px-8 py-6', config.color)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="text-white">{config.icon}</div>
            <div>
              <h2 className="text-3xl font-bold text-white">{config.label}</h2>
              <p className="text-white/80 text-sm mt-1">Claim ID: {decision.claim_id}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-white/80 text-sm">Confidence</p>
            <p className="text-4xl font-bold text-white">
              {decision.confidence != null ? (decision.confidence * 100).toFixed(0) : '0'}%
            </p>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="p-8 bg-white space-y-6">
        {/* Approved Amount */}
        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">Approved Amount</p>
          <p className="text-4xl font-bold text-gray-900">
            ${decision.approved_amount != null ? decision.approved_amount.toLocaleString() : '0'}
          </p>
        </div>

        {/* Denial Reason */}
        {decision.denial_reason && (
          <div className={clsx('p-4 rounded-lg', config.bgColor)}>
            <p className="text-sm font-medium text-gray-700 mb-2">Denial Reason</p>
            <p className={clsx('text-sm font-medium', config.textColor)}>{decision.denial_reason}</p>
          </div>
        )}

        {/* Investigation Flag */}
        {decision.investigation_required && (
          <div className="p-4 rounded-lg bg-yellow-50 border border-yellow-300">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-700" />
              <p className="text-sm font-semibold text-yellow-800">Further investigation required</p>
            </div>
          </div>
        )}

        {/* Key Factors */}
        {decision.key_factors && decision.key_factors.length > 0 && (
          <div>
            <p className="text-sm font-medium text-gray-700 mb-3">Key Decision Factors</p>
            <div className="space-y-2">
              {decision.key_factors.map((factor, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-semibold">
                    {idx + 1}
                  </div>
                  <p className="text-sm text-gray-700 leading-relaxed flex-1">{factor}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Reasoning */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">Detailed Reasoning</p>
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{decision.reasoning}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
