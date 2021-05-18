from mock_source import MockSource
import time
acceleration = 300.
m = MockSource(acceleration=acceleration)
data = []  # state, time, current, voltage
m.set_current(0.1)
sleep = 30/acceleration
while True:
    data.append(['charge', time.time(), *m.read_iv()])
    if data[-1][3] >= 4.2:
        break
    print(f'{data[-1]}, ', end='', flush=True)
    time.sleep(sleep)

m.set_voltage(4.2)
while True:
    data.append(['charge_cv', time.time(), *m.read_iv()])
    if data[-1][2] < 0.005:
        break
    print(f'{data[-1]}, ', end='', flush=True)
    time.sleep(sleep)

m.set_current(-0.1)
while True:
    data.append(['discharge', time.time(), *m.read_iv()])
    if data[-1][3] <= 3.0:
        break
    print(f'{data[-1]}, ', end='', flush=True)
    time.sleep(sleep)

with open('mock.csv', 'w') as f:
    f.writelines([','.join([str(x) for x in d])+'\n' for d in data])
