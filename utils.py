from fabric.api import env, sudo, run, cd, local, put, prefix, roles, execute, task
from fabric.api import settings as fab_settings

import hashlib

import boto

try:
    from aws import AWS_SETTINGS
except:
    print "Could not import aws.py"

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
            print question+":"
            for opt in options:
                print "Option: "+opt
            print "Selection:",
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
                    print "Must select one of the options.  Please try again.  Ctrl+C to cancel."
                    print question+":",
            return value
        else:
            value = raw_input()
            if not value:
                return value
            else:
                if value in options:
                    return value
                else:
                    print "Must select one of the options.  Please try again.  Ctrl+C to cancel."
                    print question+":",


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


def _calc_md5sum(filename):
    md5 = None
    with open (filename, "r") as f:
        md5 = hashlib.md5(f.read()).hexdigest()
    return md5


def _notify_file_uploaded(topic, lf, rf, host):
    msg = "File "+lf+" uploaded to "+rf+" on "+host+"."
    _notify_sns(topic, msg)


def _notify_error(topic, error):
    _notify_sns(topic, error)


def _notify_sns(topic, msg):
    sns = boto.connect_sns(aws_access_key_id=AWS_SETTINGS['security']['AWS_ACCESS_KEY_ID'], aws_secret_access_key=AWS_SETTINGS['security']['AWS_SECRET_ACCESS_KEY'])
    if topic in AWS_SETTINGS['topics']:
        res = sns.publish(AWS_SETTINGS['topics'][topic], msg)
