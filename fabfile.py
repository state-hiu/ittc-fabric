import os, glob
from fabric.api import env, sudo, run, cd, local, put, prefix, roles, execute, task
from fabric.api import settings as fab_settings
from fabric.context_managers import settings, hide
from fabric.contrib.files import sed
from fabtools.files import is_file, is_dir, md5sum
from subprocess import Popen, PIPE
import datetime
import hashlib
from servers import ITTC_SERVERS

from utils import _build_env, _print_target, _cron_command, _request_input, _request_continue, _append_to_file, _load_template, _calc_md5sum

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
def add_cache(n=None, d=None, ip=None, l=None, u=None, p=None):
    global target
    if target:
        with fab_settings(** _build_env(target)):
            _add_cache(n=n, d=d, ip=ip, l=l, u=u, p=p)
    else:
        print "Need to set target first."


@task
def upload_file(local=None, drop=None):
    global target
    if target:
        with fab_settings(** _build_env(target)):
            _upload_file(local=local, drop=drop)
    else:
        print "Need to set target first."

#############################################################
# The Private API

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


def _add_cache(n=None, d=None, ip=None, l=None, u=None, p=None):

    data = _load_template('tilecache.cfg')
    if data:

        n = _request_input("Name", n, True)
        d = _request_input("Description", d, True)
        ip = _request_input("IP Address", ip, True)
        l = _request_input("Layers", l, True)
        u = _request_input("User", u, True)
        p = _request_input("Password", p, True)

        data = data.replace("{{name}}", n)
        data = data.replace("{{description}}", d)
        data = data.replace("{{ip}}", ip)
        data = data.replace("{{layers}}", l)
        data = data.replace("{{user}}", u)
        data = data.replace("{{password}}", p)

        print "Data..."
        print data

        if _request_continue():
            _append_to_file(data.split("\n"), "/etc/filecache.cfg")
            _restart_apache()


def _upload_file(local, drop):

    local = _request_input("Local File Path", local, True)
    drop = _request_input("Remote Drop Folder", drop, True)
    if _request_continue():
        sudo("[ -d {d} ] || mkdir {d}".format(d=drop))
        md5 = _calc_md5sum(local)
        print "Current MD5 has: "+md5
        remote_files = put(local, drop, mode='0444', use_sudo=True)
        if remote_files:
            for f in remote_files:
                print "MD5 for "+f+": "+md5sum(f)
            print "Files uploaded"
        else:
            print "Not files uploaded"
