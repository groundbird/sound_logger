import os
import glob
import hashlib
import datetime
import subprocess
import numpy as np
import time
RINGO_SOUNDDIR = '/home/gb/logger/bdata/sound/'
D_THRE = -30
KAKAPO_SOUNDDIR ='/data.local/gb/logbdata/sound/'

def get_checksum(filename):
    """Generate checksum for file based on hash function (sha256).
 
    Args:
        filename (str): Path to file that will have the checksum generated.
    Returns:
        str`: Checksum based on Hash function of choice.
 
    Raises:
        Exception: Invalid hash function is entered.
 
    """
    with open(filename, "rb") as f:
        bytes = f.read()
        readable_hash = hashlib.sha256(bytes).hexdigest()
    return readable_hash

def get_oldest_daydir_local():
    oldday_dir = sorted(glob.glob(RINGO_SOUNDDIR + '/*/*/*'))[0]
    print(oldday_dir)
    dt_dir = datetime.datetime.strptime(oldday_dir[-10:] + '+0000', '%Y/%m/%d%z')
    dt_now = datetime.datetime.now(tz = datetime.timezone.utc)
    dif = dt_dir - dt_now
    if dif.days < D_THRE:
        paths = sorted(glob.glob(oldday_dir + '/*'))
        checksums = [get_checksum(ipath) for ipath in paths]
        return paths, checksums
    else:
        return

def get_checksum_remote(path):
    print('local path : ' + path)
    path_remote = KAKAPO_SOUNDDIR + '/'.join(path.split('/')[-4:])
    print('remote path : ' + path_remote)
    while True:
        with subprocess.Popen(['ssh', '-T', 'kakapo'],stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True) as p:
            output, error = p.communicate('python3 /home/gb/logger/sound_logger/check_diff_remote.py -p ' + path_remote)
            print('=========output===========')
            print(output)
            print(output == '')
            print(type(output))
        if output == '':
            time.sleep(3)
            pass
        else:
            break
    return output

def delete_file(path):
    if os.path.exists(path):
        os.system('rm ' + path)
    else:
        pass

def delete_dir(dire):
    if os.path.exists(dire):
        os.system('rm -rf ' + dire)
    else:
        pass

def main():
    paths, check_sums = get_oldest_daydir_local()
    #print(paths[:3])
    #print(check_sums[:3])
    remote_checksums = [get_checksum_remote(ipath).split('\n')[-2] for ipath in paths]
    bool_arr = np.array(remote_checksums) == np.array(check_sums)
    print(bool_arr)
    print(np.all(bool_arr))
    if np.all(bool_arr):
        print("==================== delete local dir below =================")
        dire = '/'.join(paths[0].split('/')[:-1])
        print(dire)
        delete_dir(dire)
    else:
        print("==================== delete local paths below =================")                    
        for ipath in paths[bool_arr]:
            print(ipath)
            delete_file(ipath)

    # save output
    date_str = ''.join(paths[0].split('/')[-4:-1])
    print(date_str)
    save_path = './output/' + date_str + '.log'
    with open(save_path, 'w') as f:
        wrt = '====== check sum output ===== \n'
        wrt += 'Date : '
        wrt += date_str + '\n'
        if np.all(bool_arr):
            wrt += 'All datas have same checksum. So directory of the date above is deleted. \n'
            f.write(wrt)
        else:
            wrt += 'All datas do not have same checksum. So only paths below which have same checksum are deleted. \n'
            f.write(wrt)            
            f.writelines(paths[bool_arr])
            

if __name__ == "__main__":
    main()
    #path = '/home/gb/logger/sound_logger/check_sum/hoge.log'
    #delete_file(path)
