import os
import pandas as pd
import numpy as np
from scipy.stats import zscore
import requests
from scipy.special import erf
from joblib import Parallel, delayed

# This is using all n's and k's

# Path to the "uploads" folder (use absolute path for robustness)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")


def distribution_worker(max_target: int, ranks: np.array):
    arr = np.zeros(max_target)
    cs = np.random.choice(ranks, max_target, replace=False).cumsum()
    for i in range(0, max_target):
        amr = cs[i] / (i + 1)
        arr[i] = np.min([amr, 1 - amr])
    return arr


def get_sd(max_target: int, total_genes: int, iters: int):
    sd_file = f"SD_anal_{max_target}_{total_genes}_{iters}.npz"
    sd_file = os.path.join(UPLOAD_DIR, sd_file)

    if os.path.isfile(sd_file):
        print("Distribution file exists. Now we have to read it.")
        return np.load(sd_file)["distribution"]

    print("Distribution file does not exist. Now we have to generate it.")

    # n = 10_000  # Sampling size for random distribution
    n = total_genes  # Sampling size for random distribution
    ranks = np.linspace(start=1, stop=total_genes, num=n)
    ranks = (ranks - 0.5) / total_genes

    dist = Parallel(n_jobs=-1, verbose=5, backend="multiprocessing")(
        delayed(distribution_worker)(max_target, ranks) for _ in range(iters)
    )
    dist = np.array(dist).T
    np.savez_compressed(file=sd_file, distribution=dist)
    return dist


def sample_worker(
        sample: pd.DataFrame,
        prior_network: pd.DataFrame,
        distribution: np.array,
        iters: int,
):
    sample.dropna(inplace=True)
    sample["rank"] = sample.rank(ascending=False)
    sample["rank"] = (sample["rank"] - 0.5) / len(sample)
    sample["rev_rank"] = 1 - sample["rank"]

    # Get target genes rank
    for tf_id, tf_row in prior_network.iterrows():
        targets = tf_row["target"]
        actions = tf_row["action"]

        # Valid target counts and total targets should be greater than 3
        valid_targets = len([t for t in targets if t in sample.index])
        if len(targets) < 3 or valid_targets < 3:
            prior_network.loc[tf_id, "rs"] = np.nan
            prior_network.loc[tf_id, "valid_target"] = np.nan
            continue

        acti_rs = 0
        inhi_rs = 0

        for i, action in enumerate(actions):
            if targets[i] in sample.index:
                if action == 1:
                    acti_rs += np.average(sample.loc[targets[i], "rank"])
                    inhi_rs += np.average(sample.loc[targets[i], "rev_rank"])
                else:
                    inhi_rs += np.average(sample.loc[targets[i], "rank"])
                    acti_rs += np.average(sample.loc[targets[i], "rev_rank"])

        rs = np.min([acti_rs, inhi_rs])
        rs = rs / len(targets)  # Average rank-sum

        prior_network.loc[tf_id, "rs"] = rs if acti_rs < inhi_rs else -1 * rs

    # Counting how many times the rs is less than the random distribution
    for idx1, row1 in prior_network.iterrows():
        n_dist = distribution[row1["updown"] - 1]
        count = (
                np.sum(np.abs(n_dist) <= np.abs(row1["rs"])) + 1
        )  # Add 1 to avoid zero division

        if row1["rs"] < 0:
            count = -1 * count

        prior_network.loc[idx1, "count"] = count
        prior_network.loc[idx1, "p-value"] = count / iters

    return prior_network["p-value"].values


def run_analysis(
        tfs,
        gene_exp: pd.DataFrame,
        prior_network: pd.DataFrame,
        distribution: np.array,
        iters: int,
) -> pd.DataFrame:
    gene_exp = gene_exp.T
    parallel = Parallel(n_jobs=-1, verbose=5, backend="multiprocessing")
    output = parallel(
        delayed(sample_worker)(pd.DataFrame(row), prior_network, distribution, iters)
        for idx, row in gene_exp.iterrows()
    )
    output = pd.DataFrame(output, columns=tfs, index=gene_exp.index)
    return output


def main(prior_network: pd.DataFrame, gene_exp: pd.DataFrame, iters: int):
    gene_exp = gene_exp.apply(zscore, axis=1, nan_policy="omit")

    # Grouping prior_network network
    prior_network = prior_network.groupby("tf").agg({"action": list, "target": list})
    prior_network["updown"] = prior_network["target"].apply(lambda x: len(x))

    # max_target = np.max(prior_network["updown"])
    distribution = get_sd(
        max_target=np.max(prior_network["updown"]),
        total_genes=len(gene_exp),
        iters=iters,
    )

    return run_analysis(
        tfs=prior_network.index,
        gene_exp=gene_exp,
        prior_network=prior_network,
        distribution=distribution,
        iters=iters,
    )


def read_mouse_to_human_mapping_file():
    mth_file = "mouse_to_human.tsv"
    mth_file_path = os.path.join(UPLOAD_DIR, mth_file)

    if os.path.isfile(mth_file_path):
        print("Mouse to human mapping file exists. Let's read")
        return pd.read_csv(mth_file_path, sep="\t")

    print("Mouse to human mapping file does not exist. Let's download it.\n")
    file_url = "https://www.cs.umb.edu/~kisan/data/mouse_to_human.tsv"

    try:
        response = requests.get(file_url)
        with open(mth_file_path, "wb") as f:
            f.write(response.content)
        print("Mouse to human mapping file downloaded successfully.")

    except requests.exceptions.RequestException as e:
        print(f"Failed to download the mouse to human map file: {e}")
        raise Exception(f"Failed to download the mouse to human map file: {e}")

    return pd.read_csv(mth_file_path, sep="\t")


def read_data(p_file: str, g_file: str, upload_dir):
    p_file_path = os.path.join(upload_dir, p_file)

    prior_network = pd.read_csv(
        p_file_path,
        sep="\t",
        header=None,
        usecols=[0, 1, 2],
        names=["tf", "action", "target"],
        converters={
            "action": lambda x: (
                1
                if x == "upregulates-expression"
                else -1 if x == "downregulates-expression" else None
            )
        },
    ).dropna()
    prior_network = prior_network.reset_index(drop=True)

    g_file_path = os.path.join(upload_dir, g_file)
    gene_exp = pd.read_csv(g_file_path, sep="\t", index_col=0)

    # Mouse to human Mapping process
    mouse_to_human = read_mouse_to_human_mapping_file()

    # Replace index with human gene IDs, filter, clean, and explode
    gene_exp = gene_exp.rename(
        index=dict(zip(mouse_to_human["Mouse"], mouse_to_human["Human"]))
    )
    gene_exp = gene_exp[gene_exp.index.str.match(r"^\[.*\]$")]
    gene_exp.index = gene_exp.index.str.strip("[]")
    gene_exp = (
        gene_exp.assign(index=gene_exp.index.str.split(","))
        .explode("index")
        .reset_index(drop=True)
    )
    gene_exp = gene_exp.set_index("index")

    gene_exp = gene_exp.replace(0.0, np.nan).dropna(
        thresh=int(len(gene_exp.columns) * 0.05)
    )

    return prior_network, gene_exp


def get_pvalues(prior_file: str, gene_file: str, iters: int, upload_dir) -> pd.DataFrame:
    try:
        prior_net, gene_e = read_data(prior_file, gene_file, upload_dir)
        p_values = main(prior_net, gene_e, iters)
        p_values.dropna(axis=1, how="all", inplace=True)
        return p_values

    except Exception as e:
        raise Exception(f"Failed to run the analysis: {e}")
