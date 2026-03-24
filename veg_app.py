import streamlit as st
import pandas as pd
import re

# ==========================================
# 1. 網頁頁面基本設定
# ==========================================
st.set_page_config(
    page_title="全台高評價素食餐廳導覽",
    page_icon="🌿",
    layout="wide"
)

# ==========================================
# 2. 數據讀取與預處理函式
# ==========================================
@st.cache_data
def load_and_process_data(file_path):
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    except FileNotFoundError:
        st.error(f"❌ 找不到檔案：{file_path}。請確保 CSV 檔案與此程式在同一目錄。")
        return None

    def parse_address_zh_tw(addr):
        if not isinstance(addr, str):
            return "未知縣市", "未知區域"
            
        addr_clean = re.sub(r'^\d{3,6}', '', addr.strip())
        addr_clean = re.sub(r'^[臺台]灣', '', addr_clean)
        
        pattern = r'^(.{2,3}?[市縣])(.{2,3}?[區市鎮鄉])'
        match = re.search(pattern, addr_clean)
        
        if match:
            city = match.group(1).strip()
            district = match.group(2).strip()
            return city, district
        else:
            return "其他", "其他"

    parsed_address = df['地址'].apply(parse_address_zh_tw)
    df['縣市'] = [p[0] for p in parsed_address]
    df['鄉鎮市區'] = [p[1] for p in parsed_address]
    
    df = df[df['縣市'] != "其他"]
    
    # 加入了「評分人數」欄位
    cols_order = ['縣市', '鄉鎮市區', '店名', '評價', '評分人數', '種類', '地址']
    existing_cols = [c for c in cols_order if c in df.columns]
    df = df[existing_cols]
    
    return df

# ==========================================
# 3. 程式主體邏輯
# ==========================================
DATA_FILE = '全台368區高評價素食餐廳.csv'
df_all = load_and_process_data(DATA_FILE)

if df_all is not None:
    st.title("🌿 全台高評價素食餐廳導覽")
    st.markdown("數據來源為 Google Maps，僅列出評價大於或等於 4.5 顆星的餐廳。")
    st.markdown("---")

    # ==========================================
    # 4. 側邊欄篩選介面 (Sidebar)
    # ==========================================
    st.sidebar.header("🔍 篩選條件")
    
    all_cities = sorted(df_all['縣市'].unique())
    selected_city = st.sidebar.selectbox("選擇縣市", ["全部"] + all_cities)

    if selected_city == "全部":
        st.sidebar.selectbox("選擇鄉鎮市區", ["請先選擇縣市"], disabled=True)
        selected_district = "全部"
    else:
        available_districts = sorted(df_all[df_all['縣市'] == selected_city]['鄉鎮市區'].unique())
        selected_district = st.sidebar.selectbox(f"選擇 {selected_city} 的區域", ["全部"] + available_districts)

    search_type = st.sidebar.text_input("輸入關鍵字搜尋種類 (例如：麵食, 咖啡, 純素)", placeholder="選填")

    # ==========================================
    # 5. 資料篩選與呈現邏輯
    # ==========================================
    filtered_df = df_all.copy()

    if selected_city != "全部":
        filtered_df = filtered_df[filtered_df['縣市'] == selected_city]
        
    if selected_district != "全部":
        filtered_df = filtered_df[filtered_df['鄉鎮市區'] == selected_district]
        
    if search_type:
        filtered_df = filtered_df[filtered_df['種類'].str.contains(search_type, case=False, na=False)]

    current_area_name = selected_city if selected_city != "全部" else "全台"
    if selected_district != "全部":
        current_area_name += selected_district
    
    total_found = len(filtered_df)
    st.markdown(f"#### 🔎 目前在 **{current_area_name}** 找到 **{total_found}** 間高評價餐廳")
    
    if total_found > 0:
        st.dataframe(
            filtered_df,
            hide_index=True, 
            column_config={
                "縣市": st.column_config.TextColumn("縣市", width="small"),
                "鄉鎮市區": st.column_config.TextColumn("區域", width="small"),
                "店名": st.column_config.TextColumn("店名", width="medium"),
                "評價": st.column_config.NumberColumn("星級", format="%.1f ⭐"),
                "評分人數": st.column_config.NumberColumn("評論數", format="%d 則"),
                "種類": st.column_config.TextColumn("種類", width="medium"),
                "地址": st.column_config.TextColumn("詳細地址", width="large")
            },
            use_container_width=True
        )
        
        csv_data = filtered_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="💾 下載當前篩選清單 (CSV)",
            data=csv_data,
            file_name=f"{current_area_name}素食餐廳清單.csv",
            mime='text/csv',
        )
    else:
        st.warning(f"📭 很抱歉，在 **{current_area_name}** 找不到符合條件的餐廳。")