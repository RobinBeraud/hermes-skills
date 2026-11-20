# Installation d'un second cerveau compatible Obsidian — 100 % VPS

## Mission

Installe et configure un **second cerveau persistant, compatible avec le format de coffre Obsidian**, hébergé **exclusivement sur mon VPS**, afin que **Claude Code** et **Hermès** puissent consulter et enrichir les mêmes connaissances.

> Important : il ne s'agit pas d'installer l'application graphique Obsidian sur le VPS. Le coffre est un répertoire de fichiers Markdown lisibles par Obsidian et directement utilisables par les agents. Site officiel : https://obsidian.md/

## Contraintes impératives

- Aucune installation nécessaire sur le Mac ou le PC du participant.
- Aucun abonnement ou service payant obligatoire.
- Aucune interface graphique requise ; fonctionnement à distance via SSH.
- Les données du coffre demeurent sur le VPS, sans synchronisation vers les postes locaux ni service cloud tiers.
- Ne pas exposer les fichiers ni une interface d'administration publiquement sur Internet.
- Préserver la configuration actuelle d'Hermès, de Claude Code et du serveur.
- Ne jamais enregistrer de mot de passe, jeton d'API, clé privée ou secret dans le coffre.
- Conserver **les skills Claude et les skills Hermès distincts** ; seule la base de connaissances est partagée.

## 1. Diagnostic avant toute modification

1. Détecte le système d'exploitation, les utilisateurs, les permissions et les disques disponibles.
2. Identifie les installations et versions de Claude Code et d'Hermès, leurs comptes d'exécution, leurs chemins de configuration et leurs mécanismes de skills/outils.
3. Recherche un éventuel coffre Obsidian ou dossier Second-Brain existant ; ne crée pas de doublon.
4. Vérifie la méthode la plus simple et sûre pour permettre l'accès en lecture/écriture à chacun des agents.
5. Présente toute opération destructive ou changement sensible avant de l'exécuter.

## 2. Créer le coffre Markdown

Utilise `/opt/second-brain/` si le chemin est adapté au VPS ; sinon explique le chemin choisi. Crée les dossiers :

```text
second-brain/
├── 00-Inbox/
├── 01-Profil/
├── 02-Projets/
├── 03-Connaissances/
├── 04-Agents/
├── 05-Skills/
├── 06-Workflows/
├── 07-Decisions/
├── 08-Memoire/
├── 09-Ressources/
├── 99-Archives/
└── README.md
```

Ajoute un `README.md` présentant les conventions de nommage, les liens internes `[[Nom de note]]`, les métadonnées YAML optionnelles, les règles d'archivage et les précautions de confidentialité. Utilise des fichiers `.md` en UTF-8, sans dépendance à un plugin Obsidian. Le coffre doit rester utilisable sans l'application Obsidian.

## 3. Connecter Claude Code

- Fournis à Claude Code un accès limité en lecture et écriture au coffre.
- Ajoute des instructions de projet ou un **skill Claude dédié** selon les conventions réellement supportées par la version installée.
- Capacités attendues : rechercher, consulter, créer, mettre à jour, catégoriser, résumer et relier des notes ; enregistrer les décisions avec dates et contexte.
- Ne modifie pas les skills existants ; évite de charger tout le coffre dans le contexte de l'agent à chaque conversation.

## 4. Connecter Hermès

- Vérifie les mécanismes pris en charge **par la version installée** : accès au système de fichiers, skills, outils, MCP ou API. Ne suppose pas qu'un protocole est disponible sans l'avoir testé.
- Crée un **skill ou outil Hermès distinct** pour les mêmes opérations sur le coffre.
- Utilise le même répertoire physique que Claude Code : aucune copie indépendante ni synchronisation.
- N'accorde que les droits nécessaires et protège les autres répertoires du VPS.

## 5. Recherche, écriture et cohérence

- Commence par une recherche simple dans les fichiers Markdown (noms, métadonnées et contenu), sans serveur de base de données obligatoire.
- Pour l'écriture, utilise une stratégie sûre : fichier temporaire et remplacement atomique lorsque pertinent, verrouillage ou coordination lors d'accès concurrents.
- Avant de créer une nouvelle note, recherche les doublons et les notes déjà liées.
- Distingue les faits établis, hypothèses, décisions et éléments à vérifier.
- Ne réécris pas silencieusement des informations contradictoires : conserve une trace de la source et de la date.

## 6. Sécurité et sauvegarde

- Configure les propriétaires, groupes et permissions minimales adaptées aux comptes exécutant Claude Code et Hermès.
- Évite l'usage de `root` pour les opérations ordinaires des agents.
- Mets en place des sauvegardes automatiques et vérifie qu'elles sont restaurables. Si les sauvegardes doivent rester **strictement sur le VPS**, indique explicitement qu'une panne ou perte du VPS pourrait supprimer données et sauvegardes, et propose une option hors VPS uniquement après accord.
- Documente comment auditer les accès et restaurer le coffre.

## 7. Tests de validation

1. Claude Code crée une note de test dans `00-Inbox`.
2. Hermès recherche et lit cette note.
3. Hermès crée une deuxième note de test.
4. Claude Code retrouve et lit cette deuxième note.
5. Vérifie les permissions, l'absence d'accès public, la persistance après redémarrage et le fonctionnement de la sauvegarde.
6. Vérifie que les skills Claude et Hermès restent séparés.
7. Supprime les notes de test si elles ne servent plus, sans toucher aux données existantes.

## 8. Livrables attendus

- Chemin définitif du coffre.
- Arborescence et conventions d'organisation.
- Description des intégrations Claude Code et Hermès, avec chemins des skills/outils créés.
- Commandes utiles pour consulter et rechercher les notes par SSH.
- Politique de permissions et de sauvegarde.
- Résultats explicites de chaque test, en distinguant **réussi**, **non testé** et **échec**.
- Limitations, risques identifiés et améliorations facultatives.

**Critère de succès : un second cerveau Markdown unique, centralisé sur le VPS, persistant, sécurisé, gratuitement exploitable par Claude Code et Hermès, sans installation d'Obsidian sur les postes des participants.**
