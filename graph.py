#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from matplotlib.backends.backend_gtk3agg import (
	FigureCanvasGTK3Agg as FigureCanvas)

import gc
import sqlite3
import matplotlib
from sys import path
from math import ceil
from datetime import datetime
from matplotlib import dates, pyplot as plt

# Preferences
ndays = 28
'the number of days to plot'

matplotlib.use('GTK3Agg')
plt.style.use('dark_background')
fignum = 0

now = datetime.now().date()
today = now.strftime('%Y-%m-%d')
db = f'{path[0]}/.db'

def track_save(seconds):
	con = sqlite3.connect(db)
	cur = con.cursor()
	cur.execute(
		'CREATE TABLE IF NOT EXISTS work (day DATE PRIMARY KEY, seconds REAL)'
	)
	if seconds > 0:
		cur.execute('SELECT seconds FROM work WHERE day = ?', (today,))
		if cur.fetchone():
			cur.execute('UPDATE work SET seconds = ? WHERE day = ?', (seconds, today))
		else:
			cur.execute('INSERT INTO work VALUES (?, ?)', (today, seconds))
	con.commit()
	con.close()

def track_load():
	# load hours from a previous session today, if it exists
	con = sqlite3.connect(db)
	cur = con.cursor()
	cur.execute('SELECT seconds FROM work WHERE day = ?', (today,))
	row = cur.fetchone()
	con.close()
	return row[0] if row else 0

def on_delete(win, widget, *data):
	plt.close(fignum)
	gc.collect()

def show(app=None):
	global fignum
	# check if window is already open
	if plt.fignum_exists(fignum):
		return

	fig, ax = plt.subplots()
	fignum = fig.number
	ax.xaxis.set_major_locator(dates.DayLocator(interval=ceil(ndays / 8)))
	ax.xaxis.set_major_formatter(dates.DateFormatter('%b-%d'))
	plt.title(f'Work Hours for the Last {ndays} Days')
	plt.xlabel('Days')
	plt.ylabel('Hours Worked')

	con = sqlite3.connect(db)
	cur = con.cursor()
	cur.execute('SELECT * FROM work ORDER BY day DESC LIMIT ?', (ndays,))
	rows = cur.fetchall()
	con.close()

	s2h = 1 / 3600
	stop = int(dates.datestr2num(today)) + 1
	start = stop - ndays
	hours = [0.0] * ndays
	for x in rows:
		hours[int(dates.datestr2num(x[0]) - start)] = x[1] * s2h

	annot = ax.annotate(text='', xy=(0, 0), xytext=(0, 10), ha='center'
		, textcoords='offset points', bbox=dict(boxstyle='round', fc='w'))
	annot.get_bbox_patch().set_facecolor('black')

	def on_pick(event):
		i = event.idx
		date = dates.num2date(i + start).strftime('%b-%d')
		hr = hours[i]
		mn = hr % 1 * 60
		sc = mn % 1 * 60
		annot.xy = (event.x, event.y)
		annot.set_text(f'{date}, {int(hr)}:{int(mn):02d}:{int(sc):02d}')
		annot.set_visible(True)
		fig.canvas.draw_idle()

	def annot_off():
		annot.set_visible(False)
		fig.canvas.draw_idle()
		return False, dict()

	def line_picker(_, mouseevent):
		if mouseevent.xdata is None:
			return annot_off()
		idx = round(mouseevent.xdata - start)
		if 0 <= idx and idx < ndays:
			props = dict(idx=idx, x=mouseevent.xdata, y=mouseevent.ydata)
			return True, props
		else:
			return annot_off()

	fig.canvas.mpl_connect('pick_event', on_pick)
	ax.bar(list(range(start, stop)), hours, picker=line_picker)

	win = Gtk.Window()
	win.set_title('Work Chart')
	win.set_default_size(800, 600)
	win.add(FigureCanvas(fig))
	win.show_all()
	if app:
		win.connect("delete-event", on_delete)
		app.add_window(win)
	else:
		win.connect("delete-event", Gtk.main_quit)
		Gtk.main()


if __name__ == '__main__':
	show()
