let originalData = null;

$(document).ready(function () {
    updatePlot();

    const hideActive = document.getElementById('hide_active');
    const hideInactive = document.getElementById('hide_inactive');
    const hideInsignificant = document.getElementById('hide_insignificant');

    const sortTfs = document.getElementById('sort_tfs');

    hideActive.addEventListener('click', function () {
        console.log('hide active clicked');
        updatePlotData();
    });

    hideInactive.addEventListener('click', function () {
        console.log('hide inactive clicked');
        updatePlotData();
    });

    hideInsignificant.addEventListener('click', function () {
        console.log('hide insignificant clicked');
        updatePlotData();
    });

    sortTfs.addEventListener("change", function () {
        console.log("Sort TFs changed");

        let sortedTfs = originalData.tfs;
        if (sortTfs.value === "sort_significance") {
            console.log("Sorting by Significance Cell Count");
            // sortedTfs = {TF1: 10, TF2: 20, TF3: 5}. I want to sort by values
            sortedTfs = Object.fromEntries(
                Object.entries(sortedTfs).sort(([, a], [, b]) => b - a)
            );
        }

        // update the dropdown document.getElementById('tf_name'); with the sorted values
        let tfNameDropdown = document.getElementById('tf_name');
        console.log("Sorted TFs:", sortedTfs);
        sortedTfs = Object.keys(sortedTfs);
        console.log("Sorted TFs Keys:", sortedTfs);
        sortedTfs.unshift('Select Transcription Factor');
        tfNameDropdown.innerHTML = '';
        for (let i = 0; i < sortedTfs.length; i++) {
            const option = document.createElement('option');
            option.value = sortedTfs[i];
            option.text = sortedTfs[i];

            if (sortedTfs[i] === originalData.selected_tf)
                option.selected = true;

            tfNameDropdown.appendChild(option);
        }
    })
});

function updatePlot() {
    const sessionId = document.getElementById('session_id').value;

    // Get data from plot_type dropdown
    const plotType = document.getElementById('plot_type').value;

    const tfNameDropdown = document.getElementById('tf_name');

    const selectMetaDataCluster = document.getElementById('select_meta_data_cluster');
    const metaDataClusterDropDown = document.getElementById('meta_data_cluster');
    const plotInfo = document.getElementById('plot_info');

    // Send data to server
    fetch('/update_plot', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(
            {
                plot_type: plotType,
                tf_name: document.getElementById('tf_name').value,
                meta_data_cluster: document.getElementById('meta_data_cluster').value,
                session_id: sessionId
            }
        )
    })
        .then(response => response.json())
        .then(data => {
            console.log("data: ", data);
            originalData = data; // Store the original data
            Plotly.newPlot('scatterPlot', data.data, data.layout);

            // Update plot when window is resized
            window.addEventListener('resize', function () {
                Plotly.relayout('scatterPlot', {
                    width: window.innerWidth * 0.82,
                    height: window.innerHeight * 0.92
                });
            });

            // Sort tfs based on the selected value
            let tfs = data.tfs;
            if (document.getElementById('sort_tfs').value === "sort_significance") {
                console.log("Sorting by Significance Cell Count");
                // sortedTfs = {TF1: 10, TF2: 20, TF3: 5}. I want to sort by values
                tfs = Object.fromEntries(
                    Object.entries(tfs).sort(([, a], [, b]) => b - a)
                );
            }

            // Get keys only of data.tfs
            tfs = Object.keys(tfs);

            // Add Select Transcription Factor option in first position of tfs
            tfs.unshift('Select Transcription Factor');

            let selected_tf = data.selected_tf;

            if (selected_tf === '') {
                selected_tf = 'Select Transcription Factor';
                plotInfo.style.display = 'none';
                selectMetaDataCluster.style.display = 'block';

                metaDataClusterDropDown.innerHTML = '';
                let metaDataCluster = data.meta_data_cluster;
                metaDataCluster.unshift('Select Meta Data Cluster');
                let selected_meta_data_cluster = data.selected_meta_data_cluster;
                for (let i = 0; i < metaDataCluster.length; i++) {
                    const option = document.createElement('option');
                    option.value = metaDataCluster[i];
                    option.text = metaDataCluster[i];

                    if (metaDataCluster[i] === selected_meta_data_cluster)
                        option.selected = true;

                    metaDataClusterDropDown.appendChild(option);
                }

            } else {
                plotInfo.style.display = 'block';
                selectMetaDataCluster.style.display = 'none';
            }

            tfNameDropdown.innerHTML = '';
            for (let i = 0; i < tfs.length; i++) {
                const option = document.createElement('option');
                option.value = tfs[i];
                option.text = tfs[i];

                if (tfs[i] === selected_tf)
                    option.selected = true;

                tfNameDropdown.appendChild(option);
            }

        })
        .catch(error => {
            console.error("Error updating plot:", error);
        });
}

function updatePlotData() {
    if (!originalData) return;

    const hideActive = document.getElementById('hide_active').checked;
    const hideInactive = document.getElementById('hide_inactive').checked;
    const hideInsignificant = document.getElementById('hide_insignificant').checked;

    const filteredData = originalData.data.map(trace => {

        console.log("Filtering data for trace:", trace);

        const filteredX = [];
        const filteredY = [];
        const filteredColor = [];

        for (let i = 0; i < trace.x.length; i++) {
            const color = trace.marker.color[i];

            if ((hideActive && color === 'red')
                || (hideInactive && color === 'blue')
                || (hideInsignificant && color === 'gray')
            ) {
                continue;
            }

            filteredX.push(trace.x[i]);
            filteredY.push(trace.y[i]);
            filteredColor.push(color);
        }

        return {
            ...trace,
            x: filteredX,
            y: filteredY,
            marker: {
                ...trace.marker,
                color: filteredColor
            }
        };
    });

    console.log("Plotting filtered data:", filteredData);
    // react relayouts the plot
    Plotly.react('scatterPlot', filteredData, originalData.data[0].layout);

    // // This is an alternative way to update the plot. But the toggling data is not working
    // Plotly.update('scatterPlot', {
    //     x: filteredData.map(trace => trace.x),
    //     y: filteredData.map(trace => trace.y),
    //     'marker.color': filteredData.map(trace => trace.marker.color)
    // });

}