// A coleta exige conexão com o servidor. Não armazenar respostas ou dados pessoais.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => { });
