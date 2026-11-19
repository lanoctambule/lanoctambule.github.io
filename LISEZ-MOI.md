# Guide du blog (sans rien connaître au code)

Ce dossier contient ton blog complet. Il est gratuit, sans cookies ni traceurs, et prévu pour être publié avec **GitHub Pages**.

## 1. Mettre le blog en ligne (une seule fois)

1. Crée un compte gratuit sur [github.com](https://github.com).
2. Clique sur **New repository** (nouveau dépôt). Donne-lui un nom (ex. `mon-blog`), choisis **Public**, puis **Create repository**.
3. Clique sur **uploading an existing file** et glisse **tout le contenu** de ce dossier (utilise un ordinateur : c'est plus simple qu'un téléphone). Valide avec **Commit changes**.
4. **Vérifie que le dossier caché `.github` est bien arrivé.** S'il manque, clique sur **Add file → Create new file**, tape comme nom `.github/workflows/deploy.yml` et colle le contenu du fichier `deploy.yml` fourni.
5. Va dans **Settings → Pages** et, sous **Source**, choisis **GitHub Actions**.
6. Attends 1 à 2 minutes (onglet **Actions**, une coche verte apparaît). Ton blog est en ligne à l'adresse `https://TON-PSEUDO.github.io/mon-blog/`.

> Astuce : si tu nommes le dépôt `TON-PSEUDO.github.io`, l'adresse sera simplement `https://TON-PSEUDO.github.io/`.

## 2. Compléter les informations légales (obligatoire)

Ouvre le fichier `config.json` (bouton crayon sur GitHub). Le blog est configuré pour rester **anonyme sous pseudonyme** : vérifie que l'adresse e-mail de contact (`editeur_email`) est bien celle que tu veux rendre publique.

Autres réglages utiles :

- `title` : le nom du blog ; `tagline` et `subtagline` : les deux phrases d'accroche
- `pseudo` : le nom avec lequel tu signes
- `instagram` : ton pseudo, pour afficher un lien dans le pied de page

**Rester anonyme : ce qu'il faut respecter**

- La loi autorise un particulier à ne pas afficher son identité sur un site **non commercial**, à condition d'avoir communiqué ses informations personnelles à l'hébergeur.
- **Pas de liens affiliés, de publicité ni d'articles sponsorisés** sur ce blog. Si tu en ajoutes un jour, il faudra passer à des mentions légales professionnelles (ton nom, une adresse, ton numéro d'immatriculation) : demande-moi, la mise à jour est prévue.
- N'écris jamais ton vrai nom ni ton SIREN dans les fichiers : le dépôt GitHub est public, tout ce qu'il contient est lisible.
- Utilise un pseudo pour ton compte GitHub et active « Keep my email addresses private » dans les réglages de ton profil.

## 3. Publier (le plus simple : la page « Écrire »)

Ton blog est un **fil** : tu peux y poster des **notes rapides** (texte court, photo possible, sans titre) et des **chroniques** (avec un titre et un résumé).

1. Ouvre `https://TON-PSEUDO.github.io/ecrire/` (ajoute-la à tes favoris ou à l'écran d'accueil de ton téléphone : elle n'apparaît nulle part sur le blog).
2. **La première fois seulement**, crée ta clé d'accès en suivant le guide affiché sur la page (2 minutes), puis colle-la : elle reste sur ton appareil.
3. Choisis **Note rapide** ou **Chronique**, la catégorie, écris ton texte, ajoute une photo si tu veux, puis **Publier**.
4. Le blog se met à jour tout seul en 1 à 2 minutes.

La photo est automatiquement réduite et débarrassée de ses données cachées (lieu, modèle d'appareil).

**Supprimer une publication** : en bas de la page « Écrire », la liste « Mes publications » montre tes dernières publications (les plus récentes d'abord). Clique sur **Supprimer** et confirme : la publication disparaît du blog en 1 à 2 minutes, avec sa photo si elle a été ajoutée par cette page. Pour la masquer sans la supprimer, ajoute `brouillon: oui` à la main dans son fichier.

**Méthode manuelle (toujours possible)** : sur GitHub, ouvre le dossier `posts`, puis **Add file → Create new file**, nomme-le `2026-12-01-mon-article.md` et copie le contenu de `_modele.md`. Pour une note rapide, utilise `type: note` et supprime la ligne `title:` (voir `posts/2026-11-19-exemple-note.md`).

Catégories possibles : `Lecture`, `Films & séries`, `Musique`.
Pour garder une publication en brouillon, ajoute la ligne `brouillon: oui` dans l'en-tête.

**Sécurité de la clé d'accès** : elle ne donne accès qu'à ce blog. Ne la partage jamais et ne la colle nulle part ailleurs que sur la page « Écrire ». Si tu perds ton appareil, supprime-la dans GitHub (Settings → Developer settings → Fine-grained tokens).

## 4. Ajouter une image

Avec la page « Écrire », c'est automatique. À la main :

1. Dépose-la dans le dossier `static/images/` (prends des images légères, moins de 300 Ko).
2. Dans l'en-tête d'une publication, ajoute `image: /images/nom-du-fichier.jpg` et `image_alt: Description de l'image`, ou, dans le texte d'une chronique, écris `![Description de l'image](/images/nom-du-fichier.jpg)`.

## 5. Rester conforme au RGPD

Le blog est conforme tel quel parce qu'il n'utilise **aucun service tiers**. Pour que ça reste vrai :

- **N'intègre pas** de lecteur YouTube, Spotify, Instagram, etc. : ils déposent des cookies chez tes lecteurs. Mets plutôt un simple lien.
- **N'ajoute pas** Google Analytics, Google Fonts, boutons de partage ou commentaires. Si tu veux des statistiques, choisis un outil respectueux comme Plausible ou Umami, et dis-le-moi pour que je mette à jour la politique de confidentialité.
- **Complète** les mentions légales (étape 2).
- Pas de formulaire de contact : une adresse e-mail suffit.

## Besoin d'aide ?

Reviens vers Claude, avec ton texte d'article ou ta demande de modification, et il fera les changements pour toi.
