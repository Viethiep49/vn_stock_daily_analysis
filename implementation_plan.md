# 🇻🇳 VN Stock Daily Analysis — Bản Kế Hoạch Triển Khai (Cập Nhật 19/04/2026)

> **Mục tiêu:** Xây dựng hệ thống AI Agent phân tích chứng khoán Việt Nam hàng ngày, lấy cảm hứng trực tiếp từ `ZhuLinsen/daily_stock_analysis`.

---

## 📊 Trạng Thái Tổng Quan (Current Status)

| Phase | Nội dung | Trạng thái | Ghi chú |
|-------|----------|-----------|---------|
| **Phase 1** | Foundation: Data Provider + Core AI | ✅ Done | Hoàn thiện vnstock provider & LiteLLM. |
| **Phase 2** | Notification + Strategies + Scheduling | ✅ Done | Telegram/Discord working. YAML strategies ready. |
| **Phase 3** | Web UI Dashboard | 🔄 In Progress | Streamlit (`app.py`) ✅. React ⏳. |
| **Phase 4** | Multi-Agent + Chat Interface | 🔄 In Progress | Core Agents ✅. Integration ✅. Chat/Portfolio ⏳. |

---

## 🧩 Chi Tiết Tiến Độ Theo Module

### 1. Module Đã Hoàn Thành (Foundational)
- **Data Provider:** Hỗ trợ `vnstock` với cơ chế fallback.
- **Core Analyzer:** Hệ thống gộp điểm (Scoring Engine) và nhận định AI.
- **Strategies:** 6 chiến lược mặc định (MA, RSI, Breakout, S/R, BB, VN30).
- **Notifier:** Discord (Rich Embeds) + Telegram (Markdown), đã hỗ trợ định dạng điểm số mới.
- **Utilities:** 
    - `Validator`: Chuẩn hoá mã chứng khoán (VNM.HO, vnm, etc.).
    - `Cache`: Hệ thống caching local cho dữ liệu thị trường (SQLite/File).
    - `Circuit Breaker`: Tự động cảnh báo giá trần/sàn và trạng thái bất thường.

### 2. Module Đang Triển Khai (Active Development)
- **Multi-Agent Flow:** Pipeline 5-step (Technical -> Intel -> Risk -> Specialist -> Decision) đã có code core nhưng cần tinh chỉnh prompt thực tế.
- **Web Interface:** Bản Streamlit hiện tại cho phép phân tích mã đơn lẻ. Cần mở rộng sang view Dashboard tổng hợp.

### 3. Module Tồn Đọng & Cần Bổ Sung (Pending/Issues)
- **Trading Calendar:** ✅ Hoàn thành. Đã có lịch nghỉ lễ 2026 và tích hợp vào `main.py`.
- **Portfolio Management:** Lưu trữ danh sách mã cổ phiếu người dùng quan tâm (Watchlist).
- **Backtesting Logic:** Đối chiếu dự đoán của AI với thực tế sau T+2/T+3.
- **LLM Response Cache:** Chưa lưu kết quả nhận định AI để tiết kiệm token khi truy vấn lại trong ngày.

---

## 🗺️ Lộ Trình Tiếp Theo (Next Steps)

1. **[URGENT]** Khởi tạo `src/market/trading_calendar.py` và kết nối vào `main.py`.
2. **[IMPROVEMENT]** Tích hợp `src/utils/cache.py` sâu hơn vào `Data Provider` để giảm tải API call.
3. **[FEATURE]** Thêm chức năng quản lý danh sách theo dõi (Watchlist) dạng file JSON/YAML đơn giản.
4. **[UI]** Hoàn thiện Dashboard tổng hợp trên Streamlit (hiển thị bảng điểm của nhiều mã cùng lúc).

---

## 🛠️ Đề Xuất Cải Tiến Kỹ Thuật (Proposed vs Status)

| Hạng mục | Trạng thái | Ghi chú |
|----------|-----------|---------|
| ✅ Symbol Validator | ✅ Done | Đã có trong `src/utils/validator.py` |
| ✅ Circuit Breaker Handler | ✅ Done | Đã có trong `src/market/circuit_breaker.py` |
| ✅ Local Caching Layer | ✅ Done | Đã có trong `src/utils/cache.py` |
| ✅ LLM Response Cache | ⏳ Pending | Cần thêm logic lưu hash prompt/response |
| ✅ Trading Calendar | ✅ Done | Đã tích hợp lịch nghỉ lễ 2026 |
| ✅ Parallel Agent Execution | 🟡 Future | Tối ưu thời gian chạy pipeline |

---
