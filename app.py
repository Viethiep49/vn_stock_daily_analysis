import streamlit as st
import pandas as pd
from src.core.analyzer import Analyzer
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="VN Stock Daily Analysis Dashboard",
    page_icon="📈",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    .report-card {
        padding: 20px;
        border-radius: 10px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Application Header
st.title("🇻🇳 VN Stock Daily Analysis")
st.markdown("Hệ thống AI phân tích chứng khoán Việt Nam hàng ngày (HOSE/HNX/UPCOM)")

# Sidebar for configuration
with st.sidebar:
    st.header("Cài đặt")
    symbol_input = st.text_input("Mã cổ phiếu", value="VNM.HO", help="Ví dụ: VNM.HO, FPT.HO, ACB.HN").upper()
    analyze_button = st.button("🚀 Bắt đầu phân tích")
    
    st.divider()
    st.info("""
    **Hướng dẫn:**
    1. Nhập mã cổ phiếu theo định dạng `SYMBOL.EXCHANGE`
    2. Nhấn nút Phân tích.
    3. Kết quả sẽ tự động hiển thị sau vài giây.
    """)

# Main Content Area
if analyze_button:
    with st.spinner(f"Đang phân tích mã {symbol_input}..."):
        try:
            # Initialize Analyzer
            analyzer = Analyzer()
            result = analyzer.analyze(symbol_input)
            
            if result.get("status") == "failed":
                st.error(f"❌ Lỗi: {result.get('error')}")
            else:
                # Layout columns
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.subheader("📊 Thông tin cơ bản")
                    info = result.get("info", {})
                    quote = result.get("quote", {})
                    
                    # metrics
                    price = quote.get('price', 0) * 1000
                    change = quote.get('change', 0) * 1000
                    change_pct = quote.get('change_pct', 0)
                    
                    st.metric("Giá hiện tại", f"{price:,.0f} đ", f"{change:+,.0f} đ ({change_pct:+.2f}%)")
                    
                    st.write(f"**🏢 Công ty:** {info.get('company_name')}")
                    st.write(f"**🏗️ Ngành:** {info.get('industry')}")
                    st.write(f"**🏛️ Sàn:** {info.get('exchange')}")
                    st.write(f"**📦 Khối lượng:** {quote.get('volume', 0):,.0f} cp")
                    
                    # Circuit Breaker
                    cb = result.get("circuit_breaker")
                    if cb and cb.get('warning'):
                        st.warning(cb.get('warning'))
                    
                    st.divider()
                    st.write(f"📈 **Chỉ số kỹ thuật:**")
                    st.code(result.get("tech_summary"))

                with col2:
                    st.subheader("🤖 Phân tích từ AI Agent")
                    st.markdown(f"""
                    <div class="report-card">
                        {result.get("llm_analysis")}
                    </div>
                    """, unsafe_allow_html=True)
                    
                st.success("✅ Phân tích hoàn tất!")
                
        except Exception as e:
            st.error(f"Đã xảy ra lỗi hệ thống: {str(e)}")
else:
    # Placeholder state
    st.info("Vui lòng nhập mã cổ phiếu ở thanh bên trái và nhấn nút 'Bắt đầu phân tích'.")

# Footer
st.divider()
st.caption("Powered by vnstock & LiteLLM | Dữ liệu mang tính chất tham khảo.")
