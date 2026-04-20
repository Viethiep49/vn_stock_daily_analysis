# Prompt 01 — Thêm Investor Persona Skills (Buffett / Lynch / Graham / Munger / Klarman)

## Mục tiêu
Bổ sung 5 persona đại gia đầu tư dưới dạng **skill `.md`** vào `src/agents/skills/` để pipeline agent hiện tại (`src/agents/skill_agent.py`) có thể chọn và inject vào prompt LLM. Lấy cảm hứng từ FinceptTerminal (37 AI agents: Buffett, Graham, Lynch, Munger, Klarman, Marks…) nhưng triển khai **thuần Python, MIT-compatible** (không copy code AGPL).

## Bối cảnh codebase (đọc kỹ, đừng khám phá thêm nếu không cần)
- Skills đang tồn tại: `src/agents/skills/CANSLIM.md`, `src/agents/skills/VSA.md`
- Loader: `src/agents/skills/registry.py` — tự động liệt kê mọi file `*.md` trong thư mục và trả nội dung raw qua `get_skill_content(name)`. **Không cần sửa registry** — chỉ cần đặt file `.md` đúng chỗ là xong.
- Mẫu cấu trúc của CANSLIM.md: có `# Title`, `## Giới thiệu / Acronym`, bullet nguyên tắc, `## Execution Rules`.
- Thị trường đích: **Việt Nam (HOSE/HNX)**, đồng VND, dữ liệu từ `vnstock` (không có option, ít ETF, thanh khoản thấp hơn US).

## Yêu cầu

### 1. Tạo 5 file markdown tại `src/agents/skills/`

| File | Persona | Góc nhìn chủ đạo |
|---|---|---|
| `BUFFETT.md` | Warren Buffett | Giá trị dài hạn, moat, ROE bền vững, giá hợp lý |
| `LYNCH.md` | Peter Lynch | Tăng trưởng PEG < 1, "invest in what you know", phân nhóm stock |
| `GRAHAM.md` | Benjamin Graham | Margin of Safety, NCAV, P/B thấp, phòng thủ |
| `MUNGER.md` | Charlie Munger | Mental models, inversion, chất lượng > giá rẻ |
| `KLARMAN.md` | Seth Klarman | Deep value, tình huống đặc biệt, tập trung rủi ro mất vốn |

### 2. Cấu trúc BẮT BUỘC cho mỗi file
```markdown
# {Tên Persona} Investing Skill

> Một đoạn quote/triết lý đặc trưng của persona đó (1–2 câu).

## Triết lý cốt lõi
- 4–6 bullet nêu nguyên tắc chính của persona.

## Checklist khi đánh giá 1 cổ phiếu
1. Câu hỏi 1 persona sẽ hỏi (ví dụ Buffett: "Tôi có hiểu doanh nghiệp này không?")
2. … (5–8 câu hỏi tổng, mỗi câu kèm chỉ số/ngưỡng định lượng khi có thể — ROE > 15%, P/E < 15, debt/equity < 0.5, v.v.)

## Tín hiệu MUA / BÁN / TRÁNH
- **MUA**: điều kiện cụ thể
- **TRÁNH**: red flags cụ thể
- **BÁN**: khi thesis bị phá vỡ như thế nào

## Điều chỉnh cho thị trường Việt Nam
- 2–4 bullet lưu ý đặc thù VN: thanh khoản, chuẩn kế toán VAS vs IFRS, cổ đông nhà nước, room ngoại, T+2.5, giới hạn biên độ HOSE/HNX.

## Output format kỳ vọng
Khi LLM dùng skill này, yêu cầu trả về JSON:
{
  "persona": "{NAME}",
  "verdict": "BUY" | "HOLD" | "AVOID",
  "conviction": 0-100,
  "thesis": "1-2 câu",
  "red_flags": ["…"],
  "key_metrics_checked": {"roe": 18.2, "pe": 12.5, …}
}
```

### 3. Ràng buộc nội dung
- Tiếng Việt xen kỹ thuật tiếng Anh (giữ tên chỉ số: ROE, P/E, PEG, NCAV, FCF, moat, margin of safety).
- Không đạo văn nguyên văn sách của Buffett/Graham — diễn đạt lại bằng ngôn ngữ của bạn.
- Mỗi file 80–150 dòng. Đừng quá dài.
- Ngưỡng định lượng phải thực tế với VN: ví dụ Graham NCAV cực hiếm ở VN, ghi chú điều đó; Lynch PEG có thể nới lên 1.2 cho midcap VN.

## Không làm
- Đừng sửa `registry.py` — nó đã auto-discover.
- Đừng thêm dependencies.
- Đừng tạo file Python mới.
- Đừng sửa `skill_agent.py`, `pipeline.py` — chỉ thêm data content.

## Kiểm tra hoàn thành
Sau khi tạo xong, chạy nhanh trong Python REPL:
```python
from src.agents.skills.registry import list_skills, get_skill_content
skills = list_skills()
assert {"BUFFETT", "LYNCH", "GRAHAM", "MUNGER", "KLARMAN"}.issubset(set(skills))
for s in ["BUFFETT", "LYNCH", "GRAHAM", "MUNGER", "KLARMAN"]:
    content = get_skill_content(s)
    assert "Triết lý cốt lõi" in content
    assert "Checklist" in content
    assert "Output format" in content
print("OK:", skills)
```

## Commit
Một commit duy nhất:
```
feat(agents): add 5 legendary investor persona skills (Buffett/Lynch/Graham/Munger/Klarman)
```
