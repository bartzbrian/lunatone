from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
from PIL import ImageFont, Image
import os
import serial
import serial.tools.list_ports
import RPi.GPIO as GPIO
import startup_animation
import midi_subprocess
from threading import Thread

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
chans = [17,27,22,23,24,25,5,6,16]
GPIO.setup(chans, GPIO.OUT)

os.system('sudo systemctl stop serial-getty@ttyAMA0.service')
os.system('sudo systemctl disable serial-getty@ttyAMA0.service')


ports = list(serial.tools.list_ports.comports())
for p in ports:
    address = p[0]

#static global vars
arduino = serial.Serial(address, 115200)
display = i2c(port=1, address=0x3C)
device = sh1106(display)

global_menus = ['oscillators','mix/LPF','envelopes','modulation','effects']
menu_mappings = [{0:'osc1_pitch',1:'osc1_waveform',2:'osc1_PWM_amt',3:'osc1_FM_amt',4:'osc2_pitch',5:'osc2_waveform',6:'osc2_PWM_amt',7:'osc2_FM_amt'},
                 {0:'osc1_amt',1:'osc2_amt',2:'noise_amt',3:'post_mix_gain',4:'filter_cutoff',5:'filter_Q',6:'cutoff_FM',7:'post_filter_gain'},
                 {0:'AMP_EG_Attack',1:'AMP_EG_Decay',2:'AMP_EG_Sustain',3:'AMP_EG_Release',4:'EG2_Attack',5:'EG2_Decay',6:'EG2_Sustain',7:'EG2_Release'},
                 {0:'LFO_freq',1:'LFO_waveform',2:'LFO_depth',3:'cutoff_mod_src',4:'osc1_PWM_src',5:'osc1_FM_src',6:'osc2_PWM_src',7:'osc2_FM_src'},
                 {0:'delay_rate_left',1:'delay_rate_right',2:'feedback_amt',3:'delay_wet_dry',4:'reverb_amt',5:'reverb_wet_dry',6:'FX_lowpass',7:'post_FX_gain'}]


#draws text to screen
def draw_text(text):
    with canvas(device) as draw:
        fnt = (ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMono.ttf', 15))
        w, h = draw.textsize(text, font=fnt)
        draw.text(((128-w)/2, 20), text, font=fnt, fill="white")

def draw_sel(text):
    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="white", fill="black")
        fnt = (ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMono.ttf', 15))
        w, h = draw.textsize(text, font=fnt)
        draw.text(((128-w)/2, 20), text, font=fnt, fill="white")
        
def fwd_to_PD(msg):
    os.system("echo '" + msg + ";" + "' | pdsend 5000")

#takes in the serial data from the arduino
def check_arduino():
    vals = []
    while len(vals) != 10:
        va = arduino.readline()
        vals = [x for x in va.split(',')]
    return vals 

def scaleVal(val,id):
    if id == 0:
        if val > 860:
            ret = ((val - 1023) * (80)) / (860 - 1023)
        elif val <= 860:
            ret = ((val - 860) * (127-80)) / (-860) + 80
        if ret < 7:
            return str(0)
        else:
            return str(ret)
    elif id == 2:
        if val > 860:
            ret = ((val - 1023) * (100-63)) / (860 - 1023)+63
        elif val <= 860:
            ret = ((val - 860) * (127-100)) / (-860)+100
        if ret < 67:
            return str(63)
        else:
            return str(ret)
    else:
        if val > 950:
            return str(0)
        elif val > 850 and val <= 950:
            return str(1)
        elif val > 400  and val <= 850:
            return str(2)
        elif val <= 400:
            return str(3)
    
def LED(menunum):
    GPIO.output(chans,0)
    if menunum == 0:
        GPIO.output([17,27,23,25,16],1)
    elif menunum == 1:
        GPIO.output([27,22,24,25,6,16],1)
    elif menunum == 2:
        GPIO.output([17,22,25,5,6],1)
    elif menunum == 3:
        GPIO.output([22,24,5,16],1)
    elif menunum == 4:
        GPIO.output([17,23,24,5,],1)

def main():
    
    startup_animation.main()
    
    prev_arduino = check_arduino()
    current_menu = 0
    selected_menu = 0
    selected = 0
    display= ''
    lastmsg=''
    LED(0)
    draw_text(global_menus[current_menu])
    Thread(target=midi_subprocess.check_midi).start()
    
    while True:        
        
        arduino = check_arduino()
        
        if arduino[9].strip().isdigit():
            if int(arduino[9]) == 2 and selected == 0:
                current_menu += 1
                if current_menu == 5:
                    current_menu = 0
                LED(current_menu)
                draw_text(global_menus[current_menu])
                display = global_menus[current_menu]

            if int(arduino[9]) == 1 and selected == 0:
                current_menu -= 1
                if current_menu == -1:
                    current_menu = 4
                LED(current_menu)    
                draw_text(global_menus[current_menu])
                display = global_menus[current_menu]
        
        if arduino[8].strip().isdigit():
            #if button press, select current menu
            if int(arduino[8]) == 1:
                if selected == 1:
                    selected = 0
                    draw_text(global_menus[current_menu])
                    display = global_menus[current_menu]
                elif selected == 0:
                    selected = 1
                    selected_menu = current_menu
                    draw_sel(global_menus[current_menu])
                    display = global_menus[current_menu]
        
        for x in xrange(0,8):
            if prev_arduino[x].strip().isdigit() and arduino[x].strip().isdigit():
                #if a knob is being turned
                if abs(int(prev_arduino[x])- int(arduino[x])) > 5:
                    if menu_mappings[selected_menu][x] == 'osc1_waveform' or menu_mappings[selected_menu][x] == 'osc2_waveform':
                        pkt = scaleVal(int(arduino[x]),1)
                    elif menu_mappings[selected_menu][x] == 'cutoff_FM':
                        pkt = scaleVal(int(arduino[x]),2)                    
                    else:
                        pkt = scaleVal(int(arduino[x]),0)                   
                    if selected == 1:   
                        msg = menu_mappings[selected_menu][x] + ' ' + pkt
                        if msg != lastmsg:
                            fwd_to_PD(msg)
                            lastmsg = msg
        
        prev_arduino = arduino
        
if __name__ == '__main__':
    main()   
        
    
