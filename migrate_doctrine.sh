#!/bin/sh
#
# Script d'automatisation de génération des classes de migration
# Doctrine pour Symfony 1.x. Nécessite Fabric. Et Git.
#
# Fonctionnement :
#   Appelez le script avec en argument un tag, commit... passé à partir
#   duquel vous voulez comparer l'évolution de votre schema.
#   Le script va voir si des modifs sur un schema (général ou plugin) a
#   été effectuée. Si oui :
#       - copie des schema actuel en tmp
#       - checkout du commit/branch en paramètre
#       - rebuild des classes à l'ancienne version des schemas
#       - copie du tmp des nouveaux schema
#       - génération des classes de migration
#       - checkout force sur la branche d'origine (ATTENTION si vous aviez
#           des modifications non commit)
#       - rebuild des classes basé sur les nouveaux schemas
#
# Auteur : Simon Hostelet. www.erreur500.com
#

if test -z "$1"
then
  echo "Précisez un tag ou un commit"
  exit 1
else
  TAG="$1"
fi


#Détermine le répertoire contenant ce fichier
# Si existe, c'est le bon, sinon le shell est dans le path
test -f $0 && cheminExe=$0 || cheminExe=`which $0`
# Si la commande est un lien, on recupère le fichier pointé par ce lien
test -L $cheminExe && cheminReel=`readlink -f $cheminExe` || cheminReel=$cheminExe
SOURCE_PATH=`dirname $cheminReel`

FABFILE="$SOURCE_PATH/fabfile.py"
PATH=`pwd`
FAB="/usr/local/bin/fab"

CURRENT_TAG=`/usr/bin/git branch | /bin/grep '\*' | /bin/sed -e "s/* //g"`

$FAB -f $FABFILE setup:path=$PATH,tag=$TAG,current_tag=$CURRENT_TAG have_schema_been_modified stash_new_schemas checkout_previous generate_migration back_to_current_tag
