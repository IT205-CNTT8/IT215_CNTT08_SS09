from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
app = FastAPI(title="Quan ly khoa hoc - Ban co ban")

courses_db = [
    {
        "id": 1,
        "course_name": "FastAPI Masterclass",
        "duration_hours": 32,
        "price": 1500000,
        "status": "active",
        "created_at": "2026-07-01T02:00:00Z",
    },
    {
        "id": 2,
        "course_name": "NextJS Next-Level",
        "duration_hours": 45,
        "price": 1800000,
        "status": "active",
        "created_at": "2026-07-01T03:15:00Z",
    },
]
def tao_id_moi():
    """
    Tao ra 1 ID moi cho khoa hoc, bang cach lay ID lon nhat hien co + 1.
    Vi du: neu dang co id 1 va 2 -> ID moi se la 3.
    """
    if len(courses_db) == 0:
        return 1

    danh_sach_id = []
    for course in courses_db:
        danh_sach_id.append(course["id"])

    id_lon_nhat = max(danh_sach_id)
    return id_lon_nhat + 1


def lay_thoi_gian_hien_tai():
    """Tra ve thoi gian hien tai dang chuoi, vi du: 2026-07-06T10:30:00Z"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tao_phan_hoi(status_code, message, data, error, path):
    """
    Day la ham QUAN TRONG NHAT bai nay.
    No dong goi MOI cau tra loi (du thanh cong hay loi) theo dung 1 khuon mau
    gom 6 truong: statusCode, message, data, error, timestamp, path.

    Lam vay de FRONT-END chi can doc 1 kieu du lieu duy nhat cho tat ca API,
    khong can viet nhieu cach xu ly khac nhau cho tung loai response.
    """
    noi_dung = {
        "statusCode": status_code,
        "message": message,
        "data": data,
        "error": error,
        "timestamp": lay_thoi_gian_hien_tai(),
        "path": path,
    }
    return JSONResponse(status_code=status_code, content=noi_dung)
class CourseCreateRequest(BaseModel):
    course_name: str = Field(..., min_length=5)
    duration_hours: int = Field(..., gt=0)
    price: int = Field(..., ge=0)

@app.exception_handler(HTTPException)
def xu_ly_loi_http(request: Request, exc: HTTPException):
    thong_tin_loi = exc.detail 

    return tao_phan_hoi(
        status_code=exc.status_code,
        message=thong_tin_loi["message"],
        data=None,
        error=thong_tin_loi["error"],
        path=request.url.path,
    )
@app.exception_handler(RequestValidationError)
def xu_ly_loi_validate(request: Request, exc: RequestValidationError):
    danh_sach_loi = exc.errors()
    cac_thong_bao = []
    for loi in danh_sach_loi:
        ten_truong = loi["loc"][-1] 
        noi_dung_loi = loi["msg"]  
        cac_thong_bao.append(f"{ten_truong}: {noi_dung_loi}")

    chuoi_loi = "; ".join(cac_thong_bao)

    return tao_phan_hoi(
        status_code=422,
        message="Lỗi: Dữ liệu đầu vào không hợp lệ!",
        data=None,
        error=f"ERR-EDU-00: {chuoi_loi}",
        path=request.url.path,
    )

@app.get("/courses")
def lay_danh_sach_khoa_hoc(request: Request):
    return tao_phan_hoi(
        status_code=200,
        message="Lấy danh sách khóa học thành công!",
        data=courses_db,
        error=None,
        path=request.url.path,
    )

@app.post("/courses", status_code=201)
def tao_khoa_hoc_moi(request: Request, du_lieu_gui_len: CourseCreateRequest):

    ten_moi_viet_thuong = du_lieu_gui_len.course_name.strip().lower()

    da_ton_tai = False
    for course in courses_db:
        ten_cu_viet_thuong = course["course_name"].strip().lower()
        if ten_cu_viet_thuong == ten_moi_viet_thuong:
            da_ton_tai = True
            break  

    if da_ton_tai:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Lỗi: Tên khóa học này đã tồn tại trong danh mục đào tạo!",
                "error": "ERR-EDU-01: Course name duplicates an existing record in memory array.",
            },
        )

    khoa_hoc_moi = {
        "id": tao_id_moi(),
        "course_name": du_lieu_gui_len.course_name,
        "duration_hours": du_lieu_gui_len.duration_hours,
        "price": du_lieu_gui_len.price,
        "status": "active",  
        "created_at": lay_thoi_gian_hien_tai(),
    }
    courses_db.append(khoa_hoc_moi)

    return tao_phan_hoi(
        status_code=201,
        message="Tạo mới khóa học thành công!",
        data=khoa_hoc_moi,
        error=None,
        path=request.url.path,
    )
@app.delete("/courses/{course_id}")
def xoa_khoa_hoc(request: Request, course_id: int):
    vi_tri_can_xoa = None
    for i in range(len(courses_db)):
        if courses_db[i]["id"] == course_id:
            vi_tri_can_xoa = i
            break
    if vi_tri_can_xoa is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Lỗi: Không tìm thấy mã khóa học yêu cầu để xóa!",
                "error": "ERR-EDU-02: Target course ID can not be found.",
            },
        )

    courses_db.pop(vi_tri_can_xoa)

    return tao_phan_hoi(
        status_code=200,
        message="Xóa khóa học thành công!",
        data=None,
        error=None,
        path=request.url.path,
    )
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)