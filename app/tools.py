"""Safe, local agent tools. No arbitrary shell, SQL, or filesystem execution."""
import ast
import operator
from typing import Any
from database.db import Database

_ALLOWED_BINOPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow}
_ALLOWED_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}

def safe_calculate(expression: str) -> float | int:
    if len(expression) > 120:
        raise ValueError("Expression is too long.")
    tree = ast.parse(expression, mode="eval")
    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if abs(node.value) > 1e12:
                raise ValueError("Number is outside the allowed range.")
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
            left, right = evaluate(node.left), evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 8:
                raise ValueError("Exponent is too large.")
            result = _ALLOWED_BINOPS[type(node.op)](left, right)
            if isinstance(result, (int, float)) and abs(result) > 1e15:
                raise ValueError("Result is outside the allowed range.")
            return result
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
            return _ALLOWED_UNARY[type(node.op)](evaluate(node.operand))
        raise ValueError("Only basic arithmetic is allowed.")
    result = evaluate(tree)
    if not isinstance(result, (int, float)):
        raise ValueError("Expression did not produce a number.")
    return result

def tool_definitions() -> list[dict[str, Any]]:
    return [
        {"type": "function", "name": "calculate", "description": "Evaluate a basic arithmetic expression safely. Use for numeric calculations.", "parameters": {"type": "object", "properties": {"expression": {"type": "string", "description": "Arithmetic such as (1200 * 3) / 4"}}, "required": ["expression"], "additionalProperties": False}, "strict": True},
        {"type": "function", "name": "add_task", "description": "Add a task to the user's task list.", "parameters": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"], "additionalProperties": False}, "strict": True},
        {"type": "function", "name": "list_tasks", "description": "List the user's tasks.", "parameters": {"type": "object", "properties": {"status": {"type": "string", "enum": ["all", "open", "done"]}}, "required": ["status"], "additionalProperties": False}, "strict": True},
        {"type": "function", "name": "complete_task", "description": "Mark one of the user's tasks complete by its numeric ID.", "parameters": {"type": "object", "properties": {"task_id": {"type": "integer"}}, "required": ["task_id"], "additionalProperties": False}, "strict": True},
    ]

def execute_tool(name: str, arguments: dict[str, Any], db: Database, session_id: str) -> dict[str, Any]:
    if name == "calculate":
        return {"result": safe_calculate(arguments["expression"])}
    if name == "add_task":
        task_id = db.add_task(session_id, arguments["title"])
        return {"task_id": task_id, "title": arguments["title"], "status": "open"}
    if name == "list_tasks":
        status = arguments.get("status", "all")
        return {"tasks": db.list_tasks(session_id, None if status == "all" else status)}
    if name == "complete_task":
        task_id = int(arguments["task_id"])
        return {"task_id": task_id, "completed": db.complete_task(session_id, task_id)}
    return {"error": f"Tool not allowed: {name}"}
