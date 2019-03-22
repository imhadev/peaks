var myvalues = [{{ ', '.join(values) }}];

var color = Chart.helpers.color;
var data = {
    labels: [],
    datasets: [{
        type: 'bar',
        label: 'highlights',
        backgroundColor: color(window.chartColors.red).alpha(0.5).rgbString(),
        borderColor: window.chartColors.red,
        borderWidth: 1,
        data: [

        ]
    }, {
        type: 'line',
        label: 'average',
        backgroundColor: color(window.chartColors.grey).alpha(0.5).rgbString(),
        borderColor: window.chartColors.blue,
        borderWidth: 2,
        fill: true,
        data: [

        ]
    }]
};


window.onload = function() {

    var ctx = document.getElementById('canvaschart').getContext('2d');
    window.myBar = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            legend: {
                position: 'top',
            }
        }
    });


    Particles.init({
        selector: '.background',
        color: '#fcfcfc',
        connectParticles: 'true',
        maxParticles: 120,

        responsive: [
            {
              breakpoint: 768,
              options: {
                maxParticles: 50,
                connectParticles: true
              }
            }, {
              breakpoint: 425,
              options: {
                maxParticles: 30,
                connectParticles: true
              }
            }, {
              breakpoint: 320,
              options: {
                maxParticles: 10,
                connectParticles: true
              }
            }
          ]
    });

    adddata();

};

function adddata(){
    var i;
    var j = 0;
    var date1, date2;
    var result1, result2;
    var cof = 4;
    for (i = 0; i < myvalues.length; i = i + 3) {
        date1 = new Date(null);
        date2 = new Date(null);

        if (i != 0) {
            if (j % 2 != 0) {
                date1.setSeconds(myvalues[i] * cof + 1);
            }
            else {
                if (myvalues[i + 1] - myvalues[i] != 0) {
                    date1.setSeconds(myvalues[i] * cof - (cof - 1) + cof);
                }
                else {
                    date1.setSeconds(myvalues[i] * cof);
                }
            }
        }
        else {
            date1.setSeconds(myvalues[i] * cof);
        }

        if (j % 2 != 0) {
            date2.setSeconds(myvalues[i + 1] * cof + cof);
        }
        else {
            date2.setSeconds(myvalues[i + 1] * cof);
        }

        result1 = date1.toISOString().substr(11, 8);
        result2 = date2.toISOString().substr(11, 8);
        myBar.data.labels[j] = result1 + ' - ' + result2;
        if (j % 2 != 0) {
            myBar.data.datasets[0].data[j] = myvalues[i + 2];
            myBar.data.datasets[1].data[j] = (myvalues[i + 2 - 3] + myvalues[i + 2 + 3]) / 2;
        }
        else {
            myBar.data.datasets[0].data[j] = 0;
            myBar.data.datasets[1].data[j] = myvalues[i + 2];
        }
        j++;
    }
    myBar.update();
}