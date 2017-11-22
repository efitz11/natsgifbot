import sys
import daemonocle
import discordtest

def main():
    discordtest()

if __name__ == '__main__':
    daemon = daemonocle.Daemon(
            worker=main,
            pidfile='/var/run/daemonocle_example.pid'
            )
    daemon.do_action(sys.argv[1])
