/**
 * Stage Indicator Component
 * Shows the current status of each workflow stage
 */

import React from 'react';
import { CheckCircle2, Circle, Loader2, XCircle } from 'lucide-react';
import type { StageStatus } from '@/types/agui';
import { clsx } from 'clsx';

interface StageIndicatorProps {
  name: string;
  label: string;
  status: StageStatus;
  icon: React.ReactNode;
}

export function StageIndicator({ name, label, status, icon }: StageIndicatorProps) {
  const getStatusIcon = () => {
    switch (status) {
      case 'pending':
        return <Circle className="w-6 h-6 text-gray-400" />;
      case 'in_progress':
        return <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle2 className="w-6 h-6 text-green-500" />;
      case 'error':
        return <XCircle className="w-6 h-6 text-red-500" />;
      default:
        return <Circle className="w-6 h-6 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'pending':
        return 'bg-gray-100 border-gray-300';
      case 'in_progress':
        return 'bg-blue-50 border-blue-400 shadow-lg shadow-blue-200/50';
      case 'completed':
        return 'bg-green-50 border-green-400';
      case 'error':
        return 'bg-red-50 border-red-400';
      default:
        return 'bg-gray-100 border-gray-300';
    }
  };

  return (
    <div
      className={clsx(
        'flex items-center gap-4 p-4 rounded-lg border-2 transition-all duration-300',
        getStatusColor()
      )}
    >
      <div className="flex-shrink-0">{icon}</div>
      <div className="flex-1">
        <h3 className="font-semibold text-gray-900">{label}</h3>
        <p className="text-sm text-gray-600 capitalize">{status.replace('_', ' ')}</p>
      </div>
      <div className="flex-shrink-0">{getStatusIcon()}</div>
    </div>
  );
}
