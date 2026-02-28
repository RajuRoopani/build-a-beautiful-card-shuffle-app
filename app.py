from fastapi import FastAPI
from pydantic import BaseModel
from typing import Literal

app = FastAPI()


class CalculateRequest(BaseModel):
    operation: Literal["add", "subtract", "multiply"]
    a: float
    b: float


class CalculateResponse(BaseModel):
    result: float


@app.post("/calculate")
def calculate(request: CalculateRequest) -> CalculateResponse:
    """
    Performs basic arithmetic operations (add, subtract, multiply).
    
    Args:
        request: JSON body with operation, a, and b
        
    Returns:
        JSON with result field
    """
    if request.operation == "add":
        result = request.a + request.b
    elif request.operation == "subtract":
        result = request.a - request.b
    elif request.operation == "multiply":
        result = request.a * request.b
    
    return CalculateResponse(result=result)
