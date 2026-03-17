import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import os

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

# --- 功能模块 ---

def perform_fitting():
    """步骤 1: 曲线拟合获取参数"""
    print("\n>>> 步骤 1: 4PL 曲线拟合 (获取 A, B, C, D)")
    print("请在 Excel 中选中并复制包含 'x' 和 'y' 表头的数据区域...")
    input("确认已复制后，请按【回车】继续...")

    try:
        df = pd.read_clipboard()
        df.columns = [str(col).strip().lower() for col in df.columns]
        
        if 'x' not in df.columns or 'y' not in df.columns:
            print("❌ 错误：剪贴板数据中未找到 'x' 和 'y' 表头！")
            return None

        df = df.dropna(subset=['x', 'y'])
        x_data = df['x'].astype(float).values
        y_data = df['y'].astype(float).values

        # 初始猜测值 [A, B, C, D]
        p0 = [np.min(y_data), 1.0, np.median(x_data), np.max(y_data)]
        popt, _ = curve_fit(logistic4, x_data, y_data, p0=p0, maxfev=10000)
        
        A, B, C, D = popt
        print("\n" + "="*40)
        print("✅ 拟合成功！")
        print(f"A (Bottom): {A:.6f}")
        print(f"B (Slope) : {B:.6f}")
        print(f"C (EC50)  : {C:.6f}")
        print(f"D (Top)   : {D:.6f}")
        print("="*40)
        return popt
    except Exception as e:
        print(f"❌ 拟合失败：{e}")
        return None

def perform_calculation(params):
    """步骤 2: 使用拟合参数计算 X 值"""
    A, B, C, D = params
    print("\n>>> 步骤 2: 矩阵逆运算 (计算 X 值)")
    print(f"已自动载入参数: A={A:.4f}, B={B:.4f}, C={C:.4f}, D={D:.4f}")
    print("请在 Excel 中选中并复制您的 y 值矩阵区域...")
    input("确认已复制后，请按【回车】开始计算...")

    try:
        df_y = pd.read_clipboard(sep='\t', header=None)
        if df_y.empty:
            print("❌ 错误：未检测到有效数据！")
            return

        print(f"正在处理 {df_y.shape[0]}x{df_y.shape[1]} 矩阵...")
        
        # 应用逆运算公式
        df_x = df_y.map(lambda val: solve_for_x(val, A, B, C, D))

        output_name = "calculate_X_results.xlsx"
        df_x.to_excel(output_name, index=False, header=False)
        
        print("\n" + "-"*30)
        print(f"✨ 计算完成！结果已保存至 Excel。")
        print(f"路径: {os.path.abspath(output_name)}")
        
        if os.name == 'nt':
            os.startfile(output_name)
    except Exception as e:
        print(f"❌ 处理失败：{e}")

# --- 主程序入口 ---

def main():
    print("="*50)
    print("药理学数据自动化处理工具 - 4PL 拟合与逆算一体化")
    print("="*50)
    
    # 执行拟合
    params = perform_fitting()
    
    if params is not None:
        choice = input("\n是否继续使用上述参数计算矩阵 X 值？(Y/N): ").strip().lower()
        if choice == 'y':
            perform_calculation(params)
        else:
            print("程序结束。")
    else:
        print("未能获取拟合参数，程序退出。")

if __name__ == "__main__":
    main()