# Blockchain en Python

Ce projet est une implémentation simple d'une blockchain en Python. Il comprend des classes pour les blocs, les transactions, les arbres de Merkle, les nœuds et les portefeuilles. Cette blockchain utilise l'algorithme de preuve de travail pour valider les blocs et permet aux utilisateurs de créer et d'échanger des transactions.

## Membres de groupe
- Abderrahim BENMELOUKA
- Paul JOURDIN
- Jary VALLIMAMODE

## Fonctionnalités

- Système de nœuds pour la communication et la synchronisation entre les participants
- Création et gestion des blocs
- Création et vérification des transactions
- Gestion d'un arbre de Merkle pour les transactions dans un bloc
- Portefeuilles pour la gestion des soldes et des transactions des utilisateurs
- Algorithme de preuve de travail pour la validation des blocs
- Particularité d'implémentation : utilisation du timestamp à la nanoseconde près au lieu d'un nonce séquentiel ordinaire. Grâce à cette méthode, il est plus facile de vérifier l'instant précis de la fin du minage d'un bloc, ce qui est très utile pour gérer les conflits entre les nœuds.

## Méthodes publiques des classes

### Block
- hash : Calcule le hachage SHA-256 du bloc.
- as_dict : Renvoie une représentation du bloc comme dictionnaire Python.
- transactions : Renvoie la liste des transactions dans le bloc.

### MerkleTree
- as_dict : Renvoie une représentation de l'arbre comme dictionnaire Python.
- build_tree : Construire l'arbre de Merkle.
- get_root : Renvoie le nœud racine de l'arbre de Merkle.
- update_tree : Met à jour l'arbre Merkle en ajoutant de nouvelles transactions.
- get_proof : Renvoie la preuve Merkle d'une transaction.
- verify_proof : Vérifie la preuve Merkle d'une transaction.

### Miner
- spend_mining_reward : Crée une nouvelle transaction en utilisant les UTXO disponibles et envoie le montant souhaité à l'adresse du destinataire.

### Node
- id : Renvoie l'identifiant du nœud, qui est un tuple contenant l'hôte et le port.
- listen : Démarre l'écoute sur le socket entrant du nœud et accepte les connexions entrantes.
- create_transaction : Crée une transaction et l'envoie à d'autres nœuds pour traitement.
- generate_locking_script : Génère le script de verrouillage pour une adresse donnée.
- generate_unlocking_script : Génère le script de déverrouillage.
- generate_key_pair : Génère une paire de clés RSA (privée et publique).
- generate_address : Génère une adresse publique à partir d'une clé publique donnée à l'aide du hachage SHA256.
- wait : Une fonction utilitaire qui met le programme en attente indéfiniment.
         Elle attend une exception KeyboardInterrupt, qui est déclenchée lorsque l'utilisateur termine le programme.
- print : Une fonction utilitaire pour imprimer le texte donné sans entrelacement dû aux threads qui impriment en même temps.

### Script
- execute : Exécute le script avec la pile spécifiée. Chaque opcode est traité un par un, modifiant la pile comme
         nécessaire. Renvoie True si le script s'est exécuté avec succès et False sinon. Les opcodes suivants sont
         prise en charge:

  - "OP_DUP": duplique l'élément supérieur de la pile.
  - "OP_HASH160": Hache l'élément supérieur de la pile en utilisant SHA256. Pousse le hash résultant sur la pile.
  - "OP_EQUALVERIFY": fait apparaître les deux éléments du haut de la pile et vérifie s'ils sont égaux. S'ils ne sont pas égal, renvoie Faux.
  - Tout autre opcode : Pousse l'opcode sur la pile.

### Transaction
- hash : Calcule le hachage SHA-256 de la transaction.
- as_dict : Renvoie une représentation de la transaction comme dictionnaire Python.
- execute : Exécute la transaction en itérant sur chaque paire d'entrée et de sortie, en appliquant leurs scripts de déverrouillage et de verrouillage, respectivement.
- sign_transaction_input : Crée une signature pour la transaction.
- verify_transaction_signature : Vérifie la signature d'une transaction.

### Wallet
- refresh_balance: Mettre à jour le solde du portefeuille en demandant et en attendant les UTXO du réseau.
- get_balance: Calcule et renvoie le solde total du portefeuille en fonction des UTXO actuellement détenus.
- send_crypto: Envoie une transaction de crypto-monnaie du portefeuille à une adresse de destinataire spécifiée.


## Comment utiliser

1. Télécharger le dépot :
```shell
git clone https://github.com/Abdou27/blockchain.git
cd blockchain
```
2. Installez les dépendances nécessaires en utilisant pip :

```shell
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3. Lancer le script de tests, 

```shell
python tests.py
```

N.B : le script peut parfois se bloquer lorsque deux nœuds minent un bloc dans 
un court délai, relancer le script semble résoudre le problème.

N.B.2 : Ce problème a été résolu dans le commit du 15/05/2023, un peu hors délai... La solution a consisté à utiliser des timestamps pour les nonces, ce qui a permis de mettre en place plusieurs nouvelles méthodes de validation de blocs.




