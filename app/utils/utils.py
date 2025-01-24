ALLOWED_EXTENSIONS = {"txt", "csv", "tsv"}


def map_cluster_value(value):
    if value == 0.5:
        return "True"
    elif value == 1:
        return "False"
    elif value == 0:
        return "NaN"
    return value


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
