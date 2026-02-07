# Claims Adjudication UI

Real-time web interface for the AI-powered Claims Adjudication Multi-Agent System using AG-UI protocol.

## Features

- **Real-time WebSocket Connection** - Live updates from the multi-agent workflow
- **AG-UI Protocol Integration** - Event-based communication with the backend
- **Beautiful UI** - Modern, responsive interface built with Next.js and Tailwind CSS
- **Live Progress Tracking** - Watch each agent complete its assessment in real-time
- **Detailed Results** - View comprehensive assessments from all specialist agents
- **Final Decision Display** - See the orchestrator's final adjudication decision with reasoning

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **WebSocket** - Real-time bidirectional communication
- **Lucide React** - Beautiful icon library

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start the Development Server

```bash
npm run dev
```

The UI will be available at [http://localhost:3000](http://localhost:3000)

## Usage

### Prerequisites

Before using the UI, ensure the following services are running:

1. **AgentField Server** (port 8080)
   ```bash
   agentfield server start
   ```

2. **All Agent Instances** (launched via the multi-agent launcher)
   ```bash
   python launch_all_agents.py
   ```

3. **AG-UI Adapter Server** (port 8000)
   ```bash
   cd ag-ui-adapter
   python server.py
   ```

### Adjudicating a Claim

1. Open [http://localhost:3000](http://localhost:3000) in your browser
2. Enter a Claim ID (e.g., `CLM10001`, `CLM10002`, `CLM10003`)
3. Click "Start Adjudication"
4. Watch the real-time workflow progress:
   - Medical Assessment
   - Fraud Detection
   - Policy Check
   - Cost Analysis
   - Final Decision

## Architecture

```
┌─────────────────┐
│   Next.js UI    │  (localhost:3000)
│  (React App)    │
└────────┬────────┘
         │ WebSocket
         │
┌────────▼────────┐
│  AG-UI Adapter  │  (localhost:8000)
│  (FastAPI WS)   │
└────────┬────────┘
         │ REST API
         │
┌────────▼────────┐
│ AgentField API  │  (localhost:8080)
│  (Multi-Agent)  │
└─────────────────┘
```

### AG-UI Protocol Events

The UI receives these event types from the AG-UI adapter:

- `session_started` - Adjudication session initiated
- `workflow_started` - Workflow execution begins
- `stage_started` - Agent starts processing
- `stage_completed` - Agent completes assessment
- `workflow_completed` - Final decision ready
- `error` - Error occurred during processing

## Components

### Main Components

- **`page.tsx`** - Main application page with workflow orchestration
- **`useAGUI.ts`** - Custom hook for WebSocket connection and state management

### UI Components

- **`StageIndicator.tsx`** - Shows status of each workflow stage
- **`AssessmentCard.tsx`** - Displays specialist agent assessments
- **`FinalDecisionCard.tsx`** - Shows final adjudication decision

## Available Claims

Test with these pre-loaded claim IDs:

- `CLM10001` - Routine appendectomy (likely approved)
- `CLM10002` - Experimental cancer treatment (requires review)
- `CLM10003` - Suspicious high-cost imaging (fraud risk)
- `CLM10004` - Covered knee replacement
- `CLM10005` - Policy exclusion case

## Development

### Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx       # Root layout
│   │   ├── page.tsx         # Main page
│   │   └── globals.css      # Global styles
│   ├── components/
│   │   ├── AssessmentCard.tsx
│   │   ├── FinalDecisionCard.tsx
│   │   └── StageIndicator.tsx
│   ├── lib/
│   │   └── useAGUI.ts       # AG-UI WebSocket hook
│   └── types/
│       └── agui.ts          # TypeScript types
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

### Build for Production

```bash
npm run build
npm start
```

## Troubleshooting

### WebSocket Connection Failed

- Ensure AG-UI adapter is running on port 8000
- Check browser console for connection errors
- Verify CORS settings in the adapter server

### No Updates Appearing

- Confirm all agents are running (medical, fraud, policy, cost, orchestrator)
- Check AG-UI adapter logs for errors
- Verify AgentField server is accessible

### Stage Stuck on "In Progress"

- Check agent logs for errors
- Verify the agent is registered with AgentField
- Try restarting the agents

## License

MIT
