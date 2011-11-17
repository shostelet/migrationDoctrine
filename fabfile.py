#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import with_statement
from fabric.api import *
import os, time
from fabric.utils import abort

try:
    from fabric.colors import blue
except ImportError:
    def blue(string, **kwargs):
        return string


def setup(path, tag, current_tag):
    """Initialise des variables"""

    print("")
    print(blue("Initialisation...", bold=True))

    env.path = os.path.realpath(path)
    env.orm = "doctrine"
    env.tag = tag
    env.current_tag = current_tag
    
    env.path_git = '/usr/bin/git'
    env.path_grep = '/bin/grep'
    env.path_find = '/usr/bin/find'
    env.path_mkdir = '/bin/mkdir'
    env.path_cp = '/bin/cp'
    env.path_php = '/usr/bin/php'


def have_schema_been_modified():
    """S'assure qu'au moins 1 fichier schema.yml a été modifié entre le HEAD
    et le tag voulu. Si non, pas la peine d'executer la migration"""
    
    print("")
    print(blue("Modification de schema ?"))
    
    with settings(hide('warnings', 'stdout'), warn_only=True):
        with cd(env.path):
            output = local("%s diff --name-only %s | %s -i schema.yml" % (env.path_git,
                                                                          env.tag,
                                                                          env.path_grep))
            if output.failed:
                env.have_schema_been_modified=False
                print('')
                print(blue("Aucune modification dans les schema.yml"))
            else:
                env.have_schema_been_modified=True


def stash_new_schemas():
    """Trouve les schemas de la branche courante et les enregistre en tmp"""

    if env.have_schema_been_modified:
        print("")
        print(blue("Copie des schemas...", bold=True))
    
        with settings(hide('warnings', 'stdout'), warn_only=True):
            env.pattern = ".*config/%s/schema\.yml" % env.orm
            env.tmp_dir = "/tmp/migration/%s/%s" % (env.orm, time.time())
        
            output = local("%s %s -iregex %s" % (env.path_find,
                                                 env.path,
                                                 env.pattern), True)
        
            config_list = output.split('\n')
        
            local("%s -p %s" % (env.path_mkdir, env.tmp_dir))
        
            for filename in config_list:
                if os.path.isfile(filename):
                    local("%s --parents %s %s" % (env.path_cp,
                                                  filename,
                                                  env.tmp_dir))


def checkout_previous():
    """Checkout la version précédente identifiée par le tag. Rebuild les classes"""

    if env.have_schema_been_modified:
        with settings(hide('warnings', 'stdout'), warn_only=True):
            with cd(env.path):
        
                print("")
                print(blue("Checkout de l'ancienne version...", bold=True))
        
                local("%s checkout %s" % (env.path_git,
                                          env.tag))
                with settings(hide('stdout')):
        
                    _buildAllClasses()



def generate_migration():
    """Récupère les nouveaux schema depuis tmp et génère les classes de migration"""

    if env.have_schema_been_modified:
        print("")
        print(blue("Récupération des nouveaux schemas...", bold=True))
    
        with settings(hide('warnings', 'stdout'), warn_only=True):
            output = local("%s %s -iregex %s" % (env.path_find,
                                                 env.tmp_dir,
                                                 env.pattern), True)
        
            config_list = output.split('\n')
            for filename in config_list:
                if os.path.isfile(filename):
                    new_filename = filename.replace(env.tmp_dir, '')
                    with settings(hide('warnings', 'stdout'), warn_only=True):
                        (dirName, fileName) = os.path.split(new_filename)
                        local('%s -p %s' % (env.path_mkdir, dirName))
                        if local("%s %s %s" % (env.path_cp,
                                               filename,
                                               new_filename)).failed:
                          abort('Impossible de copier le fichier')
        
            print("")
            print(blue("Classes de migration...", bold=True))
        
            local("%s %s/symfony doctrine:generate-migrations-diff" % (
                env.path_php, env.path))


def back_to_current_tag():
    """Annule les changements éventuels et retourne au tag courant"""
    
    if env.have_schema_been_modified:
        print("")
        print(blue("Retour à la branche d'origine", bold=True))
        
        with settings(hide('warnings', 'stdout'), warn_only=True):
            local('%s checkout -f %s' % (env.path_git, env.current_tag))
            
            _buildAllClasses()


def _buildAllClasses():
    """Rebuild les classes"""
    print("")
    print(blue("Rebuild des classes...", bold=True))

    local("%s symfony doctrine:build --all-classes" % env.path_php)