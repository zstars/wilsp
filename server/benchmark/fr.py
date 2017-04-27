"""
To manage the fakerequesters for the benchmark.

Fake Requester instances need to be started in a different computer, and on-demand. So they need to be
managed using paramiko or fabric or similar.

The remote computer needs to have everything ready:
The fakerequester in a path, and node ready to use.
"""
import time
import traceback
from fabric.api import env, run, execute, cd
from fabric.network import ssh

ssh.util.log_to_file("paramiko.log", 10)


def start_remote_fakerequester(host, keyfile, path, clients, cam_url, formatopt):
    """
    Starts the fakerequester script remotely.
    :param host:
    :param keyfile:
    :param path:
    :param clients:
    :param cam_url:
    :return:
    """
    env.key_filename = keyfile
    # env.gateway = "lrg@plunder.weblab.deusto.es:5800"
    execute(run_remote_commands, path, clients, cam_url, formatopt, hosts=[host])


def check_remote_fakerequester(host, keyfile, path, clients):
    env.key_filename = keyfile
    # env.gateway = "lrg@plunder.weblab.deusto.es:5800"
    return execute(check_remote_commands, path, hosts=[host])


def stop_remote_fakerequester(host, keyfile):
    env.key_filename = keyfile
    # env.gateway = "lrg@plunder.weblab.deusto.es:5800"
    execute(stop_remote_commands, hosts=[host])


def run_remote_commands(path, clients, cam_url, formatopt):
    with cd(path):
        run(
            "pwd && source ~/.bashrc && source ~/.nvm/nvm.sh && (nohup node run.js -w {} -u {} -t {} > nohup.out 2>&1 &)".format(
                clients, cam_url, formatopt), pty=False)
        # run("bash")


def check_remote_commands(path):
    with cd(path):
        return True


def stop_remote_commands():
    run("killall node")


def run_test_command(path, clients):
    result = run("pwd")
    print("RESULT: {}".format(result))


# This is just for testing and development. This script is meant to be called
# automatically from the benchmark.
if __name__ == "__main__":
    start_remote_fakerequester("lrg@newplunder", "~/.ssh/id_rsa", "/home/lrg/wilsa/wilsaproxy/fakerequester", 2,
                               "http://newscabb/cams/cam0_0", "img")
    time.sleep(30)
    stop_remote_fakerequester("lrg@newplunder", "~/.ssh/id_rsa")
