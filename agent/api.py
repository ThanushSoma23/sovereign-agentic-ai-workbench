from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from sovereign_agent.graph import app

app_api = FastAPI(
    title="SIH26117 Sovereign Agent API",
    version="1.0"
)


class AgentRequest(BaseModel):
    question: str
    context: str = ""


@app_api.post("/agent/run")
def run_agent(request: AgentRequest):

    try:

        initial_state = {
            "question": request.question,
            "route": "",
            "supervisor_reason": "",
            "plan": [],
            "current_agent": "",
            "agent_result": "",
            "tool_results": [],
            "observations": [],
            "verification": "",
            "verification_status": False,
            "retry_count": 0,
            "final_answer": "",
            "context": request.context
        }

        result = app.invoke(initial_state)

        return {
            "success": True,
            "route": result.get("route", ""),
            "currentAgent": result.get("current_agent", ""),
            "supervisorReason": result.get("supervisor_reason", ""),
            "plan": result.get("plan", []),
            "verification": result.get("verification", ""),
            "finalAnswer": result.get("final_answer", "")
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )