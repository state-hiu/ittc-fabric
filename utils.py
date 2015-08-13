from fabric.api import env, sudo, run, cd, local, put, prefix, roles, execute, task
from fabric.api import settings as fab_settings

import hashlib
import boto
import datetime
from glob import glob

try:
    from aws import AWS_SETTINGS
except:
    print "Error: Could not import local aws module (aws.py)."


def _parse_manifest(manifest):
    paths = []
    lines = []
    with open (filename, "r") as f:
        lines = f.readlines
    for line in lines:
        paths.extend(glob(line))
    return paths

def getTopic(alias):
    t = None
    try:
        t = AWS_SETTINGS['topics'][alias]
    except:
        pass
    return t

def _build_env(target):
    e = {
        'user': target['user'],
        'hosts': [target['host']],
        'host_string': target['host'],
        'key_filename': target['ident']
    }
    return e


def _print_target(target):
    print "Connecting to server ..."
    print "Name: "+target['name']
    print "User: "+target['user']
    print "Host: "+target['host']
    print "-------"
    print "ssh "+target['user']+'@'+target['host']+' -i '+target['ident']
    print "#######################"
    print ""

def _cron_command(f, u, c, filename):
    template = 'echo "{f} {u} {c}" > /etc/cron.d/{filename}'
    cmd = template.format(f=f, u=u, c=c, filename=filename)
    return cmd


def _load_template(filename):
    data = None
    with open ('templates/'+filename, "r") as f:
        data = f.read()
    return data


def _request_input(question, value, required, options=None):
    if value:
        return value
    else:

        if options:
            print question+" :"
            print "* Options Below."+("  Enter to skip." if not required else "")
            for opt in options:
                print "| -- "+opt
            print "* Select option:",
        else:
            print question+":",


        if required:
            value = None
            while not value:
                value = raw_input()
                if not value:
                    print "Value required.  Please try again.  Ctrl+C to cancel."
                    print question+":",
                elif options and (not value in options):
                    print "Must select one of the options.  Ctrl+C to cancel."
                    print question+":",
                    value = None
            return value

        else:
            while not value:
                value = raw_input()
                if not value:
                    return None
                elif options and (not value in options):
                    print "Must select one of the options.  Enter to skip.  Ctrl+C to cancel."
                    print question+":",
                    value = None
            return value


def _request_continue():
    print "Continue (y/n)?",
    confirm = raw_input()
    return confirm and confirm.lower() == "y"


def _append_to_file(lines, filename):
    print "Appending to file..."
    print ""
    sudo("echo '' >> {f}".format(f=filename))
    for line in lines:
        t = "echo '{line}' >> {f}"
        c = t.format(line=line.replace('"','\"'), f=filename)
        sudo(c)


def _calc_md5sum(filename, block_size=128**4):
    md5 = hashlib.md5()
    with open (filename, "r") as f:
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


def _notify_file_uploads(topic, count_success, count_failed, target, host):
    msg = None
    now = datetime.datetime.now()
    t = _load_template("templates/notification_file_uploads.txt")
    if t:
        msg = t.replace("{{target}}", target)
        msg = t.replace("{{host}}", host)
        msg = t.replace("{{count_success}}", str(count_success))
        msg = t.replace("{{count_failed}}", str(count_failed))
        msg = t.replace("{{now}}", now.isoformat())
    else:
        msg = "Files uploaded to "+host+".\nTime: "+now.isoformat()+"\nSuccess: "+str(count_success)+"\nFailed: "+str(count_failed)
    _notify_sns(topic, msg)


def _notify_file_uploaded(topic, lf, rf, target, host, success):
    msg = None
    now = datetime.datetime.now()
    if success:
        t = _load_template("templates/notification_file_uploaded_success.txt")
        if t:
            msg = t.replace("{{target}}", target)
            msg = t.replace("{{host}}", host)
            msg = t.replace("{{lf}}", lf)
            msg = t.replace("{{rf}}", rf)
            msg = t.replace("{{now}}", now.isoformat())
        else:
            msg = "Success: File "+lf+" uploaded to "+rf+" on "+host+".\nTime: "+now.isoformat()
    else:
        msg = "Failed: Could not upload file "+lf+" to "+rf+" on "+host+".\nTime: "+now.isoformat()
    _notify_sns(topic, msg)


def _notify_error(topic, error):
    _notify_sns(topic, error)


def _notify_sns(topic, msg):
    sns = boto.connect_sns(aws_access_key_id=AWS_SETTINGS['security']['AWS_ACCESS_KEY_ID'], aws_secret_access_key=AWS_SETTINGS['security']['AWS_SECRET_ACCESS_KEY'])
    if topic in AWS_SETTINGS['topics']:
        print "Sending notification to {t} ...".format(t=getTopic(topic))
        res = sns.publish(getTopic(topic), msg)
