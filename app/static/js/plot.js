let originalData = null;

$(document).ready(function () {
    // Initialize DOM elements
    const tfNameDropdown = document.getElementById("tf_name");
    const hideActive = document.getElementById('hide_active');
    const hideInactive = document.getElementById('hide_inactive');
    const hideInsignificant = document.getElementById('hide_insignificant');
    const sortTfs = document.getElementById('sort_tfs');

    // Fetch the initial data from server
    getPlotData();

    hideActive.addEventListener('click', function () {
        modifyPlot(hideActive.checked, hideInactive.checked, hideInsignificant.checked)
    });
    hideInactive.addEventListener('click', function () {
        modifyPlot(hideActive.checked, hideInactive.checked, hideInsignificant.checked)
    });
    hideInsignificant.addEventListener('click', function () {
        modifyPlot(hideActive.checked, hideInactive.checked, hideInsignificant.checked)
    });
    sortTfs.addEventListener("change", sortTranscriptionFactors)

    // Update plot when window is resized
    window.addEventListener('resize', function () {
        Plotly.relayout('scatterPlot', {
            width: window.innerWidth * 0.93,
            height: window.innerHeight * 0.91
        });
    });
});


/**
 * Fetches plot data from the server and initializes the plot.
 */
function getPlotData() {
    fetch('/get_plot_data', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({session_id: document.getElementById('session_id').value})
    })
        .then(response => response.json())
        .then(data => {
            console.log("Data:", data);
            originalData = data; // Store the original data
            Plotly.newPlot('scatterPlot', data.data, data.layout);

            // Populate TF List and metadata dropdowns
            populateDropdown('tf_name', Object.keys(data.tfs));
            populateDropdown('meta_data_cluster', data.meta_data_cluster);
        })
        .catch(error => console.error("Error fetching plot data:", error));
}


/**
 * Updates the plot based on selected options.
 */
function updatePlotNew() {
    const tfName = document.getElementById('tf_name').value;
    const plotInfo = document.getElementById('plot_info');
    fetch('/update_plot', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_id: document.getElementById('session_id').value,
            plot_type: document.getElementById('plot_type').value,
            tf_name: tfName,
            meta_data_cluster: document.getElementById('meta_data_cluster').value,
        })
    })
        .then(response => response.json())
        .then(data => {
            console.log("Data:", data);
            originalData = data; // Update the original data
            Plotly.react('scatterPlot', data.data, data.layout);

            if (tfName === 'Select an option' || tfName === '') {
                plotInfo.classList.add('hidden');
            } else {
                plotInfo.classList.remove('hidden');
            }
        })
        .catch(error => console.error("Error updating plot:", error));

}


/**
 * Modifies the plot based on the selected options.
 * @param hideActive
 * @param hideInactive
 * @param hideInsignificant
 */
function modifyPlot(hideActive, hideInactive, hideInsignificant) {
    if (!originalData) return;

    let filteredData = originalData.data;

    if (hideActive)
        filteredData = filteredData.filter(trace => {
            return trace.marker.color !== 'red';
        });

    if (hideInactive)
        filteredData = filteredData.filter(trace => {
            return trace.marker.color !== 'blue';
        });

    if (hideInsignificant)
        filteredData = filteredData.filter(trace => {
            return trace.marker.color !== 'gray';
        });

    Plotly.react('scatterPlot', filteredData, originalData.layout);
}


/**
 * Sorts transcription factors based on selected criteria.
 */
function sortTranscriptionFactors() {
    if (!originalData) return;

    const sortTfs = document.getElementById("sort_tfs").value;
    let sortedTfs = Object.entries(originalData.tfs);

    if (sortTfs === "sort_significance") {
        sortedTfs.sort(([, a], [, b]) => b - a);
    }

    populateDropdown('tf_name', sortedTfs.map(([key]) => key));
}


/**
 * Populates a dropdown with options.
 * @param {string} dropdownId - The ID of the dropdown.
 * @param {Array} options - The options to populate.
 */
function populateDropdown(dropdownId, options) {
    const dropdown = document.getElementById(dropdownId);
    dropdown.innerHTML = '';

    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Select an option';
    dropdown.appendChild(defaultOption);

    options.forEach(optionValue => {
        const option = document.createElement('option');
        option.value = optionValue;
        option.textContent = optionValue;
        dropdown.appendChild(option);
    });
}