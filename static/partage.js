/* Bouton « Partager » : menu de partage du téléphone, sinon copie du lien.
   Aucun service tiers, aucun cookie, rien n'est envoyé nulle part. */
(function () {
  "use strict";
  var buttons = document.querySelectorAll("button.share");
  Array.prototype.forEach.call(buttons, function (btn) {
    btn.hidden = false;
    btn.addEventListener("click", function () {
      var url = new URL(btn.getAttribute("data-url"), window.location.href).href;
      var title = btn.getAttribute("data-title") || document.title;
      var status = btn.parentNode.querySelector(".share-status");
      function say(msg) {
        if (!status) return;
        status.textContent = msg;
        setTimeout(function () { status.textContent = ""; }, 3000);
      }
      if (navigator.share) {
        navigator.share({ title: title, url: url }).catch(function () {});
        return;
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(
          function () { say("Lien copié !"); },
          function () { window.prompt("Copie ce lien :", url); }
        );
      } else {
        window.prompt("Copie ce lien :", url);
      }
    });
  });
})();
