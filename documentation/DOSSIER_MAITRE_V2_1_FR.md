# FMP Mes Transferts — Dossier maître V2.1

**État vérifié le 4 novembre 2026.** Projet Android indépendant et widget Samsung 4×2 consacré aux offres de transfert de **Football Manager Project (FMP)**. Ni modification de l'APK officiel, ni fusion avec FMP Squad Advisor.

## 1. Objectif précis

Lire et afficher, sur l'accueil Android et dans une application compacte, les informations concernant la propre équipe du joueur : **favoris**, **offres reçues**, **offres émises** et **offres en attente**. Il ne s'agit pas d'un moteur de recherche du marché. Les informations essentielles sont le nom du joueur, le montant de l'offre, le statut, le délai restant et l'heure de lecture.

L'utilisateur souhaite aussi pouvoir interagir un jour avec les transferts. **À V2.1, le logiciel n'envoie aucune enchère réelle.** Les boutons existants ouvrent FMP ou gèrent des fiches locales.

## 2. Livrables joints

| Fichier / dossier | Contenu |
|---|---|
| `00_GUIDE_INTERACTIF_TELEPHONE.html` | Guide hors ligne lisible dans un navigateur mobile |
| `03_APPLICATION_APK/` | APK Android V2.1 issu de la compilation GitHub du 3/11/2026 |
| `04_FIREFOX_DIRECT_BRIDGE/` | Userscript V2.1 corrigé pour Firefox Android et Violentmonkey |
| `05_SOURCES_ANDROID/` | Sources Gradle/Java, ressources Android, tests et script source |
| `02_INSTALLATION/` | Étapes d'installation et de liaison sur Samsung |
| `06_TESTS_ET_VERIFICATIONS/` | Contrôles et empreintes des fichiers |
| `07_CAPTURES_DE_TEST/` | Huit captures représentant les tests et les défauts rencontrés |
| `09_ARCHITECTURE/` | Schéma de flux et dictionnaire des données |

## 3. Architecture fonctionnelle

### A — Application FMP officielle (lecture OCR)

1. L'utilisateur active volontairement le partage d'écran via Android MediaProjection.
2. Il ouvre l'application FMP et la page « Offres concernant votre équipe ».
3. ML Kit OCR traite localement les mots visibles et leurs positions.
4. Un parseur affecte les mots aux colonnes et aux quatre rubriques.
5. Le cache privé conserve les lignes détectées, les montants et une heure de fin estimée.
6. L'application et le widget affichent les relevés sans connexion à un serveur de transfert FMP.

Cette voie fonctionnait sur l'APK officiel lors des essais V1.6/V1.7. La V2.1 **n'a pas pour objectif de changer ce moteur**, seulement l'interface et le canal Firefox.

### B — Firefox Android (lecture DOM/HTML sans OCR)

1. Firefox ouvre la page web FMP authentifiée.
2. Le script Violentmonkey indépendant lit les cellules HTML des tableaux d'offres.
3. Il supprime les badges parasites de FMP Squad Advisor, normalise noms, prix et délais.
4. Il transmet une liste structurée à `http://127.0.0.1:28471/v2/transfers` avec l'en-tête privé `X-FMP-Bridge-Token`.
5. Le service Android vérifie la clé, importe les lignes, les associe aux catégories et actualise le widget.

La connexion HTTP est sur **l'adresse de bouclage locale** du téléphone et ne publie pas les données sur Internet. Le pont doit être activé et Firefox doit pouvoir lire les tableaux ; aucune API officielle du jeu n'a été identifiée.

### C — Comptes à rebours et widget

Le logiciel enregistre `deadlineAt` (échéance Unix en millisecondes) calculé à partir du texte de durée et de l'heure de lecture. À chaque affichage, il calcule `max(0, deadlineAt - maintenant)`. Les heures/minutes visibles dans FMP pouvant être arrondies, ce décompte reste une **estimation**. Dans l'application, l'affichage est réévalué à la seconde ; pour le widget Android, un chronomètre natif est utilisé et les rafraîchissements après échéance peuvent être différés par le système.

## 4. Interface V2.1

**Accueil :** en-tête FMP · TRANSFERTS, accès ⚙ Paramètres, onglets Favoris / Reçues / Mes offres / Attente, cartes de joueurs, prix, délais, source et dernière lecture. L'objectif est de faire apparaître les joueurs immédiatement, sans passer par les boutons techniques.

**Paramètres :** installation du widget Samsung, démarrage/arrêt OCR, démarrage/arrêt pont Firefox, copie de clé, nettoyage des relevés, diagnostic OCR et raccourci vers FMP.

**Widget 4×2 :** vue compacte des favoris, montants, comptes à rebours et accès à l'application.

## 5. Données enregistrées

Le modèle `TransferStore.Entry` contient `section` (0 favoris, 1 reçues, 2 mes offres, 3 attente), `name`, `offer`, `deadline` (texte source), `deadlineAt` (heure de fin estimée), `updated` (date de relevé), `source` (ex. `FMP écran`, `FMP Firefox (HTML)`), et `draft` (brouillon personnel). Les données sont stockées localement dans les préférences privées de l'application.

Un champ absent dans un nouveau relevé ne doit pas effacer un montant déjà connu. Un favori hors de l'écran actuel ne doit pas être supprimé automatiquement.

## 6. Ce qui est réellement confirmé

- Les captures du 3/11 montrent le fonctionnement de l'APK V1.6 : deux favoris Axel Focquet et Hichem Becker, montants et délais reconnus.
- Les captures de V1.7 montrent l'affichage du compte à rebours dans l'application et le widget Samsung.
- V2.0 a installé la communication Firefox HTML vers le cache Android : une fiche Axel apparaît avec source « FMP Firefox (HTML) ».
- V2.0 comportait un nom corrompu « Axel FocquetNON », une ligne Hichem manquante, et trop de commandes sur l'accueil.
- La V2.1 a été compilée et ses tests sources reconstruits passent. **Le comportement réel de son interface et de ses imports sur le Samsung n'a pas encore été confirmé par une capture utilisateur V2.1 dans cette conversation.**

## 7. Anomalies et précautions

- **V2.1 : erreur détectée dans le workflow GitHub de publication** : celui-ci copie `firefox/FMP_Direct_Bridge_V2_0.user.js` vers un fichier nommé `FMP_Direct_Bridge_V2_1.user.js`. Utiliser plutôt `04_FIREFOX_DIRECT_BRIDGE/FMP_Direct_Bridge_V2_1_CORRIGE.user.js` de ce dossier, reconstruite et testée depuis les sources V2.1.
- FMP Squad Advisor peut ajouter des étiquettes (« NON PERTINENT », « RISQUÉ / PETIT GAIN ») à l'intérieur des cellules HTML. Ne pas les associer aux noms.
- Le bouton flottant peut masquer certaines données ; il faut afficher « non relevé » plutôt que d'inventer une offre.
- La V2.1 peut nettoyer les vieilles fiches Firefox finissant par `NON` quand la ligne corrigée arrive, mais un nettoyage manuel peut rester nécessaire pour d'autres fiches.
- Les prix et délais affichés sont les derniers **relevés** ; ce ne sont pas des disponibilités FMP en temps réel garanties.
- Android peut limiter les services d'arrière-plan, la capture d'écran et l'actualisation de certaines vues.
- Les builds ont été distribués avec une signature de développement ; mise à jour par-dessus une ancienne version parfois impossible.

## 8. Sécurité et confidentialité

La version V2.1 déclare `INTERNET` pour la communication locale TCP, ainsi que les permissions de service de premier plan nécessaires ; elle **n'a pas de service d'accessibilité**. L'utilisateur déclenche le partage d'écran. La clé privée de liaison est générée sur l'appareil (32 octets aléatoires, représentation hexadécimale de 64 caractères), et le socket écoute uniquement sur `127.0.0.1:28471`. Aucun mot de passe bancaire, cookie FMP ni mot de passe de jeu ne doit être transmis au pont.

L'application utilise le rendu de FMP sans fournir d'accès administrateur ou de droits sur les serveurs du jeu. Ne pas désactiver Play Protect pour forcer une version bloquée.

## 9. Reste à réaliser / feuille de route

1. Valider V2.1 sur le Samsung : accueil épuré, écran Paramètres, quatre catégories, stabilité du pont local.
2. Vérifier que la version du script réellement active dans Violentmonkey correspond au **script corrigé du présent dossier**.
3. Valider en conditions réelles : deux favoris visibles même avec Squad Advisor ; aucun nom parasité ; montants et délais correctement associés.
4. Ajouter un affichage explicite des états `pont actif`, `dernière synchronisation réussie`, `données périmées`.
5. Expliquer les durées arrondies, écarts OCR/DOM, fin estimée et statut vendu.
6. Étudier les liens profonds autorisés vers les fiches de joueurs dans FMP, plutôt que promettre des achats à partir du widget.
7. Mettre en place une signature de publication stable et des tests d'installation/mise à jour sur l'appareil cible.
8. Ne permettre une éventuelle interaction de transfert que si une interface officielle ou un flux validé autorise l'opération, avec confirmation de l'utilisateur.

## 10. Sources et disponibilité

- Répertoire GitHub du projet : https://github.com/elecmaspetit-tech/FMP-Genie
- Release Android V2.1 : https://github.com/elecmaspetit-tech/FMP-Genie/releases/tag/fmp-widget-v2.1.0
- APK V2.1 : https://github.com/elecmaspetit-tech/FMP-Genie/releases/download/fmp-widget-v2.1.0/FMP_Mes_Transferts_V2_1_Accueil_Transferts.apk
- Script Firefox **corrigé** : fourni dans le ZIP, pour éviter l'écart de publication identifié.

Document préparé à partir de l'historique de cette conversation, des captures fournies et des sources GitHub accessibles le 04/11/2026.