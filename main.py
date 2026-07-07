from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, Tuple, Any, Literal

app = FastAPI(title="Team Task Manager API")
class UnifiedResponse(BaseModel):
    statusCode: int
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str
    path: str

class TaskCreateSchema(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=1)
    assignee: str = Field(..., min_length=1)
    priority: int = Field(..., ge=1, le=5)

    class Config:
        str_strip_whitespace = True

class TaskStatusUpdateSchema(BaseModel):
    status: Literal["todo", "in_progress", "done"]
tasks_db = [
    {
        "id": 1, 
        "title": "Thiet ke database Shop AI", 
        "description": "Xay dung bang va toi uu index", 
        "assignee": "QuyDev", 
        "priority": 1, 
        "status": "todo",
        "created_at": "2026-07-01T09:00:00Z"
    },
    {
        "id": 2, 
        "title": "Code bo API Authen", 
        "description": "Trien khai filter verify JWT token", 
        "assignee": "FixerQ", 
        "priority": 2, 
        "status": "done",
        "created_at": "2026-07-01T10:00:00Z"
    }
]

def get_current_iso_time() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "statusCode": 422,
            "message": "Lỗi: Dữ liệu đầu vào không hợp lệ hoặc sai định dạng quy định!",
            "data": None,
            "error": "ERR-VAL-422: Validation error at Request Body fields constraint layout.",
            "timestamp": get_current_iso_time(),
            "path": request.url.path
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    internal_error = None
    message = exc.detail
    
    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", exc.detail)
        internal_error = exc.detail.get("error", None)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "statusCode": exc.status_code,
            "message": message,
            "data": None,
            "error": internal_error,
            "timestamp": get_current_iso_time(),
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "statusCode": 500,
            "message": "Lỗi: Hệ thống gặp sự cố bất ngờ. Vui lòng thử lại sau!",
            "data": None,
            "error": f"ERR-SYS-500: {str(exc)}",
            "timestamp": get_current_iso_time(),
            "path": request.url.path
        }
    )

@app.get("/tasks", response_model=UnifiedResponse)
async def get_all_tasks(request: Request, status: Optional[str] = None):
    filtered_tasks = tasks_db
    if status:
        filtered_tasks = [task for task in tasks_db if task["status"] == status]
        
    return {
        "statusCode": 200,
        "message": "Lấy danh sách công việc thành công!",
        "data": filtered_tasks,
        "error": None,
        "timestamp": get_current_iso_time(),
        "path": request.url.path
    }

@app.post("/tasks", response_model=UnifiedResponse, status_code=status.HTTP_201_CREATED)
async def create_task(request: Request, task_in: TaskCreateSchema):
    for task in tasks_db:
        if task["title"].strip().lower() == task_in.title.strip().lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Lỗi: Tiêu đề công việc này đã tồn tại trong nhóm!",
                    "error": "ERR-TASK-01: Task conflict: Title field duplicates an existing record."
                }
            )
            
    max_id = max([task["id"] for task in tasks_db]) if tasks_db else 0
    new_task = {
        "id": max_id + 1,
        "title": task_in.title,
        "description": task_in.description,
        "assignee": task_in.assignee,
        "priority": task_in.priority,
        "status": "todo",
        "created_at": get_current_iso_time()
    }
    tasks_db.append(new_task)
    
    return {
        "statusCode": 201,
        "message": "Khởi tạo công việc mới thành công!",
        "data": new_task,
        "error": None,
        "timestamp": get_current_iso_time(),
        "path": request.url.path
    }

@app.put("/tasks/{task_id}", response_model=UnifiedResponse)
async def update_task_status(request: Request, task_id: int, status_in: TaskStatusUpdateSchema):
    target_task = None
    for task in tasks_db:
        if task["id"] == task_id:
            target_task = task
            break
            
    if not target_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": f"Lỗi: Không tìm thấy công việc có ID {task_id}!",
                "error": "ERR-TASK-03: Resource not found: Target task ID does not exist."
            }
        )
        
    if target_task["status"] == "done" and status_in.status != "done":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Lỗi: Không thể thay đổi trạng thái của công việc đã hoàn thành!",
                "error": "ERR-TASK-04: State transition denied: Cannot roll back a 'done' task."
            }
        )
        
    target_task["status"] = status_in.status
    
    return {
        "statusCode": 200,
        "message": "Cập nhật tiến độ công việc thành công!",
        "data": target_task,
        "error": None,
        "timestamp": get_current_iso_time(),
        "path": request.url.path
    }

def calculate_team_metrics() -> Tuple[int, int, float]:
    total_tasks = len(tasks_db)
    completed_tasks = sum(1 for task in tasks_db if task["status"] == "done")
    
    completion_rate_percentage = 0.0
    if total_tasks > 0:
        completion_rate_percentage = round((completed_tasks / total_tasks) * 100, 2)
        
    return total_tasks, completed_tasks, completion_rate_percentage

@app.get("/tasks/analytics/dashboard", response_model=UnifiedResponse)
async def get_dashboard_analytics(request: Request):
    total_tasks, completed_tasks, completion_rate_percentage = calculate_team_metrics()
    
    return {
        "statusCode": 200,
        "message": "Lấy số liệu thống kê hiệu suất nhóm thành công!",
        "data": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate_percentage": completion_rate_percentage
        },
        "error": None,
        "timestamp": get_current_iso_time(),
        "path": request.url.path
    }