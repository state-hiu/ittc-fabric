from fabric.api import env, sudo, run, cd, local, put, prefix, roles, execute, task
from fabric.api import settings as fab_settings

import hashlib

def _build_env(target):
    e = {
        'user': target['user'],
        'hosts': [target['host']],
        'host_string': target['host'],
        'key_filename': target['ident']
    }
    return e


def _print_target(target):
    print "Connecting to server..."
    print "User: "+target['user']
    print "Host: "+target['host']
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


def _request_input(question, value, required):
    if value:
        return value
    else:
        print question+":",
        if required:
            value = None
            while not value:
                value = raw_input()
                if not value:
                    print "Value required.  Please try again.  Ctrl+C to cancel."
                    print question+":",
            return value
        else:
            return raw_input()


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
    return hashlib.md5(open(filename).read()).hexdigest()
