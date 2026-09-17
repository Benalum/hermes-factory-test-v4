from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

class CalculationRequest(BaseModel):
    operation: str
    operands: List[float]

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/calculate")
async def calculate(request: CalculationRequest):
    ops = request.operands
    if not ops:
        raise HTTPException(status_code=400, detail="Operands list cannot be empty")
    
    if request.operation == "add":
        result = sum(ops)
    elif request.operation == "subtract":
        result = ops[0]
        for x in ops[1:]:
            result -= x
    elif request.operation == "multiply":
        result = 1.0
        for x in ops:
            result *= x
    elif request.operation == "divide":
        if len(ops) < 2:
             raise HTTPException(status_code=400, detail="Divide operation requires at least 2 operands")
        result = ops[0]
        for x in ops[1:]:
            if x == 0:
                raise HTTPException(status_code=400, detail="Division by zero")
            result /= x
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported operation: {request.operation}")
    
    return {"result": result}
