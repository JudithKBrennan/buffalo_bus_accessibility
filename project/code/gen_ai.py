import pandas as pd
import argparse
import numpy as np
from accessibility.utils import getDirectory, getAllRoutes, getExperimentOD

def ai_1(results: pd.DataFrame, origins: pd.DataFrame, destinations: pd.DataFrame):
    number_of_origins = origins['name'].max()
    number_of_destinations = destinations['name'].max()

    all_od_pairs = [(i,j) for i in origins['name'] for j in destinations['name']]

    # Create a DataFrame to store accessibility information
    unique_df = results.drop_duplicates(subset=['origin_id', 'destination_id'])
    accessibility_score = np.zeros(shape=number_of_origins)
    # Check accessibility for each start point
    for (o,d) in all_od_pairs:
        count_rows = len(unique_df[(unique_df['origin_id'] == o) & (unique_df['destination_id'] == d)])
        accessibility_score[o-1] += count_rows

    accessibility_score = accessibility_score/number_of_destinations
    return accessibility_score

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Experiment Details")
    parser.add_argument('experiment_id', type=str, help='Experiment ID')
    args = parser.parse_args()

    directory = getDirectory(args.experiment_id)
    origins, destinations = getExperimentOD(directory)
    results = getAllRoutes(directory)

    score1 = ai_1(results, origins, destinations)
    np.savetxt(directory+f"\\AI\\ai_1.txt", score1)


