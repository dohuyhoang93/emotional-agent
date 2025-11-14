import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from typing import Dict

def plot_mean_with_std(df: pd.DataFrame, x_col: str, y_col: str, title: str, y_label: str, output_path: str, window_size: int = 50):
    """
    Vẽ biểu đồ đường trung bình với vùng đổ bóng thể hiện độ lệch chuẩn.
    Dữ liệu được làm mượt bằng cửa sổ trượt.
    """
    plt.figure(figsize=(12, 6))

    # Tính toán trung bình và độ lệch chuẩn theo episode
    # Group by episode and then calculate mean/std across runs
    grouped = df.groupby(x_col)[y_col]
    mean_val = grouped.mean()
    std_val = grouped.std()

    # Làm mượt dữ liệu
    mean_val_smooth = mean_val.rolling(window=window_size, min_periods=1).mean()
    std_val_smooth = std_val.rolling(window=window_size, min_periods=1).mean()

    # Vẽ đường trung bình
    plt.plot(mean_val_smooth.index, mean_val_smooth, label=f'Trung bình (làm mượt {window_size})', color='blue')

    # Vẽ vùng đổ bóng cho độ lệch chuẩn
    lower_bound = mean_val_smooth - std_val_smooth
    upper_bound = mean_val_smooth + std_val_smooth
    plt.fill_between(mean_val_smooth.index, lower_bound, upper_bound, color='blue', alpha=0.2, label=f'Độ lệch chuẩn (làm mượt {window_size})')

    plt.title(title)
    plt.xlabel(x_col.replace('_', ' ').title())
    plt.ylabel(y_label)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def plot_exploration_rate(df: pd.DataFrame, x_col: str, y_col: str, title: str, y_label: str, output_path: str, window_size: int = 50):
    """
    Vẽ biểu đồ tỷ lệ khám phá trung bình với vùng đổ bóng thể hiện độ lệch chuẩn.
    """
    plt.figure(figsize=(12, 6))

    grouped = df.groupby(x_col)[y_col]
    mean_val = grouped.mean()
    std_val = grouped.std()

    mean_val_smooth = mean_val.rolling(window=window_size, min_periods=1).mean()
    std_val_smooth = std_val.rolling(window=window_size, min_periods=1).mean()

    plt.plot(mean_val_smooth.index, mean_val_smooth, label=f'Trung bình (làm mượt {window_size})', color='green')
    plt.fill_between(mean_val_smooth.index, mean_val_smooth - std_val_smooth, mean_val_smooth + std_val_smooth, color='green', alpha=0.2)

    plt.title(title)
    plt.xlabel(x_col.replace('_', ' ').title())
    plt.ylabel(y_label)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def plot_all_experiment_results(experiments_data: Dict[str, pd.DataFrame], global_output_dir: str):
    """
    Vẽ các biểu đồ tổng hợp cho tất cả các thử nghiệm.
    """
    print("  [Plotting] Generating aggregated plots...")
    
    for exp_name, df_agg in experiments_data.items():
        exp_output_dir = os.path.join(global_output_dir, exp_name)
        os.makedirs(exp_output_dir, exist_ok=True)

        # Plot 1: Success Rate
        plot_mean_with_std(
            df=df_agg,
            x_col='episode',
            y_col='success',
            title=f'Tỷ lệ thành công trung bình - Thử nghiệm: {exp_name}',
            y_label='Tỷ lệ thành công',
            output_path=os.path.join(exp_output_dir, 'aggregated_success_rate.png')
        )

        # Plot 2: Average Steps for Successful Episodes
        # Filter for successful episodes before plotting steps
        df_successful = df_agg[df_agg['success'] == True]
        if not df_successful.empty:
            plot_mean_with_std(
                df=df_successful,
                x_col='episode',
                y_col='steps',
                title=f'Số bước trung bình cho Episode thành công - Thử nghiệm: {exp_name}',
                y_label='Số bước',
                output_path=os.path.join(exp_output_dir, 'aggregated_avg_steps_successful.png')
            )
        else:
            print(f"    [Plotting] Không có episode thành công nào cho thử nghiệm '{exp_name}' để vẽ biểu đồ số bước.")

        # Plot 3: Exploration Rate
        plot_exploration_rate(
            df=df_agg,
            x_col='episode',
            y_col='final_exploration_rate',
            title=f'Tỷ lệ khám phá trung bình - Thử nghiệm: {exp_name}',
            y_label='Tỷ lệ khám phá',
            output_path=os.path.join(exp_output_dir, 'aggregated_exploration_rate.png')
        )
    
    print("  [Plotting] Aggregated plots generated.")
