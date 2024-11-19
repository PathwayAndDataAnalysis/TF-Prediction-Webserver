from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import os
from app.utils.run_analysis import get_pvalues
from app.utils.benjamini_hotchberg import bh_frd_correction
from app.utils.run_umap_pipeline import run_umap_pipeline
from app.utils.get_umap import get_umap_coordinates
import plotly.express as px
import random

main = Blueprint("main", __name__)

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/uploads")
ALLOWED_EXTENSIONS = {"txt", "csv", "tsv"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/plot")
def view_plot():
    return render_template("plot.html")


@main.route("/upload", methods=["GET", "POST"])
def upload_data():
    if request.method == "POST":

        # Check if the UPLOADS_DIR exists, if not create that folder
        if not os.path.exists(UPLOADS_DIR):
            os.makedirs(UPLOADS_DIR)

        if (
                "gene_expression_data" not in request.files
                or "prior_data" not in request.files
        ):
            return "No file part"

        gene_expression_file = request.files["gene_expression_data"]
        prior_data_file = request.files["prior_data"]

        if gene_expression_file.filename == "" or prior_data_file.filename == "":
            return "No selected file"

        if (
                gene_expression_file
                and allowed_file(gene_expression_file.filename)
                and prior_data_file
                and allowed_file(prior_data_file.filename)
        ):
            # gene_expression_filename = os.path.join(UPLOADS_DIR, gene_expression_file.filename)
            # prior_data_filename = os.path.join(UPLOADS_DIR, prior_data_file.filename)
            #
            # gene_expression_file.save(gene_expression_filename)
            # prior_data_file.save(prior_data_filename)

            # Now Run the analysis
            iters = 100_000
            try:
                # p_values = get_pvalues(prior_data_filename.split("/")[-1], gene_expression_filename.split("/")[-1],
                #                        iters)
                # p_file_path = os.path.join(UPLOADS_DIR, "p_values.tsv")
                # p_values.to_csv(p_file_path, sep="\t")
                #
                # # Now run the Benjamini-Hochberg FDR correction
                # reject = bh_frd_correction(p_file_path, alpha=0.05)

                # Pass p_values and reject to the plot.html template
                # return render_template('plot.html', p_values=p_values, reject=reject)
                return render_template("plot.html")

            except Exception as e:
                return trigger_custom_error(str(e))

        return trigger_custom_error("Invalid file type")
    else:
        return request.method + " method not allowed"


@main.route("/update_plot", methods=["POST"])
def update_plot():
    # Read UMAP data from file
    umap_data_file = os.path.join(UPLOADS_DIR, "umap_results.csv")
    umap_data = get_umap_coordinates(umap_data_file)

    data = {
        "x": umap_data["UMAP1"].tolist(),
        "y": umap_data["UMAP2"].tolist(),
    }

    # Define Plotly data and layout
    graph_data = {
        "data": [{
            "x": data["x"],
            "y": data["y"],
            "mode": "markers",
            "type": "scatter",
            "marker": {
                "color": umap_data["Cluster"].tolist(),
                "size": 4,
                # "showscale": True,
                "colorscale": "Viridis",
            },
            "text": umap_data["Cluster"].tolist(),
            "hoverinfo": "text",
        }],
        "layout": {
            "title": "UMAP Plot",
            "xaxis": {"title": "UMAP1"},
            "yaxis": {"title": "UMAP2"},
        },
    }

    return jsonify(graph_data)


@main.route("/umap", methods=["GET", "POST"])
def run_umap():
    return render_template("plot.html")
    # if request.method == "POST":
    #     print(request.files)
    #     if "data_matrix" not in request.files or "meta_data" not in request.files:
    #         return "No file part"
    #
    #     data_matrix_file = request.files["data_matrix"]
    #     meta_data_file = request.files["meta_data"]
    #
    #     if data_matrix_file.filename == "" or meta_data_file.filename == "":
    #         return "No selected file"
    #
    #     if (data_matrix_file
    #             and allowed_file(data_matrix_file.filename)
    #             and meta_data_file
    #             and allowed_file(meta_data_file.filename)
    #     ):
    #         data_matrix_filename = os.path.join(UPLOADS_DIR, data_matrix_file.filename)
    #         meta_data_filename = os.path.join(UPLOADS_DIR, meta_data_file.filename)
    #
    #         data_matrix_file.save(data_matrix_filename)
    #         meta_data_file.save(meta_data_filename)
    #
    #         # Now run the UMAP Pipeline
    #         print("request.form ", request.form)
    #         organism = request.form['organism']
    #
    #         filter_cells = request.form['filter_cells']
    #         filter_cells_value = request.form['filter_cells_value']
    #         filter_genes = request.form['filter_genes']
    #         filter_genes_value = request.form['filter_genes_value']
    #         qc_filter = request.form['qc_filter']
    #         qc_filter_value = request.form['qc_filter_value']
    #         data_normalize = request.form['data_normalize']
    #         data_normalize_value = request.form['data_normalize_value']
    #         log_transform = request.form['log_transform']
    #
    #         pca_components = int(request.form['pca_components'])
    #
    #         n_neighbors = int(request.form['n_neighbors'])
    #         min_dist = float(request.form['min_dist'])
    #         metric = request.form['metric']
    #
    #         # Now run the UMAP Pipeline
    #         run_umap_pipeline(data_matrix_filename=data_matrix_filename.split("/")[-1],
    #                           meta_data_filename=meta_data_filename.split("/")[-1],
    #                           organism=organism,
    #                           filter_cells=filter_cells,
    #                           filter_cells_value=int(filter_cells_value),
    #                           filter_genes=filter_genes,
    #                           filter_genes_value=int(filter_genes_value),
    #                           qc_filter=qc_filter,
    #                           qc_filter_value=float(qc_filter_value),
    #                           data_normalize=data_normalize,
    #                           data_normalize_value=int(data_normalize_value),
    #                           log_transform=log_transform,
    #                           pca_components=pca_components,
    #                           n_neighbors=n_neighbors,
    #                           min_dist=min_dist,
    #                           metric=metric
    #                           )
    #
    #         return render_template("plot.html")


# Error handler for 404 Not Found
@main.app_errorhandler(404)
def not_found_error(error):
    return (
        render_template("error.html",
                        error_code=404,
                        error_message="Page Not Found"),
        404,
    )


# Error handler for 500 Internal Server Error
@main.app_errorhandler(500)
def internal_error(error):
    return (
        render_template(
            "error.html",
            error_code=500,
            error_message="Internal Server Error"
        ),
        500,
    )


# Custom error message example
@main.route("/trigger_error")
def trigger_custom_error(error_message="Error", error_code="Error Code"):
    return render_template(
        "error.html",
        error_code=error_code,
        error_message=error_message
    )
