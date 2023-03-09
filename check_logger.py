#!/usr/bin/env python3

class CheckScript():
    '''check sound logger remain or not.'''
    def __init__(self, key = 'sound'):
        import psutil, os, signal
        pidlist = []
        for proc in psutil.process_iter():
            if len(proc.cmdline())==0:
                continue
            cmdline_words = ' '.join(proc.cmdline())
            if key in cmdline_words:
                pidlist.append(str(proc.pid))
                print(pidlist)
    def check_script(self):
        print('check_script')
    def kill_script(self):
        print('kill_script')


def main():
    '''Main function'''
    check = CheckScript(key = 'sound')
    check.check_script

if __name__ == '__main__':
    main()
