# JARVIS Desktop — B2 Assistant

JARVIS Desktop est un assistant personnel Windows vocal et modulaire. Cette première version privilégie un parcours fiable : cliquer sur le microphone, parler, faire exécuter une action locale contrôlée et recevoir une réponse à l’écran et à voix haute.

Le design est original, sombre et cyan ; il s’inspire de l’idée générale d’un assistant futuriste sans reprendre l’identité visuelle de Marvel.

## Fonctionnalités de la V1

- interface PySide6 avec animation d’état, transcription, réponse et historique ;
- push-to-talk au bouton ou avec `Ctrl + Alt + Espace` ;
- saisie texte utilisable lorsque le micro ou la transcription ne sont pas disponibles ;
- ouverture d’applications Windows et correspondances personnalisables ;
- lecture et réglage exact du volume, mute et unmute ;
- indicateurs CPU, RAM et espace disque ;
- ouverture de dossiers/fichiers et recherche limitée aux dossiers utilisateur ;
- recherche web et ouverture d’URL HTTP(S) ;
- notes persistantes dans SQLite ;
- date, heure et interprétation de dates relatives en français ;
- conversation OpenAI optionnelle avec appel d’outils ;
- synthèse vocale locale avec les voix installées dans Windows ;
- zone de notification Windows et réduction à la fermeture ;
- confirmation explicite des actions sensibles ;
- logs avec rotation dans `logs/jarvis.log` ;
- assistant de premier démarrage pour tester micro, haut-parleur et configuration IA.

## Prérequis

- Windows 10 ou Windows 11 ;
- Python 3.12 ou version ultérieure ;
- un microphone pour le mode vocal ;
- une clé API OpenAI pour la transcription et les requêtes conversationnelles.

Sans clé API, l’application démarre normalement. Les commandes locales restent disponibles via le champ texte et la synthèse vocale reste locale.

## Installation

Dans PowerShell :

```powershell
git clone https://github.com/b2techstudio/jarvis.git
cd jarvis
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Si PowerShell bloque l’activation du venv, lance temporairement :

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

## Configuration

Ouvre `.env` et renseigne les valeurs nécessaires :

```dotenv
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe

ASSISTANT_NAME=Jarvis
LANGUAGE=fr-FR
ENABLE_TTS=true
ENABLE_WAKE_WORD=false
TTS_RATE=180
TTS_VOLUME=0.9
LOG_LEVEL=INFO
GLOBAL_HOTKEY=<ctrl>+<alt>+<space>
MINIMIZE_TO_TRAY=true
```

La clé API n’est jamais affichée en clair dans l’interface ni enregistrée dans les logs. Le fichier `.env` est exclu de Git.

### Ajouter une application

Copie `data/apps.json.example` vers `data/apps.json`, puis ajoute une correspondance :

```json
{
  "obs studio": "C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe"
}
```

Les applications Windows courantes (Bloc-notes, Calculatrice, Explorateur, Edge, Chrome, Firefox, Spotify, Discord, Steam et VS Code) disposent déjà d’alias. Les exécutables sont résolus via le `PATH` et quelques emplacements d’installation classiques.

## Lancement

```powershell
.venv\Scripts\Activate.ps1
python -m app.main
```

### Construire l’exécutable Windows

```powershell
.venv\Scripts\Activate.ps1
pip install -r build-requirements.txt
.\scripts\build-release.ps1
```

Le résultat est créé dans `dist\JARVIS-Desktop\JARVIS-Desktop.exe`. Distribue le dossier `JARVIS-Desktop` complet : les bibliothèques placées dans son sous-dossier `_internal` sont nécessaires. Place un fichier `.env` à côté de l’exécutable pour activer OpenAI. Les dossiers `data` et `logs` sont créés automatiquement à côté de l’exécutable au premier lancement. La clé API et la base locale ne sont jamais incluses dans la distribution.

Au premier démarrage, l’assistant propose trois vérifications. Une fois dans l’écran principal :

1. clique sur le bouton rond du microphone ;
2. parle ;
3. clique à nouveau pour terminer l’enregistrement ;
4. attends la transcription puis l’exécution.

Le champ en bas accepte aussi les mêmes commandes au clavier.

Exemples :

- « Ouvre la calculatrice. »
- « Mets le volume à 30 %. »
- « Quelle heure est-il ? »
- « Note que je dois acheter du café. »
- « Quelles sont mes dernières notes ? »
- « Recherche les dernières nouveautés Python. »
- « Ouvre mes téléchargements. »

## Sécurité

Chaque outil possède un niveau de risque :

- `SAFE` : exécution immédiate, par exemple ouvrir une application ou créer une note ;
- `CONFIRMATION_REQUIRED` : demande un « oui » explicite, par exemple fermer une application ou éteindre le PC ;
- `FORBIDDEN_AUTOMATICALLY` : l’outil ne peut pas être déclenché automatiquement.

Il n’existe aucun outil générique d’exécution PowerShell ou shell. La suppression de fichiers, le formatage, les modifications massives du registre et l’exécution d’un programme téléchargé sont absents de la V1.

## Architecture

```text
app/
├── main.py                 # composition et démarrage Qt
├── core/                   # moteur, routeur, configuration, événements, logs
├── ai/                     # abstraction IA et provider OpenAI
├── voice/                  # micro, STT, TTS, point d’extension wake word
├── tools/                  # outils contrôlés et niveaux de risque
├── memory/                 # SQLite, modèles et repositories
└── ui/                     # fenêtre, paramètres, onboarding, widgets, thème
data/                       # base locale et correspondances d’applications
logs/                       # journaux avec rotation
tests/                      # tests des composants critiques
```

L’interface ne contacte jamais directement OpenAI. Elle transmet le texte au moteur, qui utilise d’abord le routeur local, puis éventuellement le provider IA. Toutes les actions passent par le registre d’outils.

## Ajouter un outil

Crée une classe dérivée de `AssistantTool` :

```python
from app.tools.base import AssistantTool, RiskLevel, ToolResult


class MyTool(AssistantTool):
    name = "my_tool"
    description = "Description courte destinée au modèle."
    risk_level = RiskLevel.SAFE
    parameters = {"value": {"type": "string"}}

    async def execute(self, **kwargs):
        value = str(kwargs.get("value", ""))
        return ToolResult(True, f"Valeur reçue : {value}")
```

Enregistre ensuite l’instance dans `build_registry()` dans `app/main.py`. Si la commande doit fonctionner sans IA, ajoute également son intention explicite à `CommandRouter`.

## Tests

```powershell
.venv\Scripts\Activate.ps1
pytest -q
```

Les tests couvrent la configuration, SQLite, le registre, la sécurité, les applications, le routeur et la confirmation des actions sensibles.

## Données et logs

- base SQLite : `data/jarvis.db` ;
- logs : `logs/jarvis.log` avec trois rotations de 2 Mo ;
- aucun audio brut n’est sauvegardé ;
- le contenu des conversations locales est conservé dans SQLite afin de préparer l’historique futur ;
- les clés et secrets ne sont jamais journalisés.

## Limites connues de la V1

- la transcription vocale utilise OpenAI ; un moteur STT local pourra remplacer le provider sans modifier l’interface ;
- le wake word est préparé architecturalement mais désactivé ;
- le choix précis du périphérique micro et le démarrage automatique Windows ne sont pas encore persistés ;
- la compréhension locale se concentre sur les commandes essentielles en français ;
- l’historique affiché correspond à la session courante, même si les échanges sont persistés ;
- les commandes multi-étapes et les références complexes restent limitées.

## Roadmap

- moteur STT local et wake word local ;
- calendrier, e-mail, météo, rappels et tâches programmées ;
- Home Assistant, MQTT, routines et Wake-on-LAN ;
- système de plugins avec permissions ;
- mémoire longue durée contrôlable ;
- modèle LLM local facultatif ;
- notifications, téléphone et application mobile compagnon ;
- commandes multi-PC et serveur local facultatif.

## Dépannage

Si le micro ne fonctionne pas, vérifie les autorisations Windows dans **Paramètres > Confidentialité et sécurité > Microphone**. Tu peux toujours utiliser le champ texte.

Si l’IA est indisponible, vérifie `OPENAI_API_KEY`, la connexion réseau et `logs/jarvis.log`. Les outils locaux ne dépendent pas du service conversationnel.

Si l’application semble fermée, cherche son icône dans la zone de notification : la fermeture réduit la fenêtre par défaut.
