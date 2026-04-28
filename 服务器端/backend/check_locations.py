from app import engine
from models import LocationRecord
from sqlalchemy.orm import sessionmaker

# 创建数据库会话
Session = sessionmaker(bind=engine)
session = Session()

try:
    print('最近的10条位置记录:')
    # 查询最近的10条位置记录
    records = session.query(LocationRecord).order_by(LocationRecord.id.desc()).limit(10).all()
    
    if records:
        for record in records:
            print(f'ID: {record.id}, DeviceID: {record.device_id}, StudentID: {record.student_id}, Lat: {record.latitude}, Lon: {record.longitude}, Time: {record.timestamp}')
    else:
        print('没有找到位置记录')
finally:
    # 关闭会话
    session.close()