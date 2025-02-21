import pandas as pd
import numpy as np

def create_random_sample(input_file, output_file, sample_size, random_seed=42):
    # Set the random seed for reproducibility
    np.random.seed(random_seed)
    
    # Load the dataset
    df = pd.read_csv(input_file)
    
    sample_df = df.sample(n=sample_size, random_state=random_seed)
    
    sample_df.to_csv(output_file, index=False)

if __name__ == "__main__":
    input_file = 'dataset/bugs/dataset_exception_bugs.csv'
    output_file = 'dataset/bugs/sample_exception_bugs.csv'
    sample_size = 312
    
    create_random_sample(input_file, output_file, sample_size)
