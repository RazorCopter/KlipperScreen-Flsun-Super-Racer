import gi
import logging

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango

from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return PowerPanel(*args)


class PowerPanel(ScreenPanel):
    def initialize(self, panel_name):

        self.devices = {}

        # Create a scroll window for the power devices
        scroll = self._gtk.ScrolledWindow()

        # Create a grid for all devices
        self.labels['devices'] = Gtk.Grid()
        scroll.add(self.labels['devices'])

        # Create a box to contain all of the above
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_vexpand(True)
        box.pack_start(scroll, True, True, 0)

        self.load_power_devices()

        self.content.add(box)

    def activate(self):
        devices = self._screen.printer.get_power_devices()
        for x in devices:
            self.devices[x]['switch'].disconnect_by_func(self.on_switch)
            self.devices[x]['switch'].set_active(self._screen.printer.get_power_device_status(x) == "on")

            self.devices[x]['switch'].connect("notify::active", self.on_switch, x)

    def add_device(self, device):
        frame = Gtk.Frame()
        frame.get_style_context().add_class("frame-item")

        name = Gtk.Label()
        name.set_markup(f"<big><b>{device}</b></big>")
        name.set_hexpand(True)
        name.set_vexpand(True)
        name.set_halign(Gtk.Align.START)
        name.set_valign(Gtk.Align.CENTER)
        name.set_line_wrap(True)
        name.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

        switch = Gtk.Switch()
        switch.set_hexpand(False)
        switch.set_active(self._screen.printer.get_power_device_status(device) == "on")
        switch.connect("notify::active", self.on_switch, device)
        switch.set_property("width-request", round(self._gtk.get_font_size() * 7))
        switch.set_property("height-request", round(self._gtk.get_font_size() * 3.5))

        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        labels.add(name)

        dev = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        dev.set_hexpand(True)
        dev.set_vexpand(False)
        dev.set_valign(Gtk.Align.CENTER)
        dev.add(labels)
        dev.add(switch)
        frame.add(dev)

        self.devices[device] = {
            "row": frame,
            "switch": switch
        }

        devices = sorted(self.devices)
        pos = devices.index(device)

        self.labels['devices'].insert_row(pos)
        self.labels['devices'].attach(self.devices[device]['row'], 0, pos, 1, 1)
        self.labels['devices'].show_all()

    def load_power_devices(self):
        devices = self._screen.printer.get_power_devices()
        for x in devices:
            self.add_device(x)

    def on_switch(self, switch, gparam, device):
        logging.debug(f"Power toggled {device}")
        if switch.get_active():
            self._screen._ws.klippy.power_device_on(device)
        else:
            self._screen._ws.klippy.power_device_off(device)

    def process_update(self, action, data):
        if action != "notify_power_changed":
            return

        if data['device'] not in self.devices:
            return
        device = data['device']
        self.devices[device]['switch'].disconnect_by_func(self.on_switch)
        self.devices[device]['switch'].set_active(data['status'] == "on")
        self.devices[device]['switch'].connect("notify::active", self.on_switch, device)
