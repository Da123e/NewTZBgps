-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS location_db DEFAULT CHARACTER SET utf8mb4;

-- 使用数据库
USE location_db;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    password VARCHAR(100) NOT NULL COMMENT '密码',
    user_type VARCHAR(10) NOT NULL COMMENT '用户类型：student/teacher',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username),
    INDEX idx_user_type (user_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 学生信息表
CREATE TABLE IF NOT EXISTS students (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '学生ID',
    user_id INT NOT NULL COMMENT '关联用户ID',
    student_id VARCHAR(20) UNIQUE NOT NULL COMMENT '学号',
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    grade VARCHAR(20) NOT NULL COMMENT '年级',
    department VARCHAR(50) NOT NULL COMMENT '院(系)/部',
    major VARCHAR(50) NOT NULL COMMENT '专业',
    class_name VARCHAR(50) NOT NULL COMMENT '班级',
    device_id VARCHAR(50) NOT NULL COMMENT '设备唯一标识',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_student_id (student_id),
    INDEX idx_device_id (device_id),
    INDEX idx_grade (grade),
    INDEX idx_department (department),
    INDEX idx_major (major)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生信息表';

-- 教师信息表
CREATE TABLE IF NOT EXISTS teachers (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '教师ID',
    user_id INT NOT NULL COMMENT '关联用户ID',
    teacher_id VARCHAR(20) UNIQUE NOT NULL COMMENT '工号',
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    department VARCHAR(50) NOT NULL COMMENT '院(系)/部',
    major VARCHAR(50) NOT NULL COMMENT '所授专业',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_teacher_id (teacher_id),
    INDEX idx_department (department),
    INDEX idx_major (major)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师信息表';

-- 定位记录表
CREATE TABLE IF NOT EXISTS location_records (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
    device_id VARCHAR(50) NOT NULL COMMENT '设备唯一标识',
    student_id VARCHAR(20) DEFAULT NULL COMMENT '学号',
    latitude DECIMAL(10, 8) NOT NULL COMMENT '纬度',
    longitude DECIMAL(11, 8) NOT NULL COMMENT '经度',
    accuracy DECIMAL(10, 2) DEFAULT 0 COMMENT '定位精度（米）',
    is_on_campus BOOLEAN DEFAULT FALSE COMMENT '是否在校内',
    speed DECIMAL(10, 2) DEFAULT NULL COMMENT '速度（米/秒）',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '定位时间',
    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    address VARCHAR(255) DEFAULT NULL COMMENT '地址（可选）',
    INDEX idx_device_id (device_id),
    INDEX idx_student_id (student_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_upload_time (upload_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='定位记录表';