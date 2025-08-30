// firebase-messaging-sw.js

// Importa los scripts del SDK de Firebase
importScripts('https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/8.10.1/firebase-messaging.js');

// Configuración de tu proyecto de Firebase
// Reemplaza los valores con los de tu proyecto
const firebaseConfig = {
    apiKey: "JEj92zH753UENZVjBvbvyoZQ6wvaGEL28bogcAR32G4C1jyQ",
    projectId: "eacccf60-8bbc-4e99-88aa-41c67e24d7e7",
    appId: "1:896256118832:web:a539d665011e0ac9315df5",
    messagingSenderId: "896256118832" // ¡Este es el valor correcto y necesario!
};

// Inicializa Firebase en el Service Worker con la sintaxis de la v8
firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

// Maneja los mensajes cuando la aplicación no está en primer plano
messaging.onBackgroundMessage((payload) => {
    console.log('Mensaje recibido en segundo plano: ', payload);

    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        icon: '/firebase-logo.png' 
    };
    
    // Muestra la notificación al usuario
    return self.registration.showNotification(
        notificationTitle,
        notificationOptions
    );
});