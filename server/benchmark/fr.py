"""
To manage the fakerequesters for the benchmark.

Fake Requester instances need to be started in a different computer, and on-demand. So they need to be
managed using paramiko or fabric or similar.
"""

from fabric.api import env, run, execute, hosts


def start_remote_fakerequester(host, keyfile):
    env.key_filename = keyfile
    execute(run_remote_commands, hosts=[host])


def run_remote_commands():
    result = run("ls -l /var/www")
    print("RESULT: {}".format(result))


# This is just for testing and development. This script is meant to be called
# automatically from the benchmark.
if __name__ == "__main__":
    start_remote_fakerequester("weblab@plunder.weblab.deusto.es:5800", "/Users/lrg/.ssh/id_rsa")