// app/static/js/index.js

$(document).ready(function () {
    updatePlot();
});

function updatePlot() {
    // Get data from plot_type dropdown
    const plotType = document.getElementById('plot_type').value;

    // Send data to server
    fetch('/update_plot', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(
            {
                plot_type: plotType,
                tf_name: document.getElementById('tf_name').value
            }
        )
    })
        .then(response => response.json())
        .then(data => {
            Plotly.newPlot('scatterPlot', data.data, data.layout);

            // Update plot when window is resized
            window.addEventListener('resize', function () {
                Plotly.relayout('scatterPlot', {
                    width: window.innerWidth * 0.82,
                    height: window.innerHeight * 0.92
                });
            });

            // Update tf_name elements dropdown
            tfs = data.tfs;
            selected_tf = data.selected_tf;
            const tfNameDropdown = document.getElementById('tf_name');
            tfNameDropdown.innerHTML = '';
            for (let i = 0; i < tfs.length; i++) {
                const option = document.createElement('option');
                option.value = tfs[i];
                option.text = tfs[i];
                if (tfs[i] === selected_tf) {
                    option.selected = true;
                }
                tfNameDropdown.appendChild(option);
            }

        })
        .catch(error => {
            console.error("Error updating plot:", error);
        });
}
