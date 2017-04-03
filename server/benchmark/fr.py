"""
To manage the fakerequesters for the benchmark.

Fake Requester instances need to be started in a different computer, and on-demand. So they need to be
managed using paramiko or fabric or similar.

The remote computer needs to have everything ready:
The fakerequester in a path, and node ready to use.
"""

from fabric.api import env, run, execute, hosts, cd


def start_remote_fakerequester(host, keyfile, path, clients):
    """
    Starts the fakerequester script remotely.
    :param host:
    :param keyfile:
    :param path:
    :param clients:
    :return:
    """
    env.key_filename = keyfile
    execute(run_remote_commands, path, clients, hosts=[host])


def run_remote_commands(path, clients):
    with cd(path):
        run("node run.js -w {}".format(clients))

def run_test_command():
    result = run("ls -l /var/www")
    print("RESULT: {}".format(result))

# This is just for testing and development. This script is meant to be called
# automatically from the benchmark.
if __name__ == "__main__":
    start_remote_fakerequester("weblab@plunder.weblab.deusto.es:5800", "/Users/lrg/.ssh/id_rsa", "/home/lrg/", 2)