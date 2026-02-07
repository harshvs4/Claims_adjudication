"""
AG-UI Adapter for AgentField
Converts AgentField REST API to AG-UI event-based protocol
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import httpx
import asyncio
import json
import uuid
from datetime import datetime

app = FastAPI(title="AG-UI Adapter for Claims Adjudication")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AgentField configuration
AGENTFIELD_API = "http://localhost:8080/api/v1"


class ClaimRequest(BaseModel):
    claim_id: str
    session_id: Optional[str] = None


class AGUIEvent(BaseModel):
    """AG-UI protocol event"""
    type: str
    session_id: str
    timestamp: str
    data: Dict[str, Any]


class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_event(self, session_id: str, event: AGUIEvent):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(event.model_dump())


manager = ConnectionManager()


def create_event(event_type: str, session_id: str, data: Dict[str, Any]) -> AGUIEvent:
    """Create an AG-UI event"""
    return AGUIEvent(
        type=event_type,
        session_id=session_id,
        timestamp=datetime.utcnow().isoformat(),
        data=data
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ag-ui-adapter"}


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for AG-UI protocol"""
    await manager.connect(session_id, websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            if data.get("type") == "start_adjudication":
                claim_id = data.get("claim_id")

                # Send acknowledgment
                await manager.send_event(
                    session_id,
                    create_event("session_started", session_id, {
                        "claim_id": claim_id,
                        "message": "Starting claims adjudication workflow"
                    })
                )

                # Start adjudication in background
                asyncio.create_task(
                    run_adjudication(session_id, claim_id)
                )

            elif data.get("type") == "ping":
                await manager.send_event(
                    session_id,
                    create_event("pong", session_id, {})
                )

    except WebSocketDisconnect:
        manager.disconnect(session_id)


async def run_adjudication(session_id: str, claim_id: str):
    """Run the claims adjudication workflow and stream events"""

    try:
        # Send workflow started event
        await manager.send_event(
            session_id,
            create_event("workflow_started", session_id, {
                "claim_id": claim_id,
                "workflow": "claims_adjudication",
                "stages": ["medical", "fraud", "policy", "cost", "decision"]
            })
        )

        # Call AgentField API
        async with httpx.AsyncClient(timeout=120.0) as client:

            # Stage 1: Medical Assessment
            await manager.send_event(
                session_id,
                create_event("stage_started", session_id, {
                    "stage": "medical",
                    "agent": "medical-reasoner",
                    "message": "Evaluating medical necessity..."
                })
            )

            # Call workflow orchestrator (which will call all agents)
            url = f"{AGENTFIELD_API}/execute/workflow-orchestrator.adjudicate_claim"

            # Start the execution
            response = await client.post(
                url,
                json={"input": {"claim_id": claim_id}}
            )

            if response.status_code != 200:
                await manager.send_event(
                    session_id,
                    create_event("error", session_id, {
                        "error": f"AgentField API error: {response.status_code}",
                        "details": response.text
                    })
                )
                return

            result = response.json()

            if result.get("status") == "succeeded":
                # Parse the result
                adjudication = result.get("result", {})

                # Send stage completion events
                stages = [
                    ("medical", "medical_assessment"),
                    ("fraud", "fraud_assessment"),
                    ("policy", "policy_assessment"),
                    ("cost", "cost_assessment"),
                ]

                for stage_name, assessment_key in stages:
                    assessment = adjudication.get(assessment_key, {})
                    await manager.send_event(
                        session_id,
                        create_event("stage_completed", session_id, {
                            "stage": stage_name,
                            "assessment": assessment
                        })
                    )
                    await asyncio.sleep(0.5)  # Simulate streaming

                # Send final decision
                final_decision = adjudication.get("final_decision", {})
                await manager.send_event(
                    session_id,
                    create_event("workflow_completed", session_id, {
                        "claim_id": claim_id,
                        "decision": final_decision.get("decision"),
                        "approved_amount": final_decision.get("approved_amount"),
                        "confidence": final_decision.get("confidence"),
                        "reasoning": final_decision.get("reasoning"),
                        "key_factors": final_decision.get("key_factors", []),
                        "full_result": adjudication
                    })
                )

            else:
                # Handle failure
                await manager.send_event(
                    session_id,
                    create_event("error", session_id, {
                        "error": "Adjudication failed",
                        "details": result.get("error", "Unknown error")
                    })
                )

    except Exception as e:
        await manager.send_event(
            session_id,
            create_event("error", session_id, {
                "error": str(e),
                "traceback": str(e.__traceback__)
            })
        )


@app.post("/adjudicate")
async def adjudicate_claim(request: ClaimRequest):
    """
    REST endpoint for claim adjudication (non-streaming)
    For compatibility with non-WebSocket clients
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{AGENTFIELD_API}/execute/workflow-orchestrator.adjudicate_claim",
                json={"input": {"claim_id": request.claim_id}}
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"AgentField API error: {response.status_code}",
                    "details": response.text
                }

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("🔌 AG-UI ADAPTER SERVER")
    print("=" * 70)
    print("\nStarting AG-UI adapter for Claims Adjudication...")
    print("\nEndpoints:")
    print("  WebSocket: ws://localhost:8000/ws/{session_id}")
    print("  REST API:  http://localhost:8000/adjudicate")
    print("  Health:    http://localhost:8000/health")
    print("\nCORS enabled for: http://localhost:3000")
    print("=" * 70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
