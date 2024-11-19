// app/static/js/index.js

$(document).ready(function () {
    updatePlot(); // Load initial plot with default selections
});

function updatePlot() {
    $.ajax({
        url: '/update_plot',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({}),
        success: function (response) {
            const graphData = JSON.parse(JSON.stringify(response));

            Plotly.newPlot('scatterPlot', graphData.data, graphData.layout);

            // Update plot when window is resized
            $(window).resize(function () {
                Plotly.relayout('scatterPlot', {
                    width: window.innerWidth * 0.82,
                    height: window.innerHeight * 0.92
                });
            });
        },
        error: function (error) {
            console.error("Error updating plot:", error);
        }
    });
}


// // Initial load function
// $(document).ready(function () {
//     updatePlot(); // Load initial plot with default selections
// });
//
// function updatePlot() {
//     $.ajax({
//         url: '/update_plot',
//         type: 'POST',
//         contentType: 'application/json',
//         data: JSON.stringify({}),
//         success: function (response) {
//             const graphData = JSON.parse(JSON.stringify(response));
//
//             Plotly.newPlot('scatterPlot', graphData.data, graphData.layout);
//
//             // Update plot when window is resized
//             $(window).resize(function () {
//                 Plotly.relayout('scatterPlot', {
//                     width: window.innerWidth * 0.82,
//                     height: window.innerHeight * 0.92
//                 });
//             });
//         },
//         error: function (error) {
//             console.error("Error updating plot:", error);
//         }
//     });
// }