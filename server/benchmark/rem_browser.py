"""
To manage the browser-based fake requester for the benchmark.

Fake Requester instances need to be started in a different computer, and on-demand. So they need to be
managed using paramiko or fabric or similar.

The remote computer needs to have everything ready:
The fakerequester in a path, and node ready to use.
"""
import time
import traceback
from fabric.api import env, run, execute, cd
from fabric.network import ssh

ssh.util.log_to_file("paramiko_rb.log", 10)


def start_remote_browser(host, keyfile, path, clients, cam_url, format):
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
    execute(run_remote_commands, path, clients, cam_url, format, hosts=[host])


def check_remote_browser(host, keyfile, path, clients):
    env.key_filename = keyfile
    # env.gateway = "lrg@plunder.weblab.deusto.es:5800"
    return execute(check_remote_commands, path, hosts=[host])


def stop_remote_browser(host, keyfile):
    env.key_filename = keyfile
    # env.gateway = "lrg@plunder.weblab.deusto.es:5800"
    execute(stop_remote_commands, hosts=[host])


def run_remote_commands(path, clients, cam_url, format):
    with cd(path):
        run(
            "pwd && (nohup python browser.py -u {} -t 30 -c testresults.log -p {},{}, > nohup.out 2>&1 &)".format(
                cam_url, clients, format), pty=False)
        # run("bash")


def check_remote_commands(path):
    with cd(path):
        return True


def stop_remote_commands():
    run("killall python")


def run_test_command(path, clients):
    result = run("pwd")
    print("RESULT: {}".format(result))


# This is just for testing and development. This script is meant to be called
# automatically from the benchmark.
if __name__ == "__main__":
    start_remote_browser("lrg@plunder.weblab.deusto.es:5800", "~/.ssh/id_rsa", "/home/lrg/wilsa/wilsaproxy/server/benchmark", 2,
                               "http://192.168.0.7/exps/imgrefresh/cam0_0", "img")
    time.sleep(30)
    stop_remote_browser("lrg@plunder.weblab.deusto.es:5800", "~/.ssh/id_rsa")
