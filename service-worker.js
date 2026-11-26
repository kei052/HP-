const CACHE_NAME = "lecture-support-pwa-v5-backend-catalog";

const APP_FILES = [
  "./",
  "./index.html",
  "./anke-to.html",
  "./history.html",
  "./jobs.html",
  "./licenses.html",
  "./mypage.html",
  "./manifest.webmanifest",
  "./rishu-account.js",
  "./api-demo.html",
  "./js/api-demo.js",
  "./rishu-catalog.js",
  "./rishu-enhance.js",
  "./rishu-enhance.css",
  "./rishu-mypage.js",
  "./icons/icon-192.png",
  "./icons/icon-512.png"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(APP_FILES))
  );
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(names => Promise.all(
      names.filter(name => name !== CACHE_NAME).map(name => caches.delete(name))
    ))
  );
  self.clients.claim();
});

self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;
  const path = new URL(event.request.url).pathname;
  // Never cache user accounts or live backend catalog/API responses.
  if (path.startsWith("/api/") || path.startsWith("/backend/") || ["/courses","/jobs","/qualifications"].includes(path)) return;

  event.respondWith(
    fetch(event.request)
      .then(response => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
