// static/nysc/js/service-worker.js
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('corps-connect-v1').then((cache) => {
      return cache.addAll([
        '/',
        '/static/nysc/css/styles.css',
        '/static/nysc/css/custom.css',
        '/static/nysc/js/service-worker.js',
        '/static/nysc/json/nigeria_lgas.json',
        '/static/nysc/images/icon.png',
        '/static/nysc/images/icon(1).png',
        '/static/nysc/favicon/favicon.ico.png',
        '/static/nysc/json/manifest.json',
        '/static/nysc/json/camp_data.json',
        '/static/nysc/js/ppa_finder.js',
        '/static/nysc/js/submit_ppa.js',
        '/static/nysc/js/base.js',
        // Add other static assets or routes as needed
      ]);
    })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});