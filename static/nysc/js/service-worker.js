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
        '/static/nysc/images/google-logo-fallback.png',
        '/static/nysc/favicon/favicon.ico',
        '/static/nysc/json/manifest.json',
        '/static/nysc/json/camp_data.json',
        '/static/nysc/json/nigeria_states.geojson.gz',
        '/static/nysc/js/ppa_finder.js',
        '/static/nysc/js/submit_ppa.js',
        '/static/nysc/js/base.js',
      ]);
    })
  );
});

self.addEventListener('fetch', (event) => {
  // Skip cache for API endpoints
  if (event.request.url.includes('/set_user_state/')) {
    event.respondWith(
      fetch(event.request, { cache: 'no-store' }).catch(() => {
        return caches.match('/'); // Fallback to homepage if offline
      })
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request).then((networkResponse) => {
        // Update cache for static assets
        if (event.request.url.startsWith('/static/')) {
          const clonedResponse = networkResponse.clone();
          caches.open('corps-connect-v1').then((cache) => {
            cache.put(event.request, clonedResponse);
          });
        }
        return networkResponse;
      });
    }).catch(() => {
      return caches.match('/'); // Fallback to homepage if offline
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.filter((cacheName) => cacheName !== 'corps-connect-v1')
          .map((cacheName) => caches.delete(cacheName))
      );
    })
  );
});