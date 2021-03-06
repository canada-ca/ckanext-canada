import sys
import subprocess
import requests
import time

'''
Usage: python pd_ati_monitor.py usr1@reg_host usr2@portal_host slack_url
'''


def send_slack(text, url):
    payload = {"text":text}
    count = 5
    while count >0:
        count -= 1
        try:
            r = requests.post(url, json=payload)
            if r.status_code == 200:
                break
        except (requests.exceptions.ProxyError,
                requests.exceptions.ReadTimeout):
            print('slack exception')
            pass
        time.sleep(5)


def get_csv_upload(usr):
    cmd = 'ssh ' + usr + ' stat -c %Y /home/odatsrv/run_log/upload_ati_csv_from_datastore_tables.log'
    cmd = cmd.split(' ')
    result = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
    now = time.time()
    if now - int(result) > 3600 * 12:
        return -1

    cmd = 'ssh ' + usr + ' grep download /home/odatsrv/run_log/upload_ati_csv_from_datastore_tables.log | wc'
    cmd = cmd.split(' ')
    result = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
    return int(result.split()[0])


def get_pd_update(usr):
    cmd = 'ssh '+ usr +' stat -c %Y /home/odatsrv/run_log/rebuild_pd_solr_from_uploaded_csv.log'
    cmd = cmd.split(' ')
    result = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
    now = time.time()
    if now - int(result) > 3600 * 12:
        return -1

    cmd = 'ssh ' + usr + ' grep Cleared /home/odatsrv/run_log/rebuild_pd_solr_from_uploaded_csv.log | wc'
    cmd = cmd.split(' ')
    # Python3
    #result = subprocess.run(cmd, stdout=subprocess.PIPE)
    #result.stdout.decode('utf-8')
    result = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
    return int(result.split()[0])


def main():
    usr_reg = sys.argv[1]
    usr_portal = sys.argv[2]
    slack_url = sys.argv[3]
    def reason(code, total):
        if code==total:
            return 'ok'
        return ('file not updated.' if code==-1 else
                '{0} transfered but {1} expected.'.format(code, total))
    ret_code1 = get_csv_upload(usr_reg)
    ret_code2 = get_pd_update(usr_portal)

    text = ' '.join(['csv', reason(ret_code1, 15),
                     'solr', reason(ret_code2, 9)])

    send_slack(text, slack_url)

if __name__=='__main__':
    main()
