import os, glob
from fabric.api import env, sudo, run, cd, local, put, prefix, roles, execute, task
from fabric.api import settings as fab_settings
from fabric.context_managers import settings, hide
from fabric.contrib.files import sed
from subprocess import Popen, PIPE
import datetime

from servers import ITTC_SERVERS

global target
target = None

#############################################################
# The Public API

@task
def frontdoor():
    global target
    target = ITTC_SERVERS['frontdoor']
    _print_target(target)


@task
def tilejet():
    global target
    target = ITTC_SERVERS['tilejet']
    _print_target(target)


@task
def tileserver_frontend():
    global target
    target = ITTC_SERVERS['tileserver_frontend']
    _print_target(target)


@task
def tileserver_backend():
    global target
    target = ITTC_SERVERS['tileserver_backend']
    _print_target(target)


@task
def restart_nginx(*args):
    global target
    if target:
        with fab_settings(** _build_env(target)):
            _restart_nginx()
    else:
        print "Need to set target first."


@task
def restart_apache(*args):
    global target
    if target:
        with fab_settings(** _build_env(target)):
            _restart_apache()
    else:
        print "Need to set target first."


@task
def restart_geoserver(*args):
    global target
    if target:
        with fab_settings(** _build_env(target)):
            _restart_geoserver()
    else:
        print "Need to set target first."


@task
def inspect(*args):
    global target
    if target:
        with fab_settings(** _build_env(target)):
            _inspect()
    else:
        print "Need to set target first."


@task
def add_cache(*args):
    global target
    if target:
        with fab_settings(** _build_env(target)):
            _add_cache()
    else:
        print "Need to set target first."


#############################################################
# The Private API

def _build_env(t):
    e = {
        'user': target['user'],
        'hosts': [target['host']],
        'host_string': target['host'],
        'key_filename': target['ident'],
    }
    return e


def _print_target(target):
    print "Connecting to server..."
    print "User: "+target['user']
    print "Host: "+target['host']
    print "#######################"
    print ""

def _inspect():
    _lsb_release()
    _df()

def _lsb_release():
    run('lsb_release -c')


def _df():
    run('df -h')


def _host_type():
    run('uname -s')


def _restart_nginx():
    sudo('/etc/init.d/nginx restart')


def _restart_apache():
    sudo('/etc/init.d/apache2 restart')


def _restart_geoserver():
    sudo('/etc/init.d/tomcat7 restart')


def _add_cache():
    data = None
    with open ('templates/tilecache.cfg', "r") as f:
        data = f.read()

    if data:
        print "Instructions:"
        print "Fill in the details for the tile cache to add."
        print "You'll be given a chance to confirm."

        print "Name:",
        name = raw_input()
        print "Description:",
        description = raw_input()
        print "IP Address:",
        ip = raw_input()
        print "Layers:",
        layers = raw_input()
        print "User:",
        user = raw_input()
        print "Password:",
        password = raw_input()
        print "#######################"
        data = data.replace("{{name}}", name)
        data = data.replace("{{description}}", description)
        data = data.replace("{{ip}}", ip)
        data = data.replace("{{layers}}", layers)
        data = data.replace("{{user}}", user)
        data = data.replace("{{password}}", password)

        print data
        print "Continue (y/n)?",
        confirm = raw_input()

        if confirm and confirm.lower() == "y":
            print "Confirmed"
            for line in data.split("\n"):
                t = "echo '{line}' >> {tc}"
                c = t.format(line=line.replace('"','\"'), tc='/etc/tilecache.cfg')
                sudo(c)

            _restart_apache()
