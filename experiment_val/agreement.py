from sklearn.metrics import cohen_kappa_score
import numpy as np
import krippendorff
import pandas as pd

def calculate_krippendorff_alpha(ratings):
    """
    Calculate Krippendorff's alpha for inter-rater agreement.
    
    :param ratings: A 2D list or array where each row represents an item and each column represents a participant's ratings.
    :return: Krippendorff's alpha score.
    """
    # Ensure the input is a numpy array of integers
    ratings = np.array(ratings).astype(int)
    alpha = krippendorff.alpha(reliability_data=ratings, level_of_measurement='nominal')
    return alpha

def calculate_kappa_score(ratings):
    """
    Calculate the average kappa score for three raters.
    
    :param ratings: A 2D list or array where each column represents a participant's ratings.
                    For example, ratings[:,0] is the ratings from the first participant.
    :return: The average kappa score.
    """
    ratings = np.array(ratings).astype(int)
    
    kappa_12 = cohen_kappa_score(ratings[:,0], ratings[:,1])
    kappa_13 = cohen_kappa_score(ratings[:,0], ratings[:,2])
    kappa_23 = cohen_kappa_score(ratings[:,1], ratings[:,2])
    
    # Calculate the average kappa score
    average_kappa = (kappa_12 + kappa_13 + kappa_23) / 3
    
    return average_kappa

if __name__ == "__main__":
    df = pd.read_csv('experiment_val/dataset/agreement.csv', header=None)
    df = df.replace({'Y': '1', 'N': '0'})
    df = df.dropna()
    
    ratings_array = df.values
    
    # Calculate the inter-agreement scores
    average_kappa = calculate_kappa_score(ratings_array)
    print(f"Average Kappa Score: {average_kappa}")

    krippendorff_alpha = calculate_krippendorff_alpha(ratings_array.T)
    print(f"Krippendorff's Alpha: {krippendorff_alpha}")


    