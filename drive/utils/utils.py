import subprocess, os, sys


class Utils:

    @staticmethod
    def invoke_command(command, folder=os.getcwd(), shell=True, env=os.environ):
        proc = subprocess.Popen(command, cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell, env=env)
        out, err = proc.communicate()
        ret_code = proc.wait()
        return ret_code, out.decode(sys.getdefaultencoding()), err.decode(sys.getdefaultencoding())