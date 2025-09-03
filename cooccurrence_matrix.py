import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder

def create_cooccurrence_matrix_symptom_root_cause():
    """Create cooccurrence matrix for symptom_grp vs root_cause_grp"""
    # Read the dataset
    df = pd.read_csv('/home/r4ph/desenv/exception-handling-bugs/dataset/bugs/dataset_exception_bugs.csv')
    
    # Filter out rows where both columns are not null and not empty
    filtered_df = df[(df['symptom_grp'].notna()) & (df['root_cause_grp'].notna()) & 
                     (df['symptom_grp'] != '') & (df['root_cause_grp'] != '')]
    
    # Clean up trailing spaces in the data
    filtered_df = filtered_df.copy()
    filtered_df['symptom_grp'] = filtered_df['symptom_grp'].str.strip()
    filtered_df['root_cause_grp'] = filtered_df['root_cause_grp'].str.strip()
    
    print(f"\n" + "="*80)
    print("SYMPTOM GROUPS vs ROOT CAUSE GROUPS ANALYSIS")
    print("="*80)
    print(f"Total rows in dataset: {len(df)}")
    print(f"Rows with both symptom_grp and root_cause_grp: {len(filtered_df)}")
    
    # Create crosstab (co-occurrence matrix)
    cooccurrence = pd.crosstab(filtered_df['symptom_grp'], 
                               filtered_df['root_cause_grp'], 
                               margins=True)
    
    # Remove the 'All' row and column for cleaner visualization
    matrix = cooccurrence.iloc[:-1, :-1]
    
    print(f"\nCo-occurrence Matrix Shape: {matrix.shape}")
    print(f"Symptom Groups: {list(matrix.index)}")
    print(f"Root Cause Groups: {list(matrix.columns)}")
    
    # Print the matrix
    print("\nCo-occurrence Matrix:")
    print(matrix)
    
    # Calculate and display some statistics
    print(f"\nTotal co-occurrences: {matrix.sum().sum()}")
    print(f"Most frequent combinations:")
    
    # Find top combinations
    matrix_flat = matrix.unstack().sort_values(ascending=False)
    top_combinations = matrix_flat[matrix_flat > 0].head(10)
    
    for (symptom, root_cause), count in top_combinations.items():
        print(f"  {symptom} + {root_cause}: {count}")
    
    # Create a row-normalized version (percentages per symptom group)
    plt.figure(figsize=(14, 10))
    # Transpose matrix to have root causes on y-axis and symptoms on x-axis
    matrix_transposed = matrix.T
    # Normalize by row (each root cause group sums to 100%)
    matrix_pct = matrix_transposed.div(matrix_transposed.sum(axis=1), axis=0) * 100
    # Fill NaN values with 0 (for root causes with no occurrences)
    matrix_pct = matrix_pct.fillna(0)
    
    # Order columns (symptoms) by the number of different root causes they relate to
    # Count non-zero values per column (symptom)
    symptom_diversity = (matrix_pct > 0).sum(axis=0)
    # Sort symptoms by diversity (descending order)
    ordered_symptoms = symptom_diversity.sort_values(ascending=False).index
    matrix_pct_ordered = matrix_pct[ordered_symptoms]
    
    # Order rows (root causes) by total frequency
    root_cause_totals = matrix_transposed.sum(axis=1)
    ordered_root_causes = root_cause_totals.sort_values(ascending=False).index
    matrix_pct_final = matrix_pct_ordered.loc[ordered_root_causes]
    
    sns.heatmap(matrix_pct_final, 
                annot=True, 
                cmap='Blues', 
                fmt='.1f',
                # cbar_kws={'label': 'Percentage (%)'},
                cbar=False,
                linewidths=0.5)
    
    plt.title('Co-occurrence Matrix (Normalized): Root Cause Groups vs Symptom Groups', fontsize=16)
    plt.xlabel('Symptom Groups (ordered by diversity)', fontsize=12)
    plt.ylabel('Root Cause Groups (ordered by frequency)', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    # Save the normalized plot
    plt.savefig('cooccurrence_heatmap_symptom_root_cause_normalized.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print ordering information
    print(f"\nSymptom ordering (by number of different root causes):")
    for i, symptom in enumerate(ordered_symptoms):
        print(f"  {i+1}. {symptom}: {symptom_diversity[symptom]} different root causes")
    
    print(f"\nRoot cause ordering (by total frequency):")
    for i, root_cause in enumerate(ordered_root_causes):
        print(f"  {i+1}. {root_cause}: {root_cause_totals[root_cause]} total occurrences")
    
    # Save matrix to CSV
    matrix.to_csv('cooccurrence_matrix.csv')
    print(f"\nMatrix saved to 'cooccurrence_matrix.csv'")
    
    return matrix

def create_cooccurrence_matrix_root_cause_fix():
    """Create cooccurrence matrix for root_cause_grp vs fix_grp"""
    # Read the dataset
    df = pd.read_csv('/home/r4ph/desenv/exception-handling-bugs/dataset/bugs/dataset_exception_bugs.csv')
    
    # Filter out rows where both columns are not null and not empty
    filtered_df = df[(df['root_cause_grp'].notna()) & (df['fix_grp'].notna()) & 
                     (df['root_cause_grp'] != '') & (df['fix_grp'] != '')]
    
    # Clean up trailing spaces in the data
    filtered_df = filtered_df.copy()
    filtered_df['root_cause_grp'] = filtered_df['root_cause_grp'].str.strip()
    filtered_df['fix_grp'] = filtered_df['fix_grp'].str.strip()
    
    print(f"\n" + "="*80)
    print("ROOT CAUSE GROUPS vs FIX GROUPS ANALYSIS")
    print("="*80)
    print(f"Total rows in dataset: {len(df)}")
    print(f"Rows with both root_cause_grp and fix_grp: {len(filtered_df)}")
    
    # Create crosstab (co-occurrence matrix)
    cooccurrence = pd.crosstab(filtered_df['root_cause_grp'], 
                               filtered_df['fix_grp'], 
                               margins=True)
    
    # Remove the 'All' row and column for cleaner visualization
    matrix = cooccurrence.iloc[:-1, :-1]
    
    print(f"\nCo-occurrence Matrix Shape: {matrix.shape}")
    print(f"Root Cause Groups: {list(matrix.index)}")
    print(f"Fix Groups: {list(matrix.columns)}")
    
    # Print the matrix
    print("\nCo-occurrence Matrix (Root Cause vs Fix):")
    print(matrix)
    
    # Calculate and display some statistics
    print(f"\nTotal co-occurrences: {matrix.sum().sum()}")
    print(f"Most frequent combinations:")
    
    # Find top combinations
    matrix_flat = matrix.unstack().sort_values(ascending=False)
    top_combinations = matrix_flat[matrix_flat > 0].head(10)
    
    for (root_cause, fix), count in top_combinations.items():
        print(f"  {root_cause} → {fix}: {count}")
    
    # Create a row-normalized version (percentages per root cause group)
    plt.figure(figsize=(14, 10))
    # Normalize by row (each root cause group sums to 100%)
    matrix_pct = matrix.div(matrix.sum(axis=1), axis=0) * 100
    # Fill NaN values with 0 (for root causes with no occurrences)
    matrix_pct = matrix_pct.fillna(0)
    
    # Order columns (fixes) by the number of different root causes they relate to
    # Count non-zero values per column (fix)
    fix_diversity = (matrix_pct > 0).sum(axis=0)
    # Sort fixes by diversity (descending order)
    ordered_fixes = fix_diversity.sort_values(ascending=False).index
    matrix_pct_ordered = matrix_pct[ordered_fixes]
    
    # Order rows (root causes) by total frequency
    root_cause_totals = matrix.sum(axis=1)
    ordered_root_causes = root_cause_totals.sort_values(ascending=False).index
    matrix_pct_final = matrix_pct_ordered.loc[ordered_root_causes]
    
    sns.heatmap(matrix_pct_final, 
                annot=True, 
                cmap='Blues', 
                fmt='.1f',
                # cbar_kws={'label': 'Percentage (%)'},
                cbar=False,
                linewidths=0.5)
    
    plt.title('Co-occurrence Matrix (Normalized): Root Cause Groups vs Fix Groups', fontsize=16)
    plt.xlabel('Fix Groups (ordered by diversity)', fontsize=12)
    plt.ylabel('Root Cause Groups (ordered by frequency)', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    # Save the normalized plot
    plt.savefig('cooccurrence_heatmap_root_cause_fix_normalized.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print ordering information
    print(f"\nFix Groups ordering (by number of different root causes):")
    for i, fix in enumerate(ordered_fixes):
        print(f"  {i+1}. {fix}: {fix_diversity[fix]} different root causes")
    
    print(f"\nRoot cause ordering (by total frequency):")
    for i, root_cause in enumerate(ordered_root_causes):
        print(f"  {i+1}. {root_cause}: {root_cause_totals[root_cause]} total occurrences")
    
    # Save matrix to CSV
    matrix.to_csv('cooccurrence_matrix_root_cause_fix.csv')
    print(f"\nMatrix saved to 'cooccurrence_matrix_root_cause_fix.csv'")
    
    return matrix

if __name__ == "__main__":
    print("Creating Symptom Groups vs Root Cause Groups Matrix...")
    matrix1 = create_cooccurrence_matrix_symptom_root_cause()
    
    print("\n\nCreating Root Cause Groups vs Fix Groups Matrix...")
    matrix2 = create_cooccurrence_matrix_root_cause_fix()