import uuid

import numpy as np
from flask import Blueprint, render_template, request, jsonify
import os
from app.utils.benjamini_hotchberg import bh_frd_correction
from app.utils.read_data import (
    read_umap_coordinates_file,
    read_pvalues_file,
    read_bh_reject,
)
from app.utils.run_umap_pipeline import run_umap_pipeline
# from app.utils.tf_analysis import get_pvalues
from app.utils.run_analysis import get_pvalues
from app.utils.utils import map_cluster_value, allowed_file

main = Blueprint("main", __name__)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/uploads")
SESSION_ID = str(uuid.uuid4())


@main.route("/get_session_id")
def get_session_id():
    return jsonify({"session_id": SESSION_ID})


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/plot")
def view_plot():
    return render_template("plot.html")


@main.route("/plot/<session_id>")
def view_plot_session_id(session_id):
    return render_template("plot.html", session_id=session_id)


@main.route("/run_analysis", methods=["GET", "POST"])
def run_tf_analysis():
    if request.method == "POST":
        # Check if the UPLOADS_DIR exists, if not create that folder
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        if ("gene_expression_data" not in request.files
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
            gene_expression_filename = os.path.join(
                UPLOAD_DIR, gene_expression_file.filename
            )
            prior_data_filename = os.path.join(UPLOAD_DIR, prior_data_file.filename)

            gene_expression_file.save(gene_expression_filename)
            prior_data_file.save(prior_data_filename)

            # Now Run the analysis
            iters = int(request.form["iters"])
            try:
                p_values = get_pvalues(
                    prior_data_filename.split("/")[-1],
                    gene_expression_filename.split("/")[-1],
                    iters,
                )
                p_file_path = os.path.join(UPLOAD_DIR, "p_values.tsv")
                p_values.to_csv(p_file_path, sep="\t")

                # Now run the Benjamini-Hochberg FDR correction
                reject = bh_frd_correction(p_file_path, alpha=0.05)
                reject_file_path = os.path.join(UPLOAD_DIR, "reject.tsv")
                reject.to_csv(reject_file_path, sep="\t")

                # Pass p_values and reject to the plot.html template
                # return render_template('plot.html', p_values=p_values, reject=reject)
                return render_template("plot.html")

            except Exception as e:
                return trigger_custom_error(str(e))

        return trigger_custom_error("Invalid file type")
    else:
        return request.method + " method not allowed"


@main.route("/umap", methods=["GET", "POST"])
def run_umap():
    # return render_template("plot.html")
    if request.method == "POST":
        print(request.files)
        if "data_matrix" not in request.files or "meta_data" not in request.files or "prior_data" not in request.files:
            return "No file part"

        data_matrix_file = request.files["data_matrix"]
        meta_data_file = request.files["meta_data"]
        prior_data_file = request.files["prior_data"]  # for TF analysis

        if data_matrix_file.filename == "" or meta_data_file.filename == "" or prior_data_file.filename == "":
            return "No selected file"

        if (data_matrix_file
                and allowed_file(data_matrix_file.filename)
                and meta_data_file
                and allowed_file(meta_data_file.filename)
                and prior_data_file
                and allowed_file(prior_data_file.filename)
        ):
            print("First Running UMAP Pipeline....")
            # Create an uuid folder to store the uploaded files
            uuid_folder_name = SESSION_ID
            print("uuid_folder_name: ", uuid_folder_name)
            upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/uploads/" + uuid_folder_name)
            os.makedirs(upload_dir)

            data_matrix_filename = os.path.join(upload_dir, data_matrix_file.filename)
            meta_data_filename = os.path.join(upload_dir, meta_data_file.filename)
            prior_data_filename = os.path.join(upload_dir, prior_data_file.filename)  # for TF analysis

            # data_matrix_filename = os.path.join(UPLOAD_DIR, data_matrix_file.filename)
            # meta_data_filename = os.path.join(UPLOAD_DIR, meta_data_file.filename)

            data_matrix_file.save(data_matrix_filename)
            meta_data_file.save(meta_data_filename)
            prior_data_file.save(prior_data_filename)  # for TF analysis

            # Now run the UMAP Pipeline
            print("request.form ", request.form)
            organism = request.form["organism"]

            filter_cells = request.form["filter_cells"]
            filter_cells_value = request.form["filter_cells_value"]
            filter_genes = request.form["filter_genes"]
            filter_genes_value = request.form["filter_genes_value"]
            qc_filter = request.form["qc_filter"]
            qc_filter_value = request.form["qc_filter_value"]
            data_normalize = request.form["data_normalize"]
            data_normalize_value = request.form["data_normalize_value"]
            log_transform = request.form["log_transform"]

            pca_components = int(request.form["pca_components"])

            n_neighbors = int(request.form["n_neighbors"])
            min_dist = float(request.form["min_dist"])
            metric = request.form["metric"]

            # Now run the UMAP Pipeline
            umap_df = run_umap_pipeline(
                data_matrix_filename=data_matrix_filename.split("/")[-1],
                meta_data_filename=meta_data_filename.split("/")[-1],
                organism=organism,
                filter_cells=filter_cells,
                filter_cells_value=int(filter_cells_value),
                filter_genes=filter_genes,
                filter_genes_value=int(filter_genes_value),
                qc_filter=qc_filter,
                qc_filter_value=float(qc_filter_value),
                data_normalize=data_normalize,
                data_normalize_value=int(data_normalize_value),
                log_transform=log_transform,
                pca_components=pca_components,
                n_neighbors=n_neighbors,
                min_dist=min_dist,
                metric=metric,
                uuid_folder_name=uuid_folder_name
            )
            umap_df.to_csv(os.path.join(upload_dir, "umap_coordinates.csv"))

            # Now run the TF analysis
            print("Running TF analysis....")
            iters = int(request.form["iters"])
            try:
                p_values = get_pvalues(
                    prior_data_filename.split("/")[-1],
                    data_matrix_filename.split("/")[-1],
                    iters,
                    upload_dir
                )
                p_file_path = os.path.join(upload_dir, "p_values.tsv")
                p_values.to_csv(p_file_path, sep="\t")

                # Now run the Benjamini-Hochberg FDR correction
                reject = bh_frd_correction(p_file_path, alpha=0.05)
                reject_file_path = os.path.join(upload_dir, "reject.tsv")
                reject.to_csv(reject_file_path, sep="\t")

            except Exception as e:
                return trigger_custom_error(str(e))

            print("Done with UMAP and TF analysis. Now rendering plot.html")
            return render_template("plot.html", session_id=uuid_folder_name)

        return trigger_custom_error("Invalid file type")


@main.route("/update_plot", methods=["POST"])
def update_plot():
    selected_plot_type = request.json["plot_type"]
    selected_tf_name = request.json["tf_name"]
    session_id = request.json["session_id"]

    print("selected_plot_type: ", selected_plot_type)
    print("selected_tf_name: ", selected_tf_name)
    print("session_id: ", session_id)

    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/uploads/" + session_id)

    umap_data = read_umap_coordinates_file(upload_dir)
    p_values = read_pvalues_file(upload_dir)

    if selected_tf_name == "Select Transcription Factor":
        selected_tf_name = ""

    true_false_count = {True: 0, False: 0, "NaN": 0}
    if selected_tf_name:
        bh_reject = read_bh_reject(upload_dir)

        # Count how many True, False and NaN values are there in the selected TF column and save it to dictionary
        true_false_count = bh_reject[selected_tf_name].value_counts().to_dict()
        true_false_count["NaN"] = int(bh_reject[selected_tf_name].isna().sum())

        umap_data[selected_tf_name] = bh_reject[selected_tf_name]

        color_map = {True: "green", False: "red", np.nan: "gray"}
        umap_data[selected_tf_name] = umap_data[selected_tf_name].map(color_map)

    data = (
        {
            "x": umap_data["X_umap1"].tolist(),
            "y": umap_data["X_umap2"].tolist(),
        }
        if selected_plot_type == "umap"
        else {
            "x": umap_data["X_pca1"].tolist(),
            "y": umap_data["X_pca2"].tolist(),
        }
    )

    # Dynamic Title
    tf_name_and_counts = f" - {selected_tf_name}  {true_false_count}" if selected_tf_name else ""
    title = (
        f"UMAP Plot {tf_name_and_counts}"
        if selected_plot_type == "umap"
        else f"Top 2 PCA Components Plot {tf_name_and_counts}"
    )

    # Define layout for the plot
    layout = {
        "title": title,
        "xaxis": {"title": "UMAP1" if selected_plot_type == "umap" else "PCA1"},
        "yaxis": {"title": "UMAP2" if selected_plot_type == "umap" else "PCA2"},
        "hovermode": "closest",
    }

    # Define color scale for the plot
    custom_color = (
        umap_data["Cluster"].tolist()
        if not selected_tf_name
        else umap_data[selected_tf_name].tolist()
    )

    custom_text = (
        umap_data["Cluster"].tolist()
        if not selected_tf_name
        else [
            map_cluster_value(value) for value in umap_data[selected_tf_name].tolist()
        ]
    )
    custom_hovertemplate = (
        "<b>Cluster:</b> %{text}<br><b>UMAP1:</b> %{x}<br><b>UMAP2:</b> %{y}"
        if selected_plot_type == "umap"
        else "<b>Cluster:</b> %{text}<br><b>PCA1:</b> %{x}<br><b>PCA2:</b> %{y}"
    )

    # Define Plotly data and layout
    graph_data = {
        "data": [
            {
                "x": data["x"],
                "y": data["y"],
                "mode": "markers",
                "type": "scatter",
                "marker": {
                    # "showscale": True,
                    "color": custom_color,
                    "size": 6,
                    "opacity": 0.5,
                    "colorscale": "Viridis",
                },
                "text": custom_text,
                "hovertemplate": custom_hovertemplate,
                "hoverinfo": "x+y+text",
            }
        ],
        "layout": layout,
        "tfs": p_values.columns.tolist(),
        "selected_tf": selected_tf_name,
    }

    return jsonify(graph_data)


@main.route("/result", methods=["GET", "POST"])
def result():
    if request.method == "POST":
        session_id = request.form["session_id"]
        print("session_id: ", session_id)

        return render_template("plot.html", session_id=session_id)

    else:
        return trigger_custom_error("Invalid request method")


# Error handler for 404 Not Found
@main.app_errorhandler(404)
def not_found_error(error):
    return (
        render_template("error.html", error_code=404, error_message="Page Not Found"),
        404,
    )


# Error handler for 500 Internal Server Error
@main.app_errorhandler(500)
def internal_error(error):
    return (
        render_template(
            "error.html", error_code=500, error_message="Internal Server Error"
        ),
        500,
    )


# Custom error message example
@main.route("/trigger_error")
def trigger_custom_error(error_message="Error", error_code="Error Code"):
    return render_template(
        "error.html", error_code=error_code, error_message=error_message
    )
