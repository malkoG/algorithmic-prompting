(function () {
  var statusEl = document.getElementById('spk-status');

  function setStatus(text, color) {
    if (!statusEl) return;
    statusEl.textContent = text;
    statusEl.style.opacity = 0.85;
    if (color) statusEl.style.background = color;
  }

  function connect() {
    var proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    var ws = new WebSocket(proto + '//' + location.host + '/?key=' + new URLSearchParams(location.search).get('key'));

    ws.onopen = function () {
      setStatus('connected', 'rgba(90,180,90,0.35)');
    };
    ws.onclose = function () {
      setStatus('disconnected — retrying…', 'rgba(200,90,90,0.35)');
      setTimeout(connect, 1500);
    };
    ws.onerror = function () {
      ws.close();
    };
    ws.onmessage = function (evt) {
      try {
        var msg = JSON.parse(evt.data);
        if (msg.type === 'reload') location.reload();
      } catch (_err) {
        /* ignore */
      }
    };

    window.__spkSend = function (payload) {
      if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(payload));
    };
  }

  window.toggleSelect = function (el) {
    var container = el.closest('.options, .cards, .approve-reject, .split');
    var multi = container && container.hasAttribute('data-multiselect');
    if (container && !multi) {
      var siblings = container.querySelectorAll('.option.selected, .card.selected, button.selected, .mockup.selected');
      for (var i = 0; i < siblings.length; i++) {
        if (siblings[i] !== el) siblings[i].classList.remove('selected');
      }
    }
    el.classList.toggle('selected');
    var choice = el.getAttribute('data-choice');
    var titleEl = el.querySelector('h3') || el.querySelector('.mockup-header');
    var text = titleEl ? titleEl.textContent.trim() : el.textContent.trim();
    var selected = el.classList.contains('selected');
    if (window.__spkSend) {
      window.__spkSend({ type: 'click', choice: choice, text: text, selected: selected });
    }
  };

  connect();
})();
