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
- Particularité d'implémentation : utilisation du timestamp au nanoseconde près au lieu d'un nonce séquentiel ordinaire. Grâce à cette méthode, il est plus facile de vérifier l'instant précis de la fin du minage d'un bloc, ce qui est très utile pour gérer les conflits entre les nœuds.


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




