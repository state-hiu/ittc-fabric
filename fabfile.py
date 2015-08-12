import os, glob
from fabric.api import env, sudo, run, cd, local, put, prefix, roles, execute, task
from fabric.api import settings as fab_settings
from fabric.context_managers import settings, hide
from fabric.contrib.files import sed
from fabtools.files import is_file, is_dir, md5sum
from glob import glob
from subprocess import Popen, PIPE
import datetime
import hashlib
from servers import ITTC_SERVERS

from utils import _build_env, _print_target, _cron_command, _request_input, _request_continue, _append_to_file, _load_template, _calc_md5sum, _notify_file_uploaded, _parse_manifest, _notify_file_uploads

try:
    from aws import AWS_SETTINGS
except:
    print "Error: Could not import local aws module (aws.py)."

global target
target = None

#############################################################
# The Public API

@task
def frontdoor():
    """
    Load environment for frontdoor server

    Loads environment for front door server.  Frontdoor server
    is at the root domain.  All tile requests flow through
    the front door. 
    """

    global target
    target = ITTC_SERVERS['frontdoor']
    _print_target(target)


@task
def tilejet():
    """
    Load environment for tilejet server

    Loads environment for tilejet server.  TileJet server
    is between the front door and front-end tile server.
    It caches select tiles into memory.
    """

    global target
    target = ITTC_SERVERS['tilejet']
    _print_target(target)


@task
def tileserver_frontend():
    """
    Load environment for front-end tile server.

    Loads environment for front-end tile server.  The 
    front-end tile server is an on-disk cache for tiles
    that sits in front of the tileserver backend (tile renderer).
    """

    global target
    target = ITTC_SERVERS['tileserver_frontend']
    _print_target(target)


@task
def tileserver_backend():
    """
    Load environment for back-end tile server.

    Loads environment for back-end tile server.  The 
    back-end tile server renders tiles from on-disk
    raw imagery.
    """

    global target
    target = ITTC_SERVERS['tileserver_backend']
    _print_target(target)


@task
def restart_nginx(*args):
    """
    Restart NGINX server

    """

    global target
    if target:
        with fab_settings(** _build_env(target)):
            _restart_nginx()
    else:
        print "Need to set target first."


@task
def restart_apache(*args):
    """
    Restart Apache2 Server

    """

    global target
    if target:
        with fab_settings(** _build_env(target)):
            _restart_apache()
    else:
        print "Need to set target first."


@task
def restart_geoserver(*args):
    """
    Restart Tomcat 7 server, which contains GeoServer.

    """

    global target
    if target:
        with fab_settings(** _build_env(target)):
            _restart_geoserver()
    else:
        print "Need to set target first."


@task
def inspect(*args):
    """
    Inspects server.

    Prints operating system major release and disk information.
    """

    global target
    if target:
        with fab_settings(** _build_env(target)):
            _inspect()
    else:
        print "Need to set target first."


@task
def add_cache(n=None, d=None, ip=None, l=None, u=None, p=None):
    """
    Adds new cache config to /etc/tilecache.cfg

    Adds new cache config to /etc/tilecache.cfg.  Publishes
    new tileservice.

    Options:
    n = name of cache
    d = human-readable description of new tile cache
    ip = ip of source back-end tile server
    l = layers parameter.  WMS parameter.
    u = user for auth for backend server
    p = password for auth for backend server
    """

    global target
    if target:
        with fab_settings(** _build_env(target)):
            _add_cache(n=n, d=d, ip=ip, l=l, u=u, p=p)
    else:
        print "Need to set target first."


@task
def upload_files(local=None, manifest=None, drop=None, tries=None, user=None, group=None, notify_level=None, topic=None, use_sudo=None):
    """
    Uploads files to drop folder on remote server.

    local: path to local files.  Supports wildcards.
    manifest: path to local manifest file that includes a local file path for each line.  Supports wildcards.
    drop: path on remote server to upload files to.
    tries: # of tries to attempt for each file.
    user: user owner of new remote file
    group: group owner of new remote file
    notify_level: notification_level.  0 = No notification.  1 = every file.  2 = one aggerate report at end of job.
    topic: AWS SNS topic to notify when complete.  Matches values in aws.py
    use_sudo: Use sudo
    """

    global target
    if target:
        with fab_settings(** _build_env(target)):
            _upload_files(target, local=local, manifest=manifest, drop=drop, tries=tries, user=user, group=group, notify_level, topic=topic, use_sudo=use_sudo)
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
            _append_to_file(data.split("\n"), "/etc/tilecache.cfg")
            _restart_apache()


def _upload_files(target, local=None, manifest=None, drop=None, tries=None, user=None, group=None, notify_level=None, topic=None, use_sudo=None):

    while (local is None)and (manifest is None):
        local = _request_input("Local File Path", local, False)
        manifest = _request_input("Manifest Path", manifest, False)
        print "Either local or manifest required.  Please try again.  Ctrl+C to cancel."
        
    drop = _request_input("Remote Drop Folder", drop, True)
    tries = _request_input("Tries for each file", tries, True)
    user = _request_input("User", user, True)
    group = _request_input("Group", group, True)
    use_sudo = _request_input("Use Sudo", use_sudo, True, options={"yes":"yes", "no":"no"}) == "yes"
    notify_level = int(_request_input("Notification Level", notify_level, True, options=["0", "1", "2"]))

    topics = None
    try:
        topics = AWS_SETTINGS['topics']
    except:
        pass
    topic = _request_input("Notify Topic", topic, False, options=topics)

    if _request_continue():
        sudo("[ -d {d} ] || ( mkdir {d} ; chown -R {u}:{g} {d} ) ".format(d=drop,u=user,g=group))
        local_files = glob(local) if local else _parse_manifest(manifest)
        md5_list = []
        for f in local_files:
            md5_list.append(_calc_md5sum(f))

        print "Local Files"
        for i in range(len(local_files)):
            print local_files[i]+": "+md5_list[i]

        count_success = 0
        count_failed = 0

        for i in range(len(local_files)):
            print "Uploading "+local_files[i]+"..."
            rf = _upload_file(local_files[i], drop, md5_list[i], int(tries), user, group, use_sudo)
            if rf:
                count_success += 1
                if notify_level==2 and topic:
                    _notify_file_uploaded(topic, local_files[i], rf, target['name'], target['host'], True)
            else:
                count_failed += 1
                print "Aborted.  Could not upload "+local_files[i]+"."
                if notify_level==2 and topic:
                    _notify_file_uploaded(topic, local_files[i], rf, target['name'], target['host'], False)

        if notify_level==1 or notify_level==2:
            _notify_file_uploads(topic, count_success, count_failed, target['name'], target['host'])

def _upload_file(local_file, drop, md5_local, tries_left, user, group, use_sudo):
    remote_files = put(local_file, drop, mode='0444', use_sudo=use_sudo)
    if len(remote_files) == 1:
        rf = remote_files[0]
        if rf in remote_files.failed:
            if tries_left == 0:
                print "Upload failed... aborting..."
                return None
            else:
                print "Upload failed... trying again.  "+str(tries_left)+" tries left."
                return _upload_file(local_file, drop, md5_local, tries_left - 1, user, group, use_sudo)
        else:
            md5_remote = md5sum(rf)
            if md5_local == md5_remote:
                print "MD5 match.  Uploaded succeeded."
                sudo('chown {u}:{g} {f}'.format(u=user, g=group, f=rf))
                return rf
            else:
                print "MD5 mismatch."
                print "Local: "+md5_local
                print "Remote: "+md5_remote
                if tries_left == 0:
                    print "Upload failed... aborting..."
                    return None
                else:
                    print "Upload failed... trying again.  "+str(tries_left)+" tries left."
                    return _upload_file(local_file, drop, md5_local, tries_left - 1, user, group, use_sudo)
