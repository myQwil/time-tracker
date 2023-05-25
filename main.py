#!/usr/bin/env python3

import time
import graph
from os import popen, system

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

# Preferences
work = 'program-name'
'the name of the program associated with work'

def timefmt(sc):
	sign = '-' if sc < 0 else ''
	hr = abs(sc) / 3600
	mn = hr % 1 * 60
	sc = mn % 1 * 60
	return f'{sign}{int(hr)}:{int(mn):02d}:{int(sc):02d}'

def on_activate(app):
	if not hasattr(app, 'already'):
		app.already = True
		win = TrackWindow(app)
		win.show_all()
app = Gtk.Application(application_id='org.gtk.TimeTracker')
app.connect('activate', on_activate)

class TrackWindow(Gtk.ApplicationWindow):
	def __init__(self, app):
		super().__init__(title='Time Tracker', application=app)
		self.connect('delete-event', self.on_delete)
		self.set_default_size(250, 0)
		self.len = -len(work) - 1
		self.start = time.time()
		self.color = 'off'
		self.quart = None
		self.app = app

		self.more = graph.track_load()

		# # CSS styling
		provider = Gtk.CssProvider()
		Gtk.StyleContext().add_provider_for_screen( Gdk.Screen.get_default()
			,provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION )
		provider.load_from_data(b'''
			.pad    { font-size: 2pt; }
			.switch { font-size: 16pt }
			.time   { font-size: 24pt }
			.on     { color: turquoise }
			.off    { color: grey }
		''')

		# # table
		table = Gtk.Table()
		self.add(table)
		row = 0

		dummy = Gtk.Label()
		context = dummy.get_style_context()
		context.add_class('pad')
		table.attach(dummy, 0, 6, row, row+1)
		row += 1

		# # play/pause switch
		self.switch = Gtk.Switch()
		self.switch.connect('notify::active', self.on_pause)
		table.attach(self.switch, 1, 5, row, row+1)
		# add a dummy label for a taller switch
		lbl_dummy = Gtk.Label()
		context = lbl_dummy.get_style_context()
		context.add_class('switch')
		table.attach(lbl_dummy, 0, 6, row, row+1)
		row += 1

		# # clock label
		self.lbl_clock = Gtk.Label()
		self.context = self.lbl_clock.get_style_context()
		self.context.add_class('time')
		self.context.add_class('off')
		table.attach(self.lbl_clock, 0, 6, row, row+1)
		self.tick()
		row += 1

		# # graph button
		btn_graph = Gtk.Button(label='Graph')
		btn_graph.connect('clicked', self.on_graph_clicked)
		table.attach(btn_graph, 0, 6, row, row+1)

		# start the checker
		GLib.timeout_add(4000, self.check)


	def since(self):
		return time.time() - self.start

	def get_total(self):
		return (self.since() if self.switch.get_state() else 0) + self.more

	def notify(self):
		msg = f'"Worked {self.quart} hours"'
		system(f'kdialog --title "Time Tracker" --passivepopup {msg}')

	def tick(self):
		seconds = self.get_total()
		quart = seconds // 900 / 4
		if self.switch.get_state() and self.quart != quart:
			self.quart = quart
			self.notify()
		self.lbl_clock.set_label(timefmt(seconds))
		return True # repeat indefinitely

	def check(self):
		focus = popen('xdotool getactivewindow getwindowname').read()[self.len:-1]
		working = (focus == work)
		if working != self.switch.get_state():
			self.switch.set_active(working)
		return True

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

	def on_graph_clicked(self, widget):
		graph.track_save(self.get_total())
		graph.show(self.app)

	def on_delete(self, widget, *data):
		graph.track_save(self.get_total())
		return False

app.run()
