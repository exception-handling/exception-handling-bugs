import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def create_fixes_antipatterns_percentage_plot():
    """Create percentage plot for fix_grp vs anti-patterns from pre-calculated percentages"""
    # Read the dataset with pre-calculated percentages
    df = pd.read_csv('/home/r4ph/desenv/exception-handling-bugs/dataset/bugs/dataset_fixes_ap_perc.csv')
    
    print(f"Dataset shape: {df.shape}")
    print("Columns:", df.columns.tolist())
    print("\nFirst few rows:")
    print(df.head())
    
    # Set fix_grp as index
    df_matrix = df.set_index('fix_grp')
    
    # Remove empty rows (rows where fix_grp is NaN or empty)
    df_matrix = df_matrix.dropna(how='all')
    df_matrix = df_matrix[df_matrix.index.notna()]
    df_matrix = df_matrix[df_matrix.index != '']
    
    # Convert percentage strings to float, handling empty cells
    for col in df_matrix.columns:
        df_matrix[col] = pd.to_numeric(df_matrix[col], errors='coerce')
    
    # Fill NaN values with 0
    df_matrix = df_matrix.fillna(0)
    
    print(f"\nProcessed matrix shape: {df_matrix.shape}")
    print("Fix Groups:", list(df_matrix.index))
    print("Anti-patterns:", list(df_matrix.columns))
    
    # Create the plot
    plt.figure(figsize=(14, 10))
    
    # Keep original matrix to have anti-patterns on y-axis and fixes on x-axis
    matrix_plot = df_matrix
    
    # Order columns (fixes) by the number of different anti-patterns they relate to
    # Count non-zero values per column (fix)
    fix_diversity = (matrix_plot > 0).sum(axis=0)
    # Sort fixes by diversity (descending order)
    ordered_fixes = fix_diversity.sort_values(ascending=False).index
    matrix_ordered = matrix_plot[ordered_fixes]
    
    # Order rows (anti-patterns) by total percentage values
    antipattern_totals = matrix_plot.sum(axis=1)
    ordered_antipatterns = antipattern_totals.sort_values(ascending=False).index
    matrix_final = matrix_ordered.loc[ordered_antipatterns]
    
    # Create heatmap
    sns.heatmap(matrix_final, 
                annot=True, 
                cmap='Blues', 
                fmt='.1f',
                cbar=False,
                linewidths=0.5)
    
    plt.title('Fix Groups vs Anti-Patterns Percentage Matrix', fontsize=16)
    plt.xlabel('Fix Groups (ordered by diversity)', fontsize=12)
    plt.ylabel('Anti-Patterns (ordered by frequency)', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    # Save the plot
    plt.savefig('fixes_antipatterns_percentage_heatmap.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print ordering information
    print("\nFix Groups ordering (by number of different anti-patterns):")
    for i, fix in enumerate(ordered_fixes):
        non_zero_count = (matrix_plot[fix] > 0).sum()
        print(f"  {i+1}. {fix}: {non_zero_count} different anti-patterns")
    
    print(f"\nAnti-pattern ordering (by total percentage values):")
    for i, antipattern in enumerate(ordered_antipatterns):
        total_pct = antipattern_totals[antipattern]
        print(f"  {i+1}. {antipattern}: {total_pct:.1f}% total")
    
    # Display some statistics
    print(f"\nMatrix Statistics:")
    print(f"Total non-zero combinations: {(matrix_final > 0).sum().sum()}")
    print(f"Average percentage (non-zero): {matrix_final[matrix_final > 0].mean().mean():.2f}%")
    
    # Show top combinations
    print(f"\nTop combinations:")
    matrix_flat = matrix_final.unstack().sort_values(ascending=False)
    top_combinations = matrix_flat[matrix_flat > 0].head(10)
    
    for (antipattern, fix), percentage in top_combinations.items():
        print(f"  {fix} + {antipattern}: {percentage:.1f}%")
    
    return matrix_final

if __name__ == "__main__":
    print("Creating Fix Groups vs Anti-Patterns Percentage Plot...")
    matrix = create_fixes_antipatterns_percentage_plot()