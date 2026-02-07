/**
 * Chat Interface Component
 * Conversational UI for claims adjudication
 */

import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot, User } from 'lucide-react';
import { clsx } from 'clsx';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatInterfaceProps {
  onClaimSubmit: (claimId: string, intentType: 'full' | 'medical' | 'fraud' | 'policy' | 'cost') => void;
  isProcessing: boolean;
  isConnected: boolean;
}

export function ChatInterface({ onClaimSubmit, isProcessing, isConnected }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hello! I'm your AI Claims Adjudication Assistant. I can help you process health insurance claims.\n\nTo get started, please provide a Claim ID (e.g., CLM10001) or ask me a question about the adjudication process.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const extractClaimId = (text: string): string | null => {
    // Match patterns like CLM10001, CLM-10001, claim 10001, etc.
    const patterns = [
      /\b(CLM[-\s]?\d+)\b/i,
      /\bclaim\s*(?:id)?[\s:]+(\d+)\b/i,
      /\b(CLM\d+)\b/i,
    ];

    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) {
        // Normalize to CLM format
        const digits = match[1].replace(/[^\d]/g, '');
        return `CLM${digits}`;
      }
    }

    return null;
  };

  const detectIntent = (text: string): { type: 'full' | 'medical' | 'fraud' | 'policy' | 'cost' | 'unknown', claimId: string | null } => {
    const claimId = extractClaimId(text);
    if (!claimId) {
      return { type: 'unknown', claimId: null };
    }

    const lowerText = text.toLowerCase();

    // Check for specific assessment requests
    if (lowerText.includes('cost') || lowerText.includes('price') || lowerText.includes('amount')) {
      return { type: 'cost', claimId };
    }
    if (lowerText.includes('medical') || lowerText.includes('necessity') || lowerText.includes('treatment')) {
      return { type: 'medical', claimId };
    }
    if (lowerText.includes('fraud') || lowerText.includes('risk') || lowerText.includes('suspicious')) {
      return { type: 'fraud', claimId };
    }
    if (lowerText.includes('policy') || lowerText.includes('coverage') || lowerText.includes('covered')) {
      return { type: 'policy', claimId };
    }

    // Default to full adjudication
    return { type: 'full', claimId };
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);

    // Detect user intent
    const intent = detectIntent(input);

    if (intent.type === 'unknown' || !intent.claimId) {
      // User asked a question or provided unclear input
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I'd be happy to help! However, I need a valid Claim ID to process.\n\nYou can:\n• Run full adjudication: \"Process CLM10001\"\n• Get specific assessment: \"Cost analysis for CLM10001\"\n• Medical assessment: \"Medical necessity for CLM10002\"\n• Fraud check: \"Fraud analysis for CLM10003\"\n• Policy check: \"Coverage for CLM10004\"\n\nOr ask me questions about the adjudication process!",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } else {
      // Generate appropriate response based on intent
      let responseContent = '';

      switch (intent.type) {
        case 'full':
          responseContent = `Got it! Running FULL ADJUDICATION for claim ${intent.claimId}.\n\nI'll analyze:\n🏥 Medical Necessity\n🔍 Fraud Patterns\n📄 Policy Coverage\n💰 Cost Reasonableness\n\nPlease wait while all agents work...`;
          break;
        case 'medical':
          responseContent = `Analyzing MEDICAL NECESSITY for claim ${intent.claimId}...\n\n🏥 Checking if treatment is medically necessary and appropriate.`;
          break;
        case 'fraud':
          responseContent = `Running FRAUD DETECTION for claim ${intent.claimId}...\n\n🔍 Analyzing patterns and checking for red flags.`;
          break;
        case 'policy':
          responseContent = `Checking POLICY COVERAGE for claim ${intent.claimId}...\n\n📄 Verifying coverage, exclusions, and authorization.`;
          break;
        case 'cost':
          responseContent = `Analyzing COST ASSESSMENT for claim ${intent.claimId}...\n\n💰 Evaluating if costs are reasonable and within expected ranges.`;
          break;
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responseContent,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Submit with intent type so backend knows which agent(s) to call
      onClaimSubmit(intent.claimId, intent.type);
    }

    setInput('');
    inputRef.current?.focus();
  };

  const addSystemMessage = (content: string) => {
    const message: Message = {
      id: Date.now().toString(),
      role: 'assistant',
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, message]);
  };

  // Expose method for parent to add messages
  useEffect(() => {
    if (!isConnected) {
      addSystemMessage(
        '⚠️ Connection lost to the adjudication system. Please check that:\n\n1. AgentField server is running (port 8080)\n2. All agents are running\n3. AG-UI adapter is running (port 8000)\n\nTrying to reconnect...'
      );
    }
  }, [isConnected]);

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg border border-gray-200">
      {/* Chat Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4 rounded-t-lg">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Claims Adjudication AI</h2>
            <p className="text-sm text-white/80">
              {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
            </p>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={clsx(
              'flex gap-3',
              message.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            {message.role === 'assistant' && (
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                <Bot className="w-5 h-5 text-blue-600" />
              </div>
            )}

            <div
              className={clsx(
                'max-w-[80%] rounded-lg px-4 py-3',
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              )}
            >
              <p className="text-sm leading-relaxed whitespace-pre-line">{message.content}</p>
              <p
                className={clsx(
                  'text-xs mt-1',
                  message.role === 'user' ? 'text-white/70' : 'text-gray-500'
                )}
              >
                {message.timestamp.toLocaleTimeString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit',
                  hour12: false
                })}
              </p>
            </div>

            {message.role === 'user' && (
              <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                <User className="w-5 h-5 text-purple-600" />
              </div>
            )}
          </div>
        ))}

        {isProcessing && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
              <Bot className="w-5 h-5 text-blue-600" />
            </div>
            <div className="bg-gray-100 rounded-lg px-4 py-3">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                <p className="text-sm text-gray-600">Processing your claim...</p>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              isConnected
                ? 'Enter claim ID or ask a question...'
                : 'Waiting for connection...'
            }
            disabled={!isConnected}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!isConnected || !input.trim() || isProcessing}
            className={clsx(
              'px-6 py-3 rounded-lg font-medium flex items-center gap-2 transition-all',
              !isConnected || !input.trim() || isProcessing
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:shadow-lg hover:scale-105'
            )}
          >
            {isProcessing ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
            Send
          </button>
        </div>

        {/* Quick Actions */}
        <div className="mt-3 flex flex-wrap gap-2">
          <p className="text-xs text-gray-600 w-full mb-1">Quick test claims:</p>
          {['CLM10001', 'CLM10002', 'CLM10003'].map((claimId) => (
            <button
              key={claimId}
              type="button"
              onClick={() => setInput(claimId)}
              disabled={!isConnected || isProcessing}
              className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {claimId}
            </button>
          ))}
        </div>
      </form>
    </div>
  );
}
