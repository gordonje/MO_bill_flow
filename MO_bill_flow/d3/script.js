var makeChart = function (chamber, chart) {
// add a div to body and set the id to chamber
  div = d3.select("body")
          .append("div")
          .attr("id", chamber);
// these will be the same for both charts
  var width = 420,
      barHeight = 40;
// so will this
  var x = d3.scale.linear()
            .range([0, width]);
// add an svg to the div
  chart = div.append("svg")
             .attr("class", "chart")
             .attr("width", width);
// create a variable for the jsonFile
  jsonFile = chamber + '_numbers.json';
// load data and draw the chart
  d3.json(jsonFile, function(error, data) {
    x.domain([0, d3.max(data, function(d) { return d.all_bills; })]);

    chart.attr("height", barHeight * data.length);

    var bar = chart.selectAll("g")
        .data(data)
      .enter().append("g")
        .attr("transform", function(d, i) { return "translate(0," + i * barHeight + ")" });

    bar.append("rect")
        .attr("width", function(d) { return d.all_bills} )
        .attr("height", barHeight - 1);

  //   bar.append("text")
  //       .attr("x", function(d) { return x(d.all_bills) - 3; })
  //       .attr("y", barHeight / 2)
  //       .attr("dy", ".35em")
  //       .text(function(d) { return d.all_bills; });
  //   console.log(chart);

  });

  function type(d) {
    d.all_bills = +d.all_bills; 
    return d;
  }

};
// call the function twice, need the second variable in order to not override the chart
makeChart('house', 'chart1');
makeChart('senate', 'chart2');