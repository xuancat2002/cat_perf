import os,sys,subprocess,argparse
import pandas as pd
import plotly.graph_objects as go

def write_perf_file(seconds,script_file,result_file):
    interval=2
    content="""
killall mpstat sar

COUNT={COUNT}
INTERVAL={INTERVAL}

nohup mpstat -P ALL $INTERVAL $COUNT > cpu.log 2>/dev/null &
nohup sar -n DEV $INTERVAL $COUNT > net.log 2>/dev/null &
nohup sar -d $INTERVAL $COUNT > dsk.log 2>/dev/null &
nohup free -s $INTERVAL -c $COUNT > mem.log 2>/dev/null &

sleep $(($COUNT*2+5))
cat cpu.log|grep -v Average|grep all|awk '{{print $NF}}' > cpu.txt
cat net.log|grep -v Average|grep -v lo|grep -v ap0|grep -v IFACE|grep -v "^$"|awk '(NR>1)'|awk '{{print $NF}}' > net.txt
cat dsk.log|grep -v Average|grep -v DEV|grep -v "^$"|awk '(NR>1)'|awk '{{print $NF}}' > dsk.txt
cat mem.log|grep Mem|awk '{{print $2}}' > mem_total.txt
cat mem.log|grep Mem|awk '{{print $3}}' > mem_used.txt

paste cpu.txt net.txt dsk.txt mem_total.txt mem_used.txt > {RESULT}
    """.format(COUNT=int(seconds/interval),INTERVAL=interval,RESULT=result_file)
    with open(script_file, 'w') as f:
        f.write(content)

# cmd execution
def exec_cmd(cmd):
    p=subprocess.run([cmd], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out=p.stdout.decode("utf-8").strip()
    return out

# send sh file to remote server
def send_file_remote(user, ip, file):
    cmd = "scp {} {}@{}:/home/{}".format(file, user, ip, user)
    # cmd="scp /Users/xuan/cat_perf/cat_perf0.sh pi@192.168.1.115:/home/pi"
    exec_cmd(cmd)
    print(cmd)

# run perf test
def do_ssh_perf(user, ip, file):
    cmd="ssh {}@{} 'cd /home/{}; ./{}'".format(user, ip, user, file)
    print(cmd)
    exec_cmd(cmd)

# get perf result file from pi
def result_file_copy(user, ip, result_file):
    cmd='scp {}@{}:/home/{}/{} .'.format(user, ip, user, result_file)
    print(cmd)
    exec_cmd(cmd)

# draw perf graph
def figure(result_file):
    # load in txt data
    data = pd.read_csv('{}'.format(result_file), sep="\t", header=None)
    data.columns = ["cpu", "net", "dsk", "mem_t", "mem_u"]
    #print(data)
    # add a column as memory
    data.insert(5, 'mem', value=100 * data['mem_u'] / data['mem_t'])
    #data.insert(0, 'index', range(1, 1 + len(data)))
    print(data)

    # figures
    line1 = go.Scatter(y=data['cpu'], name='CPU')
    line2 = go.Scatter(y=data['net'], name='NET')
    line3 = go.Scatter(y=data['dsk'], name='DSK')
    line4 = go.Scatter(y=data['mem'], name='MEM')
    fig = go.Figure([line1, line2, line3, line4])
    fig.update_layout(
        title="Performance Output",
        xaxis_title="Index",
        yaxis_title="Performance Trends"
    )
    #fig.update_xaxes(ticklabelstep=2)
    fig.show()

# entry
def main():
    user = 'pi'
    ip = '192.168.1.115'
    file = 'cat_perf00.sh'
    result_file = 'output_perf.txt'
    write_perf_file(20, file, result_file)
    send_file_remote(user, ip, file)
    do_ssh_perf(user, ip, file)
    result_file_copy(user, ip, result_file)
    figure(result_file)

main()
