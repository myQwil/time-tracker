#!/usr/bin/env python3

import time
from sys import path
from os import system

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

def timefmt(sc):
	sign = '-' if sc < 0 else ''
	hr = abs(sc) / 3600
	mn = hr % 1 * 60
	sc = mn % 1 * 60
	return f'{sign}{int(hr)}:{int(mn):02d}:{int(sc):02d}'

class TrackWindow(Gtk.Window):
	def __init__(self):
		super().__init__(title='Timer')
		self.connect('delete-event', self.on_delete)
		self.connect('destroy' ,Gtk.main_quit)
		self.set_default_size(250, 0)
		self.start = time.time()
		self.color = 'off'
		self.quart = None

		self.conf = f'{path[0]}/timer.txt'
		try:
			f = open(self.conf ,'r')
			self.more = int(float(f.readline()))
			f.close()
		except:
			self.more = 0

		# # CSS styling
		provider = Gtk.CssProvider()
		Gtk.StyleContext().add_provider_for_screen( Gdk.Screen.get_default()
			,provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION )
		provider.load_from_data(b'''
			.switch {font-size: 16pt}
			.time   {font-size: 24pt}
			.on     {color: turquoise}
			.off    {color: grey}
		''')

		# # table
		table = Gtk.Table()
		self.add(table)
		i = 0 # row index

		# # play/pause switch
		self.switch = Gtk.Switch()
		self.switch.connect('notify::active', self.on_pause)
		table.attach(self.switch, 0, 2, i, i+1)
		# add a dummy label for a taller switch
		lbl_dummy = Gtk.Label()
		context = lbl_dummy.get_style_context()
		context.add_class('switch')
		table.attach(lbl_dummy, 0, 2, i, i+1)
		i += 1

		# # clock label
		self.lbl_clock = Gtk.Label()
		self.context = self.lbl_clock.get_style_context()
		self.context.add_class('time')
		self.context.add_class('off')
		table.attach(self.lbl_clock, 0, 2, i, i+1)
		self.tick()
		i += 1

		# # reset button
		btn_reset = Gtk.Button(label='Reset')
		btn_reset.connect('clicked', self.on_reset_clicked)
		adjust = Gtk.Adjustment(value=0 ,lower=-24 ,upper=24 ,step_increment=1)
		self.spn_reset = Gtk.SpinButton(adjustment=adjust, digits=3)
		table.attach(btn_reset, 0, 1, i, i+1)
		table.attach(self.spn_reset, 1, 2, i, i+1)
		i += 1

		# # delay button
		btn_delay = Gtk.Button(label='Delay')
		btn_delay.connect('clicked', self.on_delay_clicked)
		adjust = Gtk.Adjustment(value=0 ,lower=-60 ,upper=60 ,step_increment=1)
		self.spn_delay = Gtk.SpinButton(adjustment=adjust, digits=3)
		table.attach(btn_delay, 0, 1, i, i+1)
		table.attach(self.spn_delay, 1, 2, i, i+1)


	def since(self):
		return time.time() - self.start

	def get_total(self):
		return (self.since() if self.switch.get_state() else 0) + self.more

	def notify(self):
		system(f'kdialog --title "Timer" --passivepopup "{self.quart} hours"')

	def tick(self):
		seconds = self.get_total()
		quart = seconds // 900 / 4
		if self.switch.get_state() and self.quart != quart:
			self.quart = quart
			self.notify()
		self.lbl_clock.set_label(timefmt(seconds))
		return True # repeat indefinitely

	def change_color(self, color):
		self.context.remove_class(self.color)
		self.context.add_class(color)
		self.color = color

	def on_pause(self, switch, gparam):
		if switch.get_state():
			self.timer = GLib.timeout_add(1000, self.tick)
			self.start = time.time()
			self.change_color('on')
		else:
			GLib.source_remove(self.timer)
			self.more += self.since()
			self.change_color('off')
		self.tick()

	def on_reset_clicked(self, widget):
		self.start = time.time()
		self.more = 3600 * self.spn_reset.get_value()
		self.tick()

	def on_delay_clicked(self, widget):
		self.more -= 60 * self.spn_delay.get_value()
		self.tick()

	def on_delete(self, widget, *data):
		f = open(self.conf ,'w')
		f.write(f'{self.get_total()}\n')
		f.close()
		return False

win = TrackWindow()
win.show_all()
Gtk.main()
