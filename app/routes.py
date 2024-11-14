from flask import Blueprint, render_template, request, redirect, url_for
import os
from app.utils.run_analysis import get_pvalues

main = Blueprint('main', __name__)

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/uploads")
ALLOWED_EXTENSIONS = {'txt', 'csv', 'tsv'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/other')
def other_page():
    return render_template('other_page.html')


@main.route('/upload', methods=['GET', 'POST'])
def upload_data():
    if request.method == 'POST':
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
            gene_expression_filename = os.path.join(UPLOADS_DIR, gene_expression_file.filename)
            prior_data_filename = os.path.join(UPLOADS_DIR, prior_data_file.filename)

            gene_expression_file.save(gene_expression_filename)
            prior_data_file.save(prior_data_filename)

            # Now Run the analysis
            iters = 100_000
            p_values = get_pvalues(prior_data_filename.split("/")[-1], gene_expression_filename.split("/")[-1], iters)

            # Save the results
            p_values.to_csv(os.path.join(UPLOADS_DIR, "results.tsv"))

            return "Analysis completed. Results saved in results.tsv"

        return "Invalid file type"
    else:
        return request.method + " method not allowed"
