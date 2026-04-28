import os
import hashlib
import random
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import distinct, func, and_
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta
from database import get_db
from models import LocationRecord, User, Student, Teacher
from dotenv import load_dotenv
import math

# 黄淮学院北区边界坐标（用户提供的新坐标）
HUANGHUAI_COLLEGE_NORTH_POLYGON = [
    (114.00760883217328, 33.01498104364417),  # 点  1
    (114.00954423394002, 33.015026928694994),  # 点2
    (114.01139885612503, 33.009468648207346),  # 点3
    (114.00341637439402, 33.007172907558214),  # 点4
    (114.00281526152678, 33.01302517042209),  # 点5
    (114.00760883217328, 33.01498104364417),  # 点1（闭合多边形）
]

# 定位容错半径（米）- 用于处理GPS定位误差
LOCATION_TOLERANCE = 200  # 200米容错范围，增加以处理GPS定位误差

# 射线法判断点是否在多边形内
def is_point_in_polygon(point_lon, point_lat, polygon):
    inside = False
    n = len(polygon)
    
    for i in range(n):
        j = (i + 1) % n  # 下一个顶点索引
        
        # 检查点的纬度是否在边的纬度范围内
        if ((polygon[i][1] > point_lat) != (polygon[j][1] > point_lat)):
            # 计算交点的经度
            intersect_lon = ((polygon[j][0] - polygon[i][0]) * (point_lat - polygon[i][1]) / 
                           (polygon[j][1] - polygon[i][1]) + polygon[i][0])
            
            # 如果交点在点的右侧（东边），则切换inside状态
            if point_lon < intersect_lon:
                inside = not inside
    
    return inside

# 计算两点之间的距离（米）- 使用Haversine公式
def calculate_distance(lat1, lon1, lat2, lon2):
    """
    计算两个经纬度坐标之间的距离（米）
    """
    R = 6371000  # 地球半径（米）
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

# 计算点到多边形边界的最短距离
def distance_to_polygon(latitude, longitude, polygon):
    """
    计算点到多边形边界的最短距离（米）
    """
    min_distance = float('inf')
    n = len(polygon)
    
    # 遍历多边形的每条边，包括最后一条边（从最后一个点到第一个点）
    for i in range(n):
        lon1, lat1 = polygon[i]
        lon2, lat2 = polygon[(i + 1) % n]  # 使用模运算确保闭合
        
        # 计算点到线段的距离
        distance = point_to_segment_distance(latitude, longitude, lat1, lon1, lat2, lon2)
        min_distance = min(min_distance, distance)
    
    return min_distance

# 计算点到线段的距离
def point_to_segment_distance(lat, lon, lat1, lon1, lat2, lon2):
    """
    计算点(lat, lon)到线段(lat1,lon1)-(lat2,lon2)的距离
    """
    # 将经纬度转换为米（近似）
    # 1度纬度 ≈ 111000米
    # 1度经度 ≈ 111000 * cos(纬度) 米
    lat_avg = (lat1 + lat2) / 2
    meters_per_deg_lat = 111000
    meters_per_deg_lon = 111000 * math.cos(math.radians(lat_avg))
    
    # 转换为米坐标
    px_m = lon * meters_per_deg_lon
    py_m = lat * meters_per_deg_lat
    x1_m = lon1 * meters_per_deg_lon
    y1_m = lat1 * meters_per_deg_lat
    x2_m = lon2 * meters_per_deg_lon
    y2_m = lat2 * meters_per_deg_lat
    
    # 计算点到线段的距离
    dx = x2_m - x1_m
    dy = y2_m - y1_m
    
    if dx == 0 and dy == 0:
        return math.sqrt((px_m - x1_m) ** 2 + (py_m - y1_m) ** 2)
    
    t = max(0, min(1, ((px_m - x1_m) * dx + (py_m - y1_m) * dy) / (dx ** 2 + dy ** 2)))
    
    closest_x = x1_m + t * dx
    closest_y = y1_m + t * dy
    
    return math.sqrt((px_m - closest_x) ** 2 + (py_m - closest_y) ** 2)

# 判断是否在校内（北区多边形内，带容错机制）
def is_on_campus(latitude, longitude, accuracy=0):
    """
    判断是否在校内，考虑定位误差
    accuracy: 定位精度（米），如果提供了精度信息，会结合容错半径判断
    """
    # 首先检查点是否在多边形内
    inside_polygon = is_point_in_polygon(longitude, latitude, HUANGHUAI_COLLEGE_NORTH_POLYGON)
    
    if inside_polygon:
        return True
    
    # 如果不在多边形内，检查是否在容错范围内
    # 计算点到多边形边界的距离
    distance_to_boundary = distance_to_polygon(latitude, longitude, HUANGHUAI_COLLEGE_NORTH_POLYGON)
    
    # 使用定位精度和容错半径中的较大值
    tolerance = max(accuracy, LOCATION_TOLERANCE)
    
    # 如果在容错范围内，认为在校内
    return distance_to_boundary <= tolerance

# 密码加密
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 验证密码
def verify_password(plain_password, hashed_password):
    return hash_password(plain_password) == hashed_password

# 加载环境变量
load_dotenv()

# 初始化FastAPI应用
app = FastAPI(title="位置追踪服务", version="1.0")

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)

# 配置模板目录（后台管理界面）
templates = Jinja2Templates(directory="../admin/templates")


# Pydantic模型（数据验证）
class LocationData(BaseModel):
    device_id: str
    latitude: float
    longitude: float
    accuracy: float = 0.0
    address: str = None

# 用户注册模型
class UserRegister(BaseModel):
    username: str
    password: str
    user_type: str

# 学生注册模型
class StudentRegister(BaseModel):
    username: str
    password: str
    student_id: str
    name: str
    grade: str
    department: str
    major: str
    class_name: str
    device_id: str

# 教师注册模型
class TeacherRegister(BaseModel):
    username: str
    password: str
    teacher_id: str
    name: str
    department: str
    major: str

# 用户登录模型
class UserLogin(BaseModel):
    username: str
    password: str

# 位置上传模型（支持设备ID或学号）
class LocationUpload(BaseModel):
    device_id: Optional[str] = None
    student_id: Optional[str] = None
    latitude: float
    longitude: float
    accuracy: float = 0.0
    speed: Optional[float] = None
    address: Optional[str] = None

# 学生查询模型
class StudentQuery(BaseModel):
    grade: Optional[str] = None
    department: Optional[str] = None
    major: Optional[str] = None
    student_id: Optional[str] = None


# 1. 用户注册 - 学生
@app.post("/api/register/student")
async def register_student(data: StudentRegister, db: Session = Depends(get_db)):
    try:
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == data.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 检查学号是否已存在
        existing_student = db.query(Student).filter(Student.student_id == data.student_id).first()
        if existing_student:
            raise HTTPException(status_code=400, detail="学号已存在")
        
        # 创建用户
        hashed_password = hash_password(data.password)
        user = User(
            username=data.username,
            password=hashed_password,
            user_type="student"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建学生信息
        student = Student(
            user_id=user.id,
            student_id=data.student_id,
            name=data.name,
            grade=data.grade,
            department=data.department,
            major=data.major,
            class_name=data.class_name,
            device_id=data.device_id
        )
        db.add(student)
        db.commit()
        
        return {"code": 200, "msg": "学生注册成功", "data": {"user_id": user.id, "student_id": student.student_id}}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")

# 2. 用户注册 - 教师
@app.post("/api/register/teacher")
async def register_teacher(data: TeacherRegister, db: Session = Depends(get_db)):
    try:
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == data.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 检查工号是否已存在
        existing_teacher = db.query(Teacher).filter(Teacher.teacher_id == data.teacher_id).first()
        if existing_teacher:
            raise HTTPException(status_code=400, detail="工号已存在")
        
        # 创建用户
        hashed_password = hash_password(data.password)
        user = User(
            username=data.username,
            password=hashed_password,
            user_type="teacher"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建教师信息
        teacher = Teacher(
            user_id=user.id,
            teacher_id=data.teacher_id,
            name=data.name,
            department=data.department,
            major=data.major
        )
        db.add(teacher)
        db.commit()
        
        return {"code": 200, "msg": "教师注册成功", "data": {"user_id": user.id, "teacher_id": teacher.teacher_id}}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")

# 3. 用户登录
@app.post("/api/login")
async def login(data: UserLogin, db: Session = Depends(get_db)):
    try:
        # 查找用户
        user = db.query(User).filter(User.username == data.username).first()
        if not user or not verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 根据用户类型获取详细信息
        user_info = {"user_id": user.id, "username": user.username, "user_type": user.user_type}
        
        if user.user_type == "student":
            student = db.query(Student).filter(Student.user_id == user.id).first()
            if student:
                user_info.update({
                    "student_id": student.student_id,
                    "name": student.name,
                    "grade": student.grade,
                    "department": student.department,
                    "major": student.major,
                    "class_name": student.class_name,
                    "device_id": student.device_id
                })
        elif user.user_type == "teacher":
            teacher = db.query(Teacher).filter(Teacher.user_id == user.id).first()
            if teacher:
                user_info.update({
                    "teacher_id": teacher.teacher_id,
                    "name": teacher.name,
                    "department": teacher.department,
                    "major": teacher.major
                })
        
        return {"code": 200, "msg": "登录成功", "data": user_info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")

# 4. 接收定位数据的API（支持设备ID或学号）
@app.post("/api/upload_location")
async def upload_location(data: LocationUpload, db: Session = Depends(get_db)):
    try:
        # 调试日志：打印请求数据
        print(f"[DEBUG] 上传请求数据: {data}")
        # 获取设备ID和学号，并处理空值和空字符串
        device_id = data.device_id if data.device_id and data.device_id.strip() else None
        student_id = data.student_id if data.student_id and data.student_id.strip() else None
        
        # 如果提供了学号，获取对应的设备ID
        if student_id:
            student = db.query(Student).filter(Student.student_id == student_id).first()
            if student:
                # 如果学生有设备ID，使用学生的设备ID
                if student.device_id:
                    device_id = student.device_id
                # 如果学生没有设备ID，使用请求中的设备ID（如果有的话）
                elif not device_id:
                    # 如果都没有，生成一个临时设备ID
                    device_id = f"temp_{student_id}_{datetime.now().timestamp()}"
        
        # 如果没有设备ID和学号，生成一个临时设备ID
        if not device_id and not student_id:
            # 生成一个临时设备ID
            device_id = f"temp_{datetime.now().timestamp()}_{random.randint(1000, 9999)}"
            print(f"[DEBUG] 生成临时设备ID: {device_id}")
        elif not device_id:
            # 只有学号，生成一个基于学号的临时设备ID
            device_id = f"temp_{student_id}_{datetime.now().timestamp()}"
            print(f"[DEBUG] 基于学号生成临时设备ID: {device_id}")
        
        print(f"[DEBUG] 使用的设备ID: {device_id}")
        
        # 判断是否在校内（传入定位精度）
        campus_status = is_on_campus(data.latitude, data.longitude, data.accuracy)
        
        # 创建定位记录
        record = LocationRecord(
            device_id=device_id,
            student_id=student_id,
            latitude=data.latitude,
            longitude=data.longitude,
            accuracy=data.accuracy,
            is_on_campus=campus_status,
            speed=data.speed,
            timestamp=datetime.now(),
            upload_time=datetime.now(),
            address=data.address
        )
        
        # 保存到数据库
        db.add(record)
        db.commit()
        db.refresh(record)
        
        return {"code": 200, "msg": "上传成功", "data": {"id": record.id, "is_on_campus": campus_status}}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        print(f"[ERROR] 上传位置失败: {str(e)}")
        print(f"[ERROR] 错误详情: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


# 5. 获取所有定位记录（后台管理）
@app.get("/api/get_locations", response_model=dict)
async def get_locations(db: Session = Depends(get_db), page: int = 1, size: int = 20):
    try:
        # 分页查询
        offset = (page - 1) * size
        total = db.query(LocationRecord).count()
        records = db.query(LocationRecord).order_by(LocationRecord.upload_time.desc()).offset(offset).limit(size).all()

        # 格式化数据
        data = []
        for record in records:
            # 获取学生信息
            student = db.query(Student).filter(Student.device_id == record.device_id).first()
            student_info = {"student_id": "未知", "name": "未知"}
            if student:
                student_info.update({
                    "student_id": student.student_id,
                    "name": student.name,
                    "grade": student.grade,
                    "department": student.department,
                    "major": student.major,
                    "class_name": student.class_name
                })
            
            data.append({
                "id": record.id,
                "device_id": record.device_id,
                "student_id": record.student_id or student_info["student_id"],
                "student_name": student_info["name"],
                "grade": student_info.get("grade", "未知"),
                "department": student_info.get("department", "未知"),
                "major": student_info.get("major", "未知"),
                "class_name": student_info.get("class_name", "未知"),
                "latitude": record.latitude,
                "longitude": record.longitude,
                "accuracy": record.accuracy,
                "is_on_campus": record.is_on_campus,
                "campus_status": "校内" if record.is_on_campus else "校外",
                "speed": float(record.speed) if record.speed else None,
                "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "upload_time": record.upload_time.strftime("%Y-%m-%d %H:%M:%S"),
                "address": record.address or "未获取"
            })

        return {
            "code": 200,
            "msg": "查询成功",
            "data": {
                "list": data,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

# 7. 获取单个设备的所有定位记录
@app.get("/api/get_device_locations", response_model=dict)
async def get_device_locations(device_id: str, db: Session = Depends(get_db)):
    try:
        # 查询指定设备的所有定位记录（按时间排序）
        records = db.query(LocationRecord).filter(
            LocationRecord.device_id == device_id
        ).order_by(LocationRecord.timestamp.asc()).all()

        # 格式化数据
        data = []
        for record in records:
            data.append({
                "id": record.id,
                "device_id": record.device_id,
                "student_id": record.student_id,
                "latitude": record.latitude,
                "longitude": record.longitude,
                "accuracy": record.accuracy,
                "is_on_campus": record.is_on_campus,
                "campus_status": "校内" if record.is_on_campus else "校外",
                "speed": float(record.speed) if record.speed else None,
                "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "upload_time": record.upload_time.strftime("%Y-%m-%d %H:%M:%S"),
                "address": record.address or "未获取"
            })

        return {
            "code": 200,
            "msg": "查询成功",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询设备定位失败: {str(e)}")

# 8. 获取所有学生信息（支持多条件筛选）
@app.post("/api/get_students", response_model=dict)
async def get_students(query: StudentQuery, db: Session = Depends(get_db)):
    try:
        # 调试日志：打印查询条件
        print(f"[DEBUG] 获取学生列表查询条件: {query}")
        
        # 构建查询条件
        conditions = []
        if query.grade:
            conditions.append(Student.grade == query.grade)
        if query.department:
            conditions.append(Student.department == query.department)
        if query.major:
            conditions.append(Student.major == query.major)
        if query.student_id:
            conditions.append(Student.student_id.like(f"%{query.student_id}%"))
        
        # 查询学生信息
        if conditions:
            students = db.query(Student).filter(and_(*conditions)).all()
        else:
            students = db.query(Student).all()
        
        # 获取每个学生的最新位置
        student_list = []
        for student in students:
            # 获取最新位置记录（只有设备ID存在且不为空时才查询）
            latest_location = None
            if student.device_id and student.device_id.strip():
                latest_location = db.query(LocationRecord).filter(
                    LocationRecord.device_id == student.device_id
                ).order_by(LocationRecord.timestamp.desc()).first()
            
            location_info = {
                "latitude": "",
                "longitude": "",
                "accuracy": 0,
                "is_on_campus": False,
                "campus_status": "未知",
                "address": "未获取",
                "timestamp": "",
                "speed": None
            }
            
            if latest_location:
                location_info.update({
                    "latitude": latest_location.latitude,
                    "longitude": latest_location.longitude,
                    "accuracy": latest_location.accuracy,
                    "is_on_campus": latest_location.is_on_campus,
                    "campus_status": "校内" if latest_location.is_on_campus else "校外",
                    "address": latest_location.address or "未获取",
                    "timestamp": latest_location.timestamp.strftime("%Y-%m-%d %H:%M:%S") if latest_location.timestamp else "",
                    "speed": float(latest_location.speed) if latest_location.speed else None
                })
            
            student_list.append({
                "student_id": student.student_id,
                "name": student.name,
                "grade": student.grade,
                "department": student.department,
                "major": student.major,
                "class_name": student.class_name,
                "device_id": student.device_id,
                "location": location_info
            })
        
        return {
            "code": 200,
            "msg": "查询成功",
            "data": student_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询学生信息失败: {str(e)}")

# 9. 获取单个学生的位置历史记录
@app.get("/api/get_student_locations", response_model=dict)
async def get_student_locations(student_id: str, db: Session = Depends(get_db)):
    try:
        # 查找学生
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            raise HTTPException(status_code=400, detail="学号不存在")
        
        # 查询最近100次位置记录
        records = db.query(LocationRecord).filter(
            LocationRecord.device_id == student.device_id
        ).order_by(LocationRecord.timestamp.desc()).limit(100).all()
        
        # 格式化数据
        data = []
        for record in records:
            data.append({
                "id": record.id,
                "student_id": student_id,
                "student_name": student.name,
                "latitude": record.latitude,
                "longitude": record.longitude,
                "accuracy": record.accuracy,
                "is_on_campus": record.is_on_campus,
                "campus_status": "校内" if record.is_on_campus else "校外",
                "speed": float(record.speed) if record.speed else None,
                "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "upload_time": record.upload_time.strftime("%Y-%m-%d %H:%M:%S"),
                "address": record.address or "未获取"
            })
        
        return {
            "code": 200,
            "msg": "查询成功",
            "data": {
                "student_info": {
                    "student_id": student.student_id,
                    "name": student.name,
                    "grade": student.grade,
                    "department": student.department,
                    "major": student.major,
                    "class_name": student.class_name
                },
                "location_records": data
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询学生定位历史失败: {str(e)}")


# 3. 后台管理界面（列表视图）
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# 新增：地图视图页面
@app.get("/admin/map", response_class=HTMLResponse)
async def admin_map(request: Request):
    return templates.TemplateResponse("map.html", {"request": request})


# 10. 获取超速报警学生列表（校外学生速度超过80码约等于35.76米/秒）
@app.get("/api/get_speeding_alerts", response_model=dict)
async def get_speeding_alerts(
    teacher_major: str = None,
    teacher_department: str = None,
    db: Session = Depends(get_db)
):
    try:
        # 80码 = 80 * 0.44704 ≈ 35.76 米/秒
        SPEED_THRESHOLD = 35.76
        
        # 计算30天前的时间
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # 构建查询条件 - 只查询校外学生，且时间在30天内
        query = db.query(LocationRecord).filter(
            LocationRecord.is_on_campus == False,
            LocationRecord.speed >= SPEED_THRESHOLD,
            LocationRecord.timestamp >= thirty_days_ago
        )
        
        # 如果指定了教师的专业和院系，只查询该教师所授专业的学生
        if teacher_major and teacher_department:
            # 获取该专业和院系的所有学生
            students = db.query(Student).filter(
                Student.major == teacher_major,
                Student.department == teacher_department
            ).all()
            
            student_device_ids = [s.device_id for s in students if s.device_id]
            if student_device_ids:
                query = query.filter(LocationRecord.device_id.in_(student_device_ids))
            else:
                # 如果没有找到对应学生，返回空列表
                return {
                    "code": 200,
                    "msg": "查询成功",
                    "data": []
                }
        
        # 获取所有超速记录，按时间降序排列
        from sqlalchemy import desc
        records = query.order_by(desc(LocationRecord.timestamp)).all()
        
        # 构建报警数据
        alerts = []
        for record in records:
            # 获取学生信息
            student = db.query(Student).filter(Student.device_id == record.device_id).first()
            
            # 计算速度（转换为码）
            speed_mps = float(record.speed) if record.speed else 0
            speed_mph = speed_mps / 0.44704  # 转换为英里/小时（码）
            
            alert_data = {
                "id": record.id,
                "device_id": record.device_id,
                "student_id": record.student_id or (student.student_id if student else "未知"),
                "student_name": student.name if student else "未知",
                "grade": student.grade if student else "未知",
                "department": student.department if student else "未知",
                "major": student.major if student else "未知",
                "class_name": student.class_name if student else "未知",
                "latitude": record.latitude,
                "longitude": record.longitude,
                "speed_mps": round(speed_mps, 2),
                "speed_mph": round(speed_mph, 2),
                "address": record.address or "未获取",
                "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "alert_level": "严重" if speed_mph > 100 else "警告"
            }
            alerts.append(alert_data)
        
        return {
            "code": 200,
            "msg": "查询成功",
            "data": alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询超速报警失败: {str(e)}")

# 4. 健康检查接口
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "location-tracker"}


# 启动服务
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=os.getenv("API_HOST"),
        port=int(os.getenv("API_PORT")),
        workers=4,  # 生产环境多进程
        reload=False  # 生产环境关闭自动重载
    )