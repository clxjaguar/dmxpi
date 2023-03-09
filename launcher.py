#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, subprocess

try:
	# sudo apt-get install python3-pyqt5
	# ~ raise("Uncomment this line is to want to force fallback to PyQt4 for testing")
	from PyQt5.QtGui import *
	from PyQt5.QtCore import *
	from PyQt5.QtWidgets import *
	PYQT_VERSION = 5
	print("Using PyQt5")
except:
	# sudo apt-get install python-qtpy python3-qtpy
	from PyQt4.QtGui import *
	from PyQt4.QtCore import *
	PYQT_VERSION = 4
	print("Using PyQt4")

class GUI(QWidget):
	def __init__(self):
		self.BUTTONS = [("FOG GUI",      (0, 1),       "python fog-gui.py"),
		                ("DMX MONITOR",  (0, 0),       "python monitor.py"),
		                ("TERMINAL",     (0, 2),       "lxterminal"),
	                    ("EXIT",         (1, 0),       self.close),
	                    ("SHUTDOWN",     (1, 1, 1, 2), self.shutdown)]

		QWidget.__init__(self)
		self.initUI()
		self.address = ""
		self.refreshTimerTimeout()

	def initUI(self):
		self.setStyleSheet("\
			QWidget { background-color: #000000; color: #ffffff; } \
			QLabel { margin: 0px; padding: 0px; } \
			QSplitter::handle:vertical   { image: none; } \
			QSplitter::handle:horizontal { width:  2px; image: none; } \
			QPushButton { font-size: 12pt; background: #404040; border-radius: 6px; } \
			QPushButton#activated { background: #ff0000; } \
			QLabel#label { font-size: 24pt; } \
		");

		layout = QVBoxLayout(self)

		def mkQLabel(text=None, layout=None, alignment=Qt.AlignLeft, objectName=None):
			o = QLabel()
			if objectName:
				o.setObjectName(objectName)
			o.setAlignment(alignment)
			if text:
				o.setText(text)
			if layout != None:
				layout.addWidget(o)
			return o

		def mkButton(text, layout=None, function=None):
			btn = QPushButton(text)
			btn.setFocusPolicy(Qt.TabFocus)
			if function:
				btn.clicked.connect(function)
			if layout != None:
				layout.addWidget(btn)
			return btn

		gridLayout = QGridLayout()

		self.buttons = []
		def mkGridButton(name, gridLayout, pos, func):
			b = QPushButton(name)

			gridLayout.addWidget(b, *pos)
			if func != None:
				if type(func) == str:
					b.clicked.connect(self.clickedOnButton)
					b.runFunc = func
				else:
					b.clicked.connect(func)

			b.setFocusPolicy(Qt.NoFocus)
			b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
			return b

		self.addressLabel = mkQLabel("---", layout, Qt.AlignLeft | Qt.AlignCenter, 'label')

		def fct(text):
			lines = len(text.split("\n"))
			if lines == 2:
				text+="\n"
			elif lines == 1:
				text+="\n\n"
			elif lines == 0:
				text+="\n\n\n"

			self.addressLabel.setText2(text)

		self.addressLabel.setText2 = self.addressLabel.setText
		self.addressLabel.setText = fct

		for t, pos, func in self.BUTTONS:
			self.buttons.append(mkGridButton(t, gridLayout, pos, func))

		layout.addLayout(gridLayout)

		self.setWindowTitle(u"DMX PI Launcher")
		self.showFullScreen()
		self.show()

		self.refreshTimer = QTimer()
		self.refreshTimer.timeout.connect(self.refreshTimerTimeout)
		self.refreshTimer.start(5000)

		self.hideMouseTimer = QTimer()
		self.hideMouseTimer.timeout.connect(self.hideMouseTimerTimeout)
		self.hideMouseTimer.start(100)

	def refreshTimerTimeout(self):
		completedProcess = subprocess.check_output(["ip", "addr"])

		addr = ""
		for line in str(completedProcess).replace("\\n", "\n").split("\n"):
			data = line.split()
			if len(data) < 2:
				continue
			if data[0] == "inet":
				if data[1].split("/")[0] == "127.0.0.1":
					continue
				if addr != "":
					addr+="\n"
				addr+= data[-1]+" "+data[1]

		self.addressLabel.setText(addr)
		if addr != self.address:
			self.address = addr
			if addr != "":
				print(addr)
				self.addressLabel.setText(self.address+"\nRestarting OLAD...")
				self.reloadServiceTimer = QTimer()
				self.reloadServiceTimer.timeout.connect(self.reloadService)
				self.reloadServiceTimer.start(1000)

	def reloadService(self):
		del self.reloadServiceTimer
		try:
			completedProcess = subprocess.check_output(["sudo", "service", "olad-clx", "restart"], stderr=subprocess.STDOUT)
			if completedProcess == "":
				completedProcess = "OLAD service restarted!"
			self.addressLabel.setText(self.address+"\n"+completedProcess)
		except:
			self.addressLabel.setText(self.address+"\nERROR")

	def close(self):
		exit(0)

	def shutdown(self):
		self.runCommandWithTimer("sudo poweroff", self.sender())
		self.refreshTimer.stop()

	def clickedOnButton(self):
		self.runCommandWithTimer(self.sender().runFunc, self.sender())

	def runCommandWithTimer(self, command, btn):
		btn.setStyleSheet("background: #ffff00; color: #000000;");
		btn.setEnabled(False)
		self.addressLabel.setText(command)
		self.runCommand = command
		self.timerCommand = QTimer()
		self.timerCommand.timeout.connect(self.runCommandTimeoutTimer)
		self.timerCommand.start(1000)

	def runCommandTimeoutTimer(self):
		del self.timerCommand
		os.system(self.runCommand)
		self.addressLabel.setText("")
		for b in self.buttons:
			b.setStyleSheet("");
			b.setEnabled(True)

	def eventFilter(self, source, event):
		if event.type() == QEvent.MouseMove:
			if event.buttons() == Qt.NoButton:
				self.setCursor(Qt.ArrowCursor)
				self.hideMouseTimer.start(300)
		return QMainWindow.eventFilter(self, source, event)

	def hideMouseTimerTimeout(self):
		self.hideMouseTimer.stop()
		self.setCursor(Qt.BlankCursor)

def main():
	global m1
	app = QApplication(sys.argv)
	m1 = GUI()
	app.installEventFilter(m1)
	ret = app.exec_()
	sys.exit(ret)

if __name__ == '__main__':
	main()
