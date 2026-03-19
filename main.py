import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import os
import streamlit as st
import matplotlib.pyplot as plt
import io

# --- 核心数学公式 ---

def logistic4(x, A, B, C, D):
    """4参数logistic公式"""
    return D + (A - D) / (1 + (x / C)**B)

def solve_for_x(y_value, A, B, C, D):
    """4PL 逆运算公式: x = C * ((A - y) / (y - D))**(1 / B)"""
    try:
        y = float(y_value)
        # 数学逻辑检查：比值必须大于 0 才能进行幂运算
        ratio = (A - y) / (y - D)
        if ratio <= 0:
            return np.nan
        return C * (ratio**(1/B))
    except:
        return np.nan

# --- Streamlit UI 界面 ---

def main():
    st.set_page_config(page_title="ELISA 4PL 数据处理工具", layout="wide")
    
    st.title("🧪 ELISA 数据自动化处理工具")
    st.markdown("---")

    # 初始化 session_state
    if 'params' not in st.session_state:
        st.session_state.params = None

    col1, col2 = st.columns(2)

    with col1:
        st.header("1️⃣ 曲线拟合 (Curve Fitting)")
        st.write("请上传包含 'x' 和 'y' 列的数据文件 (CSV 或 Excel)")
        
        uploaded_file = st.file_uploader("选择拟合数据文件", type=["csv", "xlsx"], key="fitting_upload")
        
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                df.columns = [str(col).strip().lower() for col in df.columns]
                
                if 'x' in df.columns and 'y' in df.columns:
                    st.write("数据预览：")
                    st.dataframe(df.head())

                    if st.button("开始拟合"):
                        df_clean = df.dropna(subset=['x', 'y'])
                        x_data = df_clean['x'].astype(float).values
                        y_data = df_clean['y'].astype(float).values

                        # 初始猜测值 [A, B, C, D]
                        p0 = [np.min(y_data), 1.0, np.median(x_data), np.max(y_data)]
                        popt, _ = curve_fit(logistic4, x_data, y_data, p0=p0, maxfev=10000)
                        
                        st.session_state.params = popt
                        A, B, C, D = popt
                        
                        st.success("✅ 拟合成功！")
                        st.write(f"**A (Bottom):** {A:.6f}")
                        st.write(f"**B (Slope) :** {B:.6f}")
                        st.write(f"**C (EC50)  :** {C:.6f}")
                        st.write(f"**D (Top)   :** {D:.6f}")

                        # 绘制图形
                        fig, ax = plt.subplots()
                        ax.scatter(x_data, y_data, label='Data Points', color='red')
                        x_fit = np.logspace(np.log10(min(x_data)), np.log10(max(x_data)), 100) if min(x_data) > 0 else np.linspace(min(x_data), max(x_data), 100)
                        y_fit = logistic4(x_fit, *popt)
                        ax.plot(x_fit, y_fit, label='4PL Fit')
                        ax.set_xscale('log')
                        ax.set_xlabel('Concentration (X)')
                        ax.set_ylabel('Response (Y)')
                        ax.legend()
                        st.pyplot(fig)
                else:
                    st.error("❌ 错误：文件中未找到 'x' 和 'y' 列！")
            except Exception as e:
                st.error(f"❌ 处理失败：{e}")

    with col2:
        st.header("2️⃣ 逆运算计算 (Calculation)")
        
        if st.session_state.params is not None:
            A, B, C, D = st.session_state.params
            st.info(f"当前参数: A={A:.4f}, B={B:.4f}, C={C:.4f}, D={D:.4f}")
            
            st.write("请上传需要计算 X 值的 Y 矩阵文件 (Excel)")
            y_file = st.file_uploader("选择 Y 矩阵文件", type=["xlsx"], key="calc_upload")
            
            if y_file:
                try:
                    df_y = pd.read_excel(y_file, header=None)
                    st.write("Y 矩阵预览：")
                    st.dataframe(df_y.head())

                    if st.button("开始计算 X 值"):
                        # 应用逆运算公式
                        df_x = df_y.map(lambda val: solve_for_x(val, A, B, C, D))
                        
                        st.write("计算结果预览：")
                        st.dataframe(df_x.head())

                        # 提供下载
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_x.to_excel(writer, index=False, header=False)
                        
                        st.download_button(
                            label="📥 下载计算结果 (Excel)",
                            data=output.getvalue(),
                            file_name="calculate_X_results.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                except Exception as e:
                    st.error(f"❌ 处理失败：{e}")
        else:
            st.warning("⚠️ 请先完成左侧的曲线拟合以获取参数。")

if __name__ == "__main__":
    main()