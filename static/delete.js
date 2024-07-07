window.addEventListener('unload', function(event) {
    navigator.sendBeacon('/cleanup');
});
