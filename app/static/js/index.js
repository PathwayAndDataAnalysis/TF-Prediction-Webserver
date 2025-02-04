$(document).ready(function () {
    const haveAnnDataCheckbox = document.getElementById('have_anndata_checkbox');
    const geneExpMetaDataView = document.getElementById('view_gene_exp_metadata');
    const annDataUploadView = document.getElementById('view_anndata_upload');

    haveAnnDataCheckbox.addEventListener('change', function () {
        console.log("haveAnnDataCheckbox.checked: ", haveAnnDataCheckbox.checked);
        if (haveAnnDataCheckbox.checked) {
            geneExpMetaDataView.style.display = 'none';
            annDataUploadView.style.display = 'block';
        } else {
            geneExpMetaDataView.style.display = 'block';
            annDataUploadView.style.display = 'none';
        }
    });
});