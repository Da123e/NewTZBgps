from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Numeric, Index
from datetime import datetime
from database import Base

# 用户基础模型
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    password = Column(String(100), nullable=False, comment="密码")
    user_type = Column(String(10), nullable=False, comment="用户类型：student/teacher")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 复合索引
    __table_args__ = (
        Index('idx_user_type', 'user_type'),
    )

# 学生信息模型
class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, comment="关联用户ID")
    student_id = Column(String(20), unique=True, nullable=False, index=True, comment="学号")
    name = Column(String(50), nullable=False, comment="姓名")
    grade = Column(String(20), nullable=False, comment="年级")
    department = Column(String(50), nullable=False, comment="院(系)/部")
    major = Column(String(50), nullable=False, comment="专业")
    class_name = Column(String(50), nullable=False, comment="班级")
    device_id = Column(String(50), nullable=False, index=True, comment="设备唯一标识")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 复合索引
    __table_args__ = (
        Index('idx_student_grade', 'grade'),
        Index('idx_student_department', 'department'),
        Index('idx_student_major', 'major'),
    )

# 教师信息模型
class Teacher(Base):
    __tablename__ = "teachers"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, comment="关联用户ID")
    teacher_id = Column(String(20), unique=True, nullable=False, index=True, comment="工号")
    name = Column(String(50), nullable=False, comment="姓名")
    department = Column(String(50), nullable=False, comment="院(系)/部")
    major = Column(String(50), nullable=False, comment="所授专业")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 复合索引
    __table_args__ = (
        Index('idx_teacher_department', 'department'),
        Index('idx_teacher_major', 'major'),
    )

# 定位数据模型
class LocationRecord(Base):
    __tablename__ = "location_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(50), nullable=False, index=True, comment="设备唯一标识")
    student_id = Column(String(20), index=True, nullable=True, comment="学号")
    latitude = Column(Numeric(10, 8), nullable=False, comment="纬度")
    longitude = Column(Numeric(11, 8), nullable=False, comment="经度")
    accuracy = Column(Numeric(10, 2), default=0, comment="定位精度（米）")
    is_on_campus = Column(Boolean, default=False, comment="是否在校内")
    speed = Column(Numeric(10, 2), nullable=True, comment="速度（米/秒）")
    timestamp = Column(DateTime, default=datetime.now, comment="定位时间")
    upload_time = Column(DateTime, default=datetime.now, comment="上传时间")
    address = Column(String(255), nullable=True, comment="地址（可选）")
    
    # 复合索引
    __table_args__ = (
        Index('idx_location_timestamp', 'timestamp'),
        Index('idx_location_upload_time', 'upload_time'),
        Index('idx_location_campus_speed_time', 'is_on_campus', 'speed', 'timestamp'),
    )

# 创建数据表
def create_tables():
    from database import engine
    Base.metadata.create_all(bind=engine)
    print("数据表创建成功/已存在")

# 初始化数据表
create_tables()
