import datetime

# Lịch nghỉ lễ Việt Nam năm 2026 (định dạng: YYYY-MM-DD)
# Dựa trên lịch nghỉ chính thức của Chính phủ
VIETNAM_HOLIDAYS_2026 = [
    "2026-01-01",  # Tết Dương lịch
    
    # Tết Nguyên Đán (9 ngày liên tiếp)
    "2026-02-14", "2026-02-15", "2026-02-16", "2026-02-17", 
    "2026-02-18", "2026-02-19", "2026-02-20", "2026-02-21", "2026-02-22",
    
    # Giỗ Tổ Hùng Vương (Nghỉ bù do rơi vào Chủ nhật)
    "2026-04-26", "2026-04-27",
    
    # Ngày Chiến thắng (30/4) và Quốc tế Lao động (1/5)
    "2026-04-30", "2026-05-01", "2026-05-02", "2026-05-03",
    
    # Ngày Quốc khánh (Nghỉ 2 ngày: mùng 1 và mùng 2/9)
    "2026-09-01", "2026-09-02"
]

# Giờ giao dịch chuẩn (Giờ Việt Nam)
TRADING_MORNING_START = datetime.time(9, 0)
TRADING_MORNING_END = datetime.time(11, 30)
TRADING_AFTERNOON_START = datetime.time(13, 0)
TRADING_AFTERNOON_END = datetime.time(14, 45)  # Kết thúc phiên ATC

def is_trading_day(date: datetime.date = None) -> bool:
    """
    Kiểm tra xem một ngày có phải là ngày giao dịch (Thứ 2 - Thứ 6 & không phải ngày lễ) hay không.
    """
    if date is None:
        date = datetime.date.today()
        
    # 1. Kiểm tra cuối tuần (Thứ 7 = 5, Chủ nhật = 6)
    if date.weekday() >= 5:
        return False
        
    # 2. Kiểm tra ngày lễ
    if date.isoformat() in VIETNAM_HOLIDAYS_2026:
        return False
        
    return True

def is_trading_hours(dt: datetime.datetime = None) -> bool:
    """
    Kiểm tra xem thời điểm hiện tại có đang trong giờ giao dịch hay không.
    """
    if dt is None:
        # Giả sử server đang chạy ở giờ Việt Nam. Nếu không, cần dùng timezone.
        dt = datetime.datetime.now()
        
    if not is_trading_day(dt.date()):
        return False
        
    current_time = dt.time()
    
    # Phiên sáng
    if TRADING_MORNING_START <= current_time <= TRADING_MORNING_END:
        return True
        
    # Phiên chiều
    if TRADING_AFTERNOON_START <= current_time <= TRADING_AFTERNOON_END:
        return True
        
    return False

def get_last_trading_day(date: datetime.date = None) -> datetime.date:
    """
    Lấy ngày giao dịch gần nhất trước hoặc bằng ngày hiện tại.
    """
    if date is None:
        date = datetime.date.today()
        
    while not is_trading_day(date):
        date -= datetime.timedelta(days=1)
    return date
