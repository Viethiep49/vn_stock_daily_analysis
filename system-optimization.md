# System Optimization Plan

## Overview
Quét toàn diện dự án, tối ưu hóa hiệu suất API (giảm độ trễ), thiết kế lại Dashboard UI/UX lấy cảm hứng từ Simplize (trực quan, mượt mà hơn), và verify/refactor lại logic của bộ nguồn tin (News Scraper) để đảm bảo độ tin cậy, không phát sinh lỗi. Đồng thời rà soát và refactor clean code toàn bộ dự án.

## Project Type
WEB & BACKEND (Fullstack)

## Success Criteria
- [ ] API phản hồi nhanh hơn, giảm latency trong các lời gọi lấy dữ liệu và phân tích.
- [ ] Dashboard Frontend (Next.js) được cải tiến UI/UX với phong cách hiện đại, trực quan (Simplize-inspired).
- [ ] Logic lấy tin tức (`vn_news_scraper.py`) được xác minh tính ổn định, có thêm các cơ chế fallback/logging nếu cần.
- [ ] Codebase gọn gàng, clean code.
- [ ] Vượt qua các bài kiểm tra từ `checklist.py`.

## Tech Stack
- **Backend:** FastAPI, Python (Agents)
- **Frontend:** Next.js, React, TailwindCSS
- **Scraper:** Python (BeautifulSoup / requests / vnstock)

## File Structure
- `api/main.py` & `src/` (Backend/Scraping logic)
- `frontend/src/components/` & `frontend/src/app/` (Frontend UI)
- `src/news/vn_news_scraper.py` (News Scraping)

## Task Breakdown

| ID  | Name | Agent | Skills | Priority | Dependencies | INPUT → OUTPUT → VERIFY |
|---|---|---|---|---|---|---|
| T1 | **API Performance Review & Optimization** | `backend-specialist` | `performance-profiling`, `python-patterns` | P1 | None | Phân tích `api/main.py` và các module liên quan → Refactor tối ưu caching, async/await, giảm I/O block → Kiểm tra thời gian phản hồi (Latency test). |
| T2 | **News Scraper Verification** | `backend-specialist` | `systematic-debugging` | P1 | None | Đọc `src/news/vn_news_scraper.py` → Rà soát logic cào dữ liệu, timeout, fallback → Viết script test hoặc chạy thử scraper để đảm bảo không lỗi. |
| T3 | **Dashboard UI/UX Redesign (Simplize Inspired)** | `frontend-specialist` | `frontend-design`, `tailwind-patterns` | P2 | T1 | Lấy ý tưởng UI từ Simplize, rà soát `frontend/src/components/StockDashboard.tsx` → Thiết kế lại layout, chart, data table trực quan, data fetching mượt mà → Chạy thử frontend và verify UI. |
| T4 | **Clean Code Refactoring** | `orchestrator` | `clean-code` | P3 | T1, T2, T3 | Rà soát toàn bộ project → Loại bỏ code thừa, comments không cần thiết, chuẩn hóa naming convention → `npm run lint` & `python -m flake8`. |

## ✅ PHASE X: Verification
- [x] Socratic Gate was respected
- [x] `npm run lint` & `tsc` pass for Frontend
- [x] Python backend chạy ổn định không lỗi
- [x] Chạy `python .agent/scripts/checklist.py .` hoặc tương đương

## ✅ PHASE X COMPLETE
- Lint: ✅ Pass
- Security: ✅ No critical issues
- Build: ✅ Success
- Date: 2026-04-22
