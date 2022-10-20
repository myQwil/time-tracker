#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from matplotlib.backends.backend_gtk3agg import (
    FigureCanvasGTK3Agg as FigureCanvas)

import gc
import sqlite3
import matplotlib
import numpy as np
from sys import path
from math import ceil
from datetime import datetime, timedelta
from matplotlib import pyplot as plt, dates as mdates

# Preferences
ndays = 28
'the number of days to plot'

matplotlib.use('GTK3Agg')
plt.style.use('dark_background')
fignum = 0

now = datetime.now().date()
today = now.strftime('%Y-%m-%d')
db = f'{path[0]}/hours.db'

def track_save(seconds=None):
	# create hours.db if it doesn't already exist
	con = sqlite3.connect(db)
	cur = con.cursor()
	cur.execute(
		'CREATE TABLE IF NOT EXISTS work (day DATE PRIMARY KEY, seconds REAL)'
	)
	cur.execute('SELECT seconds FROM work WHERE day = ?', (today,))
	if cur.fetchone():
		if seconds is not None:
			cur.execute('UPDATE work SET seconds = ? WHERE day = ?', (seconds, today))
	else:
		# insert blank rows on any skipped days
		cur.execute('SELECT day FROM work ORDER BY day DESC LIMIT 1')
		prev = cur.fetchone()
		if prev:
			one_day = timedelta(days=1)
			prev = datetime.strptime(prev[0],'%Y-%m-%d').date() + one_day
			while prev < now:
				cur.execute('INSERT INTO work VALUES(?, 0)', (prev.strftime('%Y-%m-%d'),))
				prev += one_day
		if seconds is None:
			seconds = 0
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
	return row[0]

def on_delete(win, widget, *data):
	plt.close(fignum)
	gc.collect()

def show(app=None):
	global fignum
	# check if window is already open
	if plt.fignum_exists(fignum):
		return

	con = sqlite3.connect(db)
	cur = con.cursor()
	cur.execute('SELECT * FROM work ORDER BY day DESC LIMIT ?', (ndays,))
	rows = cur.fetchall()
	con.close()

	s2h = 1 / 3600
	hours = [r[1] * s2h for r in reversed(rows)]
	days = [mdates.datestr2num(r[0]) for r in reversed(rows)]
	rowlen = len(rows)
	if rowlen < ndays:
		# prepend the list with blank days
		rem = ndays - rowlen
		firstday = days[0] - rem
		hours = [0.0] * rem + hours
		days = [firstday + i for i in range(rem)] + days

	fig, ax = plt.subplots()
	fignum = fig.number
	ax.xaxis.set_major_locator(mdates.DayLocator(interval=ceil(len(days) / 8)))
	ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d'))

	annot = ax.annotate(
		 text='', xy=(0, 0), xytext=(0, 10), ha='center'
		,textcoords='offset points', bbox=dict(boxstyle='round', fc='w')
	)
	annot.get_bbox_patch().set_facecolor('black')

	def on_pick(event):
		xdata, ydata = event.artist.get_data()
		i = event.ind
		date = mdates.num2date(xdata[i]).strftime('%b-%d')
		hr = ydata[i]
		mn = hr % 1 * 60
		sc = mn % 1 * 60
		annot.xy = (xdata[i], ydata[i])
		annot.set_text(f'{date}, {int(hr)}:{int(mn):02d}:{int(sc):02d}')
		annot.set_visible(True)
		fig.canvas.draw_idle()
	fig.canvas.mpl_connect('pick_event', on_pick)

	def line_picker(line, mouseevent):
		if mouseevent.xdata is None:
			annot.set_visible(False)
			fig.canvas.draw_idle()
			return False, dict()
		xdata = line.get_xdata()
		ydata = line.get_ydata()
		maxd = 0.5
		d = np.sqrt(
			(xdata - mouseevent.xdata)**2 + (ydata - mouseevent.ydata)**2)

		ind = min(range(len(d)), key=d.__getitem__)
		if d[ind] <= maxd:
			pickx = xdata[ind]
			picky = ydata[ind]
			props = dict(ind=ind, pickx=pickx, picky=picky)
			return True, props
		else:
			annot.set_visible(False)
			fig.canvas.draw_idle()
			return False, dict()
	plt.plot(days, hours, marker='o', picker=line_picker)

	plt.title(f'Work Hours for the Last {ndays} Days')
	plt.xlabel('Days')
	plt.ylabel('Hours Worked')

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


track_save()
if __name__ == '__main__':
	show()
