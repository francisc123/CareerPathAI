import httpx
import json
import asyncio
import logging
from aiokafka import AIOKafkaProducer
from langgraph.graph import StateGraph, END, START
from .state import WorkflowState
from .config import KAFKA_BROKERS, TOPIC_GAPS_IDENTIFIED, JOB_SCRAPER_URL

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Graph Nodes ---

async def trigger_job_search(state: WorkflowState):
    """Node: Triggers the job scraping service via HTTP POST."""
    user_id = state["user_id"]
    target_role = state["target_role"]
    logging.info(f"Attempting to trigger job search for user {user_id} (Attempt {state['retry_count'] + 1})")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{JOB_SCRAPER_URL}/scrape/trigger",
                json={"user_id": user_id, "query": target_role},
                timeout=10.0
            )
            response.raise_for_status()
            state["current_node"] = "job_search_triggered"
            state["error"] = None # Clear error on success
        except httpx.RequestError as e:
            logging.warning(f"HTTP request to job scraper failed for user {user_id}: {e}")
            state["error"] = str(e)
            state["retry_count"] += 1
    return state

async def trigger_learning_path(state: WorkflowState):
    """Node: Publishes a 'gaps.identified' event to Kafka."""
    user_id = state["user_id"]
    logging.info(f"Triggering learning path generation for user {user_id}")

    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await producer.start()
    try:
        message = {
            "user_id": user_id,
            "gaps": state["gaps"],
            "target_role": state["target_role"]
        }
        await producer.send_and_wait(TOPIC_GAPS_IDENTIFIED, message)
        state["current_node"] = "learning_path_triggered"
    finally:
        await producer.stop()
    return state

async def handle_failure(state: WorkflowState):
    """Node: Handles the final failure after all retries."""
    user_id = state["user_id"]
    error = state["error"]
    logging.error(f"Job search trigger failed permanently for user {user_id} after {state['retry_count']} retries. Error: {error}")
    state["current_node"] = "failed_state"
    # Here you could also publish to a DLQ or trigger an alert
    return state

# --- Conditional Edges ---

def route_flow(state: WorkflowState):
    """Conditional edge: Routes based on the CV score."""
    score = state.get("cv_score", 0)
    if score >= 70:
        return "trigger_job_search"
    else:
        return "trigger_learning_path"

def check_job_search_status(state: WorkflowState):
    """Conditional edge: Checks if the job search trigger was successful."""
    if state.get("error"):
        if state.get("retry_count", 0) < 2: # 2 retries (total 3 attempts)
            return "retry"
        else:
            return "fail"
    return "success"

# --- Graph Definition ---

def build_workflow_graph():
    """Builds and returns the LangGraph StateGraph with retry logic."""
    workflow = StateGraph(WorkflowState)

    workflow.add_node("trigger_job_search", trigger_job_search)
    workflow.add_node("trigger_learning_path", trigger_learning_path)
    workflow.add_node("handle_failure", handle_failure)

    workflow.add_conditional_edges(
        START,
        route_flow,
        {
            "trigger_job_search": "trigger_job_search",
            "trigger_learning_path": "trigger_learning_path",
        },
    )

    workflow.add_conditional_edges(
        "trigger_job_search",
        check_job_search_status,
        {
            "success": END,
            "fail": "handle_failure",
            "retry": "trigger_job_search",
        }
    )

    workflow.add_edge("trigger_learning_path", END)
    workflow.add_edge("handle_failure", END)

    return workflow.compile()

# Singleton instance of the compiled graph
graph = build_workflow_graph()
