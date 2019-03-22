window.onload = function() {
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
};