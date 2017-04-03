"""
To manage the fakerequesters for the benchmark.

Fake Requester instances need to be started in a different computer, and on-demand. So they need to be
managed using paramiko or fabric or similar.
"""

from fabric.api import env,run,execute,hosts

def start_remote_fakerequester(host, keyfile):
    env.key_filename = keyfile
    execute(run_remote_commands, hosts=[host])

def run_remote_commands():
    result = run("ls -l /var/www")
    print("RESULT: {}".format(result))
