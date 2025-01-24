import os

import pandas as pd


def read_umap_coordinates_file(upload_dir):
    umap_data_path = os.path.join(upload_dir, "umap_coordinates.csv")
    print(f"Reading UMAP coordinates file: {umap_data_path}")
    umap_df = pd.read_csv(umap_data_path, index_col=0)
    return umap_df


def read_pvalues_file(upload_dir):
    # p_value_path = os.path.join(upload_dir, "p_values_9k.tsv")
    p_value_path = os.path.join(upload_dir, "p_values.tsv")  # Hardcoded pvalues file
    print(f"Reading p-value file: {p_value_path}")
    p_value = pd.read_csv(p_value_path, sep="\t", index_col=0)
    return p_value


def read_bh_reject(upload_dir):
    # bh_reject_path = os.path.join(upload_dir, "reject_9k.tsv")
    bh_reject_path = os.path.join(upload_dir, "reject.tsv")
    print(f"Reading Benjamini-Hochberg reject file: {bh_reject_path}")
    bh_reject = pd.read_csv(bh_reject_path, sep="\t", index_col=0, low_memory=False)
    return bh_reject
