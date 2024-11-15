from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import os
from app.utils.run_analysis import get_pvalues
from app.utils.benjamini_hotchberg import bh_frd_correction
import plotly.express as px
import random

main = Blueprint('main', __name__)

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/uploads")
ALLOWED_EXTENSIONS = {'txt', 'csv', 'tsv'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/plot')
def view_plot():
    return render_template('plot.html')


@main.route('/upload', methods=['GET', 'POST'])
def upload_data():
    if request.method == 'POST':

        # Check if the UPLOADS_DIR exists, if not create that folder
        if not os.path.exists(UPLOADS_DIR):
            os.makedirs(UPLOADS_DIR)

        if 'gene_expression_data' not in request.files or 'prior_data' not in request.files:
            return "No file part"

        gene_expression_file = request.files['gene_expression_data']
        prior_data_file = request.files['prior_data']

        if gene_expression_file.filename == '' or prior_data_file.filename == '':
            return "No selected file"

        if (gene_expression_file
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
                return render_template('plot.html')

            except Exception as e:
                return trigger_custom_error(str(e))

        return trigger_custom_error("Invalid file type")
    else:
        return request.method + " method not allowed"


@main.route('/update_plot', methods=['POST'])
def update_plot():
    # Generate 50 random points for x and y
    data = {
        "x": [random.uniform(0, 100) for _ in range(50)],
        "y": [random.uniform(0, 100) for _ in range(50)]
    }

    # Define Plotly data and layout
    graph_data = {
        "data": [
            {
                "x": data["x"],
                "y": data["y"],
                "mode": "markers",
                "type": "scatter"
            }
        ],
        "layout": {
            "title": "Random Scatter Plot of 50 Points",
            "xaxis": {"title": "X-Axis"},
            "yaxis": {"title": "Y-Axis"}
        }
    }

    return jsonify(graph_data)


# Error handler for 404 Not Found
@main.app_errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_code=404, error_message="Page Not Found"), 404


# Error handler for 500 Internal Server Error
@main.app_errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_code=500, error_message="Internal Server Error"), 500


# Custom error message example
@main.route('/trigger_error')
def trigger_custom_error(error_message="Error", error_code="Error Code"):
    return render_template('error.html', error_code=error_code, error_message=error_message)
