import customtkinter as ctk
import paho.mqtt.client as mqtt_client
from PIL import Image, ImageTk
from threading import Thread
from xml.etree import ElementTree
from playsound import playsound
from os import path, system
from time import sleep, localtime, strftime, time


class StateImage:
    def __init__(self):
        self.white = ctk.CTkImage(Image.open('img/white-circle.png'), size=(15, 15))
        self.orange = ctk.CTkImage(Image.open('img/orange-circle.png'), size=(15, 15))
        self.green = ctk.CTkImage(Image.open('img/green-circle.png'), size=(15, 15))
        self.red = ctk.CTkImage(Image.open('img/red-circle.png'), size=(15, 15))


class Action:
    def __init__(self):
        self.description = 'Aus'
        self.run = None
        self.file = None
        self.param = None
        self.time = time() + 2

    def run_action(self):
        if time() - self.time < 1:
            print_log('Ungewollte Aktion verhindert')
            return
        self.time = time()
        if self.run == 'sound':
            Thread(target=self.play_sound).start()
            print_log('Sound abgespielt: ' + self.description)
        elif self.run == 'bash':
            Thread(target=self.run_bash).start()
            print_log('Bash ausgeführt: ' + self.description)
        else:
            f_error('unknown_command', self.run)

    def play_sound(self):
        if path.isfile(self.file):
            playsound(self.file)
        else:
            f_error('file', self.file)

    def run_bash(self):
        if path.isfile(self.file):
            if self.param != 'none':
                prompt = 'bash -c \'' + self.file + ' ' + self.param + '\''
            else:
                prompt = 'bash -c \'' + self.file + '\''
            system(prompt)
        else:
            f_error('file', self.file)


class DeviceFloatFrame(ctk.CTkFrame):
    def __init__(self, master, device_name, adress, rounds, unit):
        super().__init__(master)

        self.grid_columnconfigure(2, weight=1)

        self.objekt = 'float'
        self.adress = adress
        self.rounds = rounds
        self.unit = unit
        self.float_device = ctk.CTkLabel(self, text='-')
        self.float_device.grid(column=0, row=0, padx=10)
        self.label_device = ctk.CTkLabel(self, text=device_name)
        self.label_device.grid(column=1, row=0, padx=5)

    def set_device_state(self, state):
        state = round(float(state), self.rounds)
        if self.rounds == 0:
            state = str(format(state, 'g')) + self.unit
        else:
            state = str(state) + self.unit
        self.float_device.configure(text=state)


class DeviceBoolFrame(ctk.CTkFrame):
    def __init__(self, master, device_name, adress, actions, default_false, default_true, color_false, color_true):
        super().__init__(master)

        self.grid_columnconfigure(2, weight=1)

        self.objekt = 'bool'
        self.adress = adress
        self.last_state = 'none'

        if color_false == 'white':
            self.color_false = state_image.white
        elif color_false == 'orange':
            self.color_false = state_image.orange
        elif color_false == 'green':
            self.color_false = state_image.green
        elif color_false == 'red':
            self.color_false = state_image.red
        else:
            self.color_false = state_image.green

        if color_true == 'white':
            self.color_true = state_image.white
        elif color_true == 'orange':
            self.color_true = state_image.orange
        elif color_true == 'green':
            self.color_true = state_image.green
        elif color_true == 'red':
            self.color_true = state_image.red
        else:
            self.color_true = state_image.red

        self.img_device = ctk.CTkLabel(self, text='', image=state_image.orange)
        self.img_device.grid(column=0, row=0, padx=10)
        self.label_device = ctk.CTkLabel(self, text=device_name)
        self.label_device.grid(column=1, row=0, padx=5)
        self.combo_watch_false = ctk.CTkComboBox(self, values=actions, width=200, state='readonly')
        self.combo_watch_false.grid(column=2, row=0, padx=15, sticky='e')
        self.combo_watch_false.set(default_false)
        self.combo_watch_true = ctk.CTkComboBox(self, values=actions, width=200, state='readonly')
        self.combo_watch_true.grid(column=3, row=0, padx=15, pady=5, sticky='e')
        self.combo_watch_true.set(default_true)

    def set_device_state(self, state):
        if state:
            self.img_device.configure(image=self.color_true)
        else:
            self.img_device.configure(image=self.color_false)


class HeaderFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.signal_active = False
        self.configure(fg_color='transparent')
        self.grid_columnconfigure(2, weight=1)

        self.img_network = ctk.CTkLabel(self, text='', image=state_image.white)
        self.img_network.grid(column=0, row=0, padx=10)
        self.label_device = ctk.CTkLabel(self, text='Geräte', font=('Arial', 13))
        self.label_device.grid(column=1, row=0, padx=5)
        self.label_a_false = ctk.CTkLabel(self, text='Aktion unwahr', font=('Arial', 13), width=200)
        self.label_a_false.grid(column=2, row=0, padx=15, sticky='e')
        self.label_a_true = ctk.CTkLabel(self, text='Aktion wahr', font=('Arial', 13), width=200)
        self.label_a_true.grid(column=3, row=0, padx=15, pady=5, sticky='e')


class Window(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title('ioBroker GUI')
        self.win_icon('img/iobroker.png')
        self.minsize(width=600, height=250)
        self.grid_columnconfigure(0, weight=1)

        self.header = HeaderFrame(self)
        self.header.grid(column=0, row=0, padx=5, pady=5, sticky='we')

        xml_file = ElementTree.parse('config.xml')
        self.appearance = xml_file.findall('setting')[0].find('appearance').text
        self.mqtt = Mqtt()
        self.mqtt.server_host = xml_file.findall('setting')[0].find('server_host').text
        self.mqtt.server_port = int(xml_file.findall('setting')[0].find('server_port').text)
        self.mqtt.client_id = xml_file.findall('setting')[0].find('client_id').text
        self.mqtt.client_user = xml_file.findall('setting')[0].find('client_user').text
        self.mqtt.client_pw = xml_file.findall('setting')[0].find('client_pw').text
        self.mqtt.topics = []

        self.actions = [Action()]
        self.action_list = [self.actions[0].description]
        for element in xml_file.findall('action'):
            self.actions.append(Action())
            index = len(self.actions) - 1
            if path.isfile(element.find('file').text):
                self.actions[index].description = element.find('description').text
            else:
                self.actions[index].description = element.find('description').text + ' *err'
                f_error('file', element.find('file').text)
            self.actions[index].run = element.find('run').text
            self.actions[index].file = element.find('file').text
            self.actions[index].param = element.find('parameters').text
            self.action_list.append(self.actions[index].description)
        print_log(str(len(self.actions)) + ' Aktionen definiert')

        hidden_count = 0
        grid_row_count = 0
        self.devices = []
        for element in xml_file.findall('device'):
            if element.find('type').text == 'separator':
                grid_row_count += 1
                ctk.CTkLabel(self, text='', height=0).grid(column=0, row=grid_row_count)
            elif element.find('type').text == 'bool' or element.find('type').text == 'hidden':
                self.mqtt.topics.append((element.find('adress').text, 1))
                self.devices.append(DeviceBoolFrame(self,
                                                    element.find('description').text,
                                                    element.find('adress').text,
                                                    self.action_list,
                                                    element.find('default_false').text,
                                                    element.find('default_true').text,
                                                    element.find('color_false').text,
                                                    element.find('color_true').text))
                if element.find('type').text == 'hidden':
                    hidden_count += 1
                else:
                    grid_row_count += 1
                    self.devices[len(self.devices) - 1].grid(column=0, row=grid_row_count, padx=5, pady=3, sticky='we')
            elif element.find('type').text == 'float':
                self.mqtt.topics.append((element.find('adress').text, 1))
                self.devices.append(DeviceFloatFrame(self,
                                                     element.find('description').text,
                                                     element.find('adress').text,
                                                     int(element.find('round').text),
                                                     element.find('unit').text))
                grid_row_count += 1
                self.devices[len(self.devices) - 1].grid(column=0, row=grid_row_count, padx=5, pady=3, sticky='we')

        print_log(str(len(self.devices)) + ' Geräte definiert (' + str(hidden_count) + ' davon versteckt)')
        self.label_version = ctk.CTkLabel(self, text=self.mqtt.client_id + ' | ' + version, font=('Arial', 13))
        self.label_version.grid(column=0, row=grid_row_count + 1, padx=15, pady=5, sticky='e')

    def win_icon(self, file_name):
        tk_icon = ImageTk.PhotoImage(Image.open(file_name))
        self.call('wm', 'iconphoto', self, tk_icon)

    def change_state_by_adress(self, adress, state):
        index = self.get_device_index(adress)
        if index == -1:
            f_error('unknown_device', adress)
        else:
            if self.devices[index].objekt == 'bool':
                if self.devices[index].last_state != state:
                    self.devices[index].last_state = state
                    if state == 'true':
                        self.devices[index].set_device_state(True)
                        if self.devices[index].combo_watch_true.get() != 'Aus':
                            action_index = self.get_action_index(self.devices[index].combo_watch_true.get())
                            if action_index != -1:
                                self.actions[action_index].run_action()
                    else:
                        self.devices[index].set_device_state(False)
                        if self.devices[index].combo_watch_false.get() != 'Aus':
                            action_index = self.get_action_index(self.devices[index].combo_watch_false.get())
                            if action_index != -1:
                                self.actions[action_index].run_action()
            elif self.devices[index].objekt == 'float':
                self.devices[index].set_device_state(state)

    def get_device_index(self, adress):
        index = 0
        for device in self.devices:
            if device.adress == adress:
                return index
            index += 1
        return -1

    def get_action_index(self, description):
        index = 0
        for action in self.actions:
            if action.description == description:
                return index
            index += 1
        return -1

    def signal_network_error(self):
        self.header.img_network.configure(image=state_image.red)
        # wenn Rücksetzung (signal_off) noch aktiv ist, wird auch das rote Signal zurückgesetzt ...

    def signal_input_data(self, image):
        if not self.header.signal_active:
            self.header.signal_active = True
            self.header.img_network.configure(image=image)
            Thread(target=self.signal_off).start()

    def signal_off(self):
        sleep(1.5)
        self.header.img_network.configure(image=state_image.white)
        self.header.signal_active = False


class Mqtt:
    def __init__(self):
        self.server_host = None
        self.server_port = None
        self.client_id = None
        self.client_user = None
        self.client_pw = None
        self.topics = None
        self.client = None

    def start(self):
        self.client = mqtt_client.Client(self.client_id)
        self.client.username_pw_set(self.client_user, self.client_pw)
        self.client.on_connect = mqtt_connect
        self.client.on_disconnect = mqtt_disconnect
        self.client.on_message = mqtt_incoming_data
        try:
            self.client.connect(self.server_host, self.server_port, 60)
        except OSError as err:
            f_error('connection_refused', str(err))
            window.signal_network_error()
        Thread(target=self.client.loop_forever).start()

    def stop(self):
        self.client.disconnect()
        self.client.loop_stop()

    def subscribe(self):
        self.client.subscribe(self.topics)

    def publish(self, topic, value):
        self.client.publish(topic, value)


def mqtt_connect(_cl, _ud, _code, _pp):
    window.mqtt.subscribe()
    print_log('Verbindung hergestellt')


def mqtt_disconnect(_cl, _ud, code):
    if code == 0:
        print_log('Verbindung getrennt')
    else:
        f_error('connection_interrupted', str(code))
        window.signal_network_error()


def mqtt_incoming_data(_cl, _ud, msg):
    topic = msg.topic
    value = msg.payload.decode('UTF-8')
    if value != '':
        window.signal_input_data(state_image.green)
        window.change_state_by_adress(topic, value)


def f_error(error_code, param=None):
    if error_code == 'file':
        Thread(target=lambda: playsound('sound/err_file.wav')).start()
        print_log('Datei nicht gefunden: ' + param)
    elif error_code == 'unknown_command':
        Thread(target=lambda: playsound('sound/err_unknown_command.wav')).start()
        print_log('Unbekanntes Kommando: ' + param)
    elif error_code == 'unknown_device':
        Thread(target=lambda: playsound('sound/err_unknown_device.wav')).start()
        print_log('Gerät ' + param + ' nicht definiert!')
    elif error_code == 'connection_refused':
        Thread(target=lambda: playsound('sound/err_connection_refused.wav')).start()
        print_log('Fehler beim aufbauen der Verbindung: ' + param)
    elif error_code == 'connection_interrupted':
        Thread(target=lambda: playsound('sound/err_connection_interrupted.wav')).start()
        print_log('Verbindung unterbrochen (Code ' + param + ')')


def print_log(message):
    print(message)
    log_file = open('iobroker.log', 'a')
    log_file.write(strftime('[%d/%m/%Y %H:%M:%S] ', localtime()) + message + '\n')
    log_file.close()


runtime = time()
version = 'Version 0.14-m'
print_log('ioBroker GUI gestartet (' + version + ')')
state_image = StateImage()
window = Window()
ctk.set_appearance_mode(window.appearance)

window.mqtt.start()
print_log('Bereit nach ' + str(round(time() - runtime, 3)) + ' Sec.')
window.mainloop()

window.mqtt.stop()
print_log('ioBroker GUI beendet')
