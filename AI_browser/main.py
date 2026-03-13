from fastapi import FastAPI,Query
from agent.planner import plan_task
from agent.executor import ActionExecutor
from agent.memory import Memory
from browser_manager import execute_plan

app=FastAPI()

executor=ActionExecutor()

memory=Memory()


@app.post("/run")

def run_agent(task:str=Query(...)):

    plan=plan_task(task)

    results=[]

    for step in plan:

        action=step["action"]

        params=step.get("params",{})

        result=executor.execute(action,params)

        memory.add(action,result)

        results.append(result)

    return {
        "task":task,
        "plan":plan,
        "results":results
    }

