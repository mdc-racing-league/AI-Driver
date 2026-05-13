import socket
import sys
import getopt
import os
import time
import math

PI = 3.14159265359
data_size = 2**17

ophelp =  'Options:\n'
ophelp += ' --host, -H <host>    TORCS server host. [localhost]\n'
ophelp += ' --port, -p <port>    TORCS port. [3001]\n'
ophelp += ' --id, -i <id>        ID for server. [SCR]\n'
ophelp += ' --steps, -m <#>      Maximum simulation steps. 1 sec ~ 50 steps. [100000]\n'
ophelp += ' --episodes, -e <#>   Maximum learning episodes. [1]\n'
ophelp += ' --track, -t <track>  Your name for this track. Used for learning. [unknown]\n'
ophelp += ' --stage, -s <#>      0=warm up, 1=qualifying, 2=race, 3=unknown. [3]\n'
ophelp += ' --debug, -d          Output full telemetry.\n'
ophelp += ' --help, -h           Show this help.\n'
ophelp += ' --version, -v        Show current version.'
usage = 'Usage: %s [ophelp [optargs]] \n' % sys.argv[0]
usage = usage + ophelp
version = "20130505-2"


def clip(v, lo, hi):
    if v < lo: return lo
    elif v > hi: return hi
    else: return v


def bargraph(x, mn, mx, w, c='X'):
    if not w: return ''
    if x < mn: x = mn
    if x > mx: x = mx
    tx = mx - mn
    if tx <= 0: return 'backwards'
    upw = tx / float(w)
    if upw <= 0: return 'what?'
    negpu, pospu, negnonpu, posnonpu = 0, 0, 0, 0
    if mn < 0:
        if x < 0:
            negpu = -x + min(0, mx)
            negnonpu = -mn + x
        else:
            negnonpu = -mn + min(0, mx)
    if mx > 0:
        if x > 0:
            pospu = x - max(0, mn)
            posnonpu = mx - x
        else:
            posnonpu = mx - max(0, mn)
    nnc = int(negnonpu / upw) * '-'
    npc = int(negpu / upw) * c
    ppc = int(pospu / upw) * c
    pnc = int(posnonpu / upw) * '_'
    return '[%s]' % (nnc + npc + ppc + pnc)


class Client():
    def __init__(self, H=None, p=None, i=None, e=None, t=None, s=None, d=None, vision=False):
        self.vision = vision
        self.host = 'localhost'
        self.port = 3001
        self.sid = 'SCR'
        self.maxEpisodes = 1
        self.trackname = 'unknown'
        self.stage = 3
        self.debug = False
        self.maxSteps = 100000
        self.parse_the_command_line()
        if H: self.host = H
        if p: self.port = p
        if i: self.sid = i
        if e: self.maxEpisodes = e
        if t: self.trackname = t
        if s: self.stage = s
        if d: self.debug = d
        self.S = ServerState()
        self.R = DriverAction()
        self.setup_connection()

    def setup_connection(self):
        try:
            self.so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error as emsg:
            print('Error: Could not create socket...')
            sys.exit(-1)
        self.so.settimeout(1)
        n_fail = 5
        while True:
            a = "-45 -19 -12 -7 -4 -2.5 -1.7 -1 -.5 0 .5 1 1.7 2.5 4 7 12 19 45"
            initmsg = '%s(init %s)' % (self.sid, a)
            try:
                self.so.sendto(initmsg.encode(), (self.host, self.port))
            except socket.error as emsg:
                sys.exit(-1)
            sockdata = str()
            try:
                sockdata, addr = self.so.recvfrom(data_size)
                sockdata = sockdata.decode('utf-8')
            except socket.error as emsg:
                print("Waiting for server on %d............" % self.port)
                print("Count Down : " + str(n_fail))
                if n_fail < 0:
                    print("relaunch torcs")
                    os.system('pkill torcs')
                    time.sleep(1.0)
                    if self.vision is False:
                        os.system('torcs -nofuel -nodamage -nolaptime &')
                    else:
                        os.system('torcs -nofuel -nodamage -nolaptime -vision &')
                    time.sleep(1.0)
                    os.system('sh autostart.sh')
                    n_fail = 5
                n_fail -= 1
            identify = '***identified***'
            if identify in sockdata:
                print("Client connected on %d.............." % self.port)
                break

    def parse_the_command_line(self):
        try:
            (opts, args) = getopt.getopt(sys.argv[1:], 'H:p:i:m:e:t:s:dhv',
                                         ['host=', 'port=', 'id=', 'steps=',
                                          'episodes=', 'track=', 'stage=',
                                          'debug', 'help', 'version'])
        except getopt.error as why:
            print('getopt error: %s\n%s' % (why, usage))
            sys.exit(-1)
        try:
            for opt in opts:
                if opt[0] == '-h' or opt[0] == '--help':
                    print(usage)
                    sys.exit(0)
                if opt[0] == '-d' or opt[0] == '--debug':
                    self.debug = True
                if opt[0] == '-H' or opt[0] == '--host':
                    self.host = opt[1]
                if opt[0] == '-i' or opt[0] == '--id':
                    self.sid = opt[1]
                if opt[0] == '-t' or opt[0] == '--track':
                    self.trackname = opt[1]
                if opt[0] == '-s' or opt[0] == '--stage':
                    self.stage = int(opt[1])
                if opt[0] == '-p' or opt[0] == '--port':
                    self.port = int(opt[1])
                if opt[0] == '-e' or opt[0] == '--episodes':
                    self.maxEpisodes = int(opt[1])
                if opt[0] == '-m' or opt[0] == '--steps':
                    self.maxSteps = int(opt[1])
                if opt[0] == '-v' or opt[0] == '--version':
                    print('%s %s' % (sys.argv[0], version))
                    sys.exit(0)
        except ValueError as why:
            print('Bad parameter \'%s\' for option %s: %s\n%s' % (
                opt[1], opt[0], why, usage))
            sys.exit(-1)
        if len(args) > 0:
            print('Superflous input? %s\n%s' % (', '.join(args), usage))
            sys.exit(-1)

    def get_servers_input(self):
        if not self.so: return
        sockdata = str()
        while True:
            try:
                sockdata, addr = self.so.recvfrom(data_size)
                sockdata = sockdata.decode('utf-8')
            except socket.error as emsg:
                print('.', end=' ')
            if '***identified***' in sockdata:
                print("Client connected on %d.............." % self.port)
                continue
            elif '***shutdown***' in sockdata:
                print((("Server has stopped the race on %d. " +
                        "You were in %d place.") %
                       (self.port, self.S.d['racePos'])))
                self.shutdown()
                return
            elif '***restart***' in sockdata:
                print("Server has restarted the race on %d." % self.port)
                self.shutdown()
                return
            elif not sockdata:
                continue
            else:
                self.S.parse_server_str(sockdata)
                if self.debug:
                    sys.stderr.write("\x1b[2J\x1b[H")
                    print(self.S)
                break

    def respond_to_server(self):
        if not self.so: return
        try:
            message = repr(self.R)
            self.so.sendto(message.encode(), (self.host, self.port))
        except socket.error as emsg:
            print("Error sending to server: %s Message %s" % (emsg[1], str(emsg[0])))
            sys.exit(-1)
        if self.debug: print(self.R.fancyout())

    def shutdown(self):
        if not self.so: return
        print(("Race terminated or %d steps elapsed. Shutting down %d."
               % (self.maxSteps, self.port)))
        self.so.close()
        self.so = None


class ServerState():
    def __init__(self):
        self.servstr = str()
        self.d = dict()

    def parse_server_str(self, server_string):
        self.servstr = server_string.strip()[:-1]
        sslisted = self.servstr.strip().lstrip('(').rstrip(')').split(')(')
        for i in sslisted:
            w = i.split(' ')
            self.d[w[0]] = destringify(w[1:])

    def __repr__(self):
        return self.fancyout()

    def fancyout(self):
        out = str()
        sensors = [
            'stucktimer', 'fuel', 'distRaced', 'distFromStart',
            'opponents', 'wheelSpinVel', 'z', 'speedZ', 'speedY',
            'speedX', 'targetSpeed', 'rpm', 'skid', 'slip',
            'track', 'trackPos', 'angle',
        ]
        for k in sensors:
            if type(self.d.get(k)) is list:
                if k == 'track':
                    strout = str()
                    raw_tsens = ['%.1f' % x for x in self.d['track']]
                    strout += ' '.join(raw_tsens[:9]) + '_' + raw_tsens[9] + '_' + ' '.join(raw_tsens[10:])
                elif k == 'opponents':
                    strout = str()
                    for osensor in self.d['opponents']:
                        if osensor > 190: oc = '_'
                        elif osensor > 90: oc = '.'
                        elif osensor > 39: oc = chr(int(osensor / 2) + 97 - 19)
                        elif osensor > 13: oc = chr(int(osensor) + 65 - 13)
                        elif osensor > 3: oc = chr(int(osensor) + 48 - 3)
                        else: oc = '?'
                        strout += oc
                    strout = ' -> ' + strout[:18] + ' ' + strout[18:] + ' <-'
                else:
                    strlist = [str(i) for i in self.d[k]]
                    strout = ', '.join(strlist)
            else:
                strout = str(self.d.get(k, ''))
            out += "%s: %s\n" % (k, strout)
        return out


class DriverAction():
    def __init__(self):
        self.actionstr = str()
        self.d = {
            'accel': 0.2,
            'brake': 0,
            'clutch': 0,
            'gear': 1,
            'steer': 0,
            'focus': [-90, -45, 0, 45, 90],
            'meta': 0
        }

    def clip_to_limits(self):
        self.d['steer'] = clip(self.d['steer'], -1, 1)
        self.d['brake'] = clip(self.d['brake'], 0, 1)
        self.d['accel'] = clip(self.d['accel'], 0, 1)
        self.d['clutch'] = clip(self.d['clutch'], 0, 1)
        if self.d['gear'] not in [-1, 0, 1, 2, 3, 4, 5, 6]:
            self.d['gear'] = 0
        if self.d['meta'] not in [0, 1]:
            self.d['meta'] = 0
        if type(self.d['focus']) is not list or min(self.d['focus']) < -180 or max(self.d['focus']) > 180:
            self.d['focus'] = 0

    def __repr__(self):
        self.clip_to_limits()
        out = str()
        for k in self.d:
            out += '(' + k + ' '
            v = self.d[k]
            if not type(v) is list:
                out += '%.3f' % v
            else:
                out += ' '.join([str(x) for x in v])
            out += ')'
        return out

    def fancyout(self):
        out = str()
        od = self.d.copy()
        od.pop('gear', '')
        od.pop('meta', '')
        od.pop('focus', '')
        for k in sorted(od):
            if k in ('clutch', 'brake', 'accel'):
                strout = '%6.3f %s' % (od[k], bargraph(od[k], 0, 1, 50, k[0].upper()))
            elif k == 'steer':
                strout = '%6.3f %s' % (od[k], bargraph(od[k] * -1, -1, 1, 50, 'S'))
            else:
                strout = str(od[k])
            out += "%s: %s\n" % (k, strout)
        return out


def destringify(s):
    if not s: return s
    if type(s) is str:
        try:
            return float(s)
        except ValueError:
            print("Could not find a value in %s" % s)
            return s
    elif type(s) is list:
        if len(s) < 2:
            return destringify(s[0])
        else:
            return [destringify(i) for i in s]


#############################################
#   IMPROVED DRIVE LOGIC                    #
#############################################

# ================= USER CONFIGURABLE PARAMETERS =================
TARGET_SPEED = 100          # km/h cruising target. Reduce for more conservative driving.
MAX_SPEED = 160             # Absolute speed cap; throttle cuts above this.
STEER_GAIN = 18             # Steering gain on angle. Lower = smoother turns.
CENTERING_GAIN = 0.5        # How hard the car pulls back to track centre.
CENTERING_SPEED_SCALE = True  # Scale centering by speed (gentler at high speed).
GEAR_SPEEDS = [0, 30, 55, 85, 115, 150]  # Upshift speed thresholds (km/h) per gear 1→6.
DOWNSHIFT_MARGIN = 12       # km/h below upshift threshold before downshifting.
ENABLE_TRACTION_CONTROL = True
ENABLE_ABS = True           # Anti-lock braking: eases off if wheels lock.
BRAKE_ON_HIGH_ANGLE = True  # Apply brakes when car is badly aligned.
HIGH_ANGLE_THRESHOLD = 0.6  # Radians. Above this: brake hard.
TRACK_EDGE_THRESHOLD = 0.85 # |trackPos| above this triggers emergency steer-back.
LOOKAHEAD_SENSORS = [7, 8, 9, 10, 11]  # Centre track sensor indices (of 19) for curve detection.
CURVE_SPEED_FACTOR = 0.0015 # Throttle reduction per degree of upcoming curve tightness.


# ================= HELPER: GEAR SHIFTING =================
def compute_gear(S, current_gear):
    speed = S.get('speedX', 0)
    gear = max(1, current_gear)
    # Upshift
    if gear < 6 and speed > GEAR_SPEEDS[gear]:
        gear += 1
    # Downshift
    elif gear > 1 and speed < GEAR_SPEEDS[gear - 1] - DOWNSHIFT_MARGIN:
        gear -= 1
    return clip(gear, 1, 6)


# ================= HELPER: CURVE DETECTION =================
def curve_severity(S):
    """
    Returns a 0..1 severity value based on how much the forward track sensors
    differ from the centre sensor. High value = tight curve ahead.
    """
    track = S.get('track', [200] * 19)
    if not isinstance(track, list) or len(track) < 19:
        return 0.0
    centre = track[9]
    if centre <= 0:
        return 1.0  # Pointing off-track
    left_near = track[8]
    right_near = track[10]
    asymmetry = abs(left_near - right_near) / (centre + 1e-6)
    return clip(asymmetry, 0.0, 1.0)


# ================= HELPER: EMERGENCY RECOVERY =================
def is_off_track(S):
    return abs(S.get('trackPos', 0)) > TRACK_EDGE_THRESHOLD


def recovery_steer(S):
    """Steer hard back toward centre when off-track."""
    track_pos = S.get('trackPos', 0)
    angle = S.get('angle', 0)
    # Steer toward centre, amplified
    steer = -track_pos * 1.2 + angle * 6.0 / PI
    return clip(steer, -1, 1)


# ================= HELPER: STEERING =================
def compute_steering(S):
    angle = S.get('angle', 0)
    track_pos = S.get('trackPos', 0)
    speed = max(S.get('speedX', 1), 1)

    # Scale centering by speed: less aggressive at high speed to avoid oscillation
    if CENTERING_SPEED_SCALE:
        centering = CENTERING_GAIN * (1.0 - clip(speed / 200.0, 0, 0.6))
    else:
        centering = CENTERING_GAIN

    steer = (angle * STEER_GAIN / PI) - (track_pos * centering)
    return clip(steer, -1, 1)


# ================= HELPER: THROTTLE =================
def compute_throttle(S, steer, current_accel):
    speed = S.get('speedX', 0)

    # Reduce target speed in curves
    severity = curve_severity(S)
    dynamic_target = TARGET_SPEED * (1.0 - CURVE_SPEED_FACTOR * severity * 300)
    dynamic_target = clip(dynamic_target, 30, MAX_SPEED)

    # Absolute cap
    if speed > MAX_SPEED:
        return 0.0

    # Steer-speed coupling: slow down more when turning hard
    steer_penalty = abs(steer) * 3.0
    effective_target = dynamic_target - steer_penalty * (speed / 80.0) * 10

    if speed < effective_target:
        accel = min(1.0, current_accel + 0.3)
    else:
        accel = max(0.0, current_accel - 0.3)

    # Low-speed boost
    if speed < 10:
        accel += 1.0 / (speed + 0.1)

    return clip(accel, 0.0, 1.0)


# ================= HELPER: BRAKING =================
def compute_brake(S, steer):
    angle = S.get('angle', 0)
    speed = S.get('speedX', 0)
    wheel_spin = S.get('wheelSpinVel', [0, 0, 0, 0])

    brake = 0.0

    # Brake when badly misaligned (spinning out)
    if BRAKE_ON_HIGH_ANGLE and abs(angle) > HIGH_ANGLE_THRESHOLD:
        brake = clip((abs(angle) - HIGH_ANGLE_THRESHOLD) * 1.5, 0.1, 0.8)

    # Brake when cornering fast and drifting off edge
    off_edge = abs(S.get('trackPos', 0))
    if off_edge > 0.7 and speed > 60:
        brake = max(brake, 0.4)

    # ABS: if wheels are locking (front spin much lower than rear), ease off
    if ENABLE_ABS and isinstance(wheel_spin, list) and len(wheel_spin) == 4:
        front_avg = (wheel_spin[0] + wheel_spin[1]) / 2.0
        rear_avg = (wheel_spin[2] + wheel_spin[3]) / 2.0
        if front_avg < rear_avg * 0.6 and brake > 0:
            brake *= 0.5  # ABS pulse

    return clip(brake, 0.0, 1.0)


# ================= HELPER: TRACTION CONTROL =================
def apply_traction_control(S, accel):
    if not ENABLE_TRACTION_CONTROL:
        return accel
    wheel_spin = S.get('wheelSpinVel', [0, 0, 0, 0])
    if isinstance(wheel_spin, list) and len(wheel_spin) == 4:
        rear_spin = wheel_spin[2] + wheel_spin[3]
        front_spin = wheel_spin[0] + wheel_spin[1]
        if rear_spin - front_spin > 5.0:
            accel -= 0.2
        elif rear_spin - front_spin > 2.0:
            accel -= 0.1
    return clip(accel, 0.0, 1.0)


# ================= MAIN DRIVE FUNCTION =================
def drive(c):
    S, R = c.S.d, c.R.d

    # Emergency off-track recovery overrides everything
    if is_off_track(S):
        R['steer'] = recovery_steer(S)
        R['accel'] = 0.4
        R['brake'] = 0.0
        R['gear'] = compute_gear(S, R.get('gear', 1))
        return

    # Normal driving
    steer = compute_steering(S)
    R['steer'] = steer

    accel = compute_throttle(S, steer, R.get('accel', 0.2))
    accel = apply_traction_control(S, accel)
    R['accel'] = accel

    R['brake'] = compute_brake(S, steer)

    # Don't accelerate and brake at the same time
    if R['brake'] > 0.1:
        R['accel'] = max(0.0, R['accel'] - R['brake'])

    R['gear'] = compute_gear(S, R.get('gear', 1))


# ================= MAIN LOOP =================
if __name__ == "__main__":
    C = Client(p=3001)
    for step in range(C.maxSteps, 0, -1):
        C.get_servers_input()
        drive(C)
        C.respond_to_server()
    C.shutdown()
