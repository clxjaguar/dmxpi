#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import array, time

try:
	# sudo apt-get install python3-pyqt5
	# ~ raise("We want to use PyQt4")
	from PyQt5.QtGui import *
	from PyQt5.QtCore import *
	from PyQt5.QtWidgets import *
	print("Using PyQt5")
except:
	# sudo apt-get install python-qtpy python3-qtpy
	from PyQt4.QtGui import *
	from PyQt4.QtCore import *
	print("Using PyQt4")

class GUI(QWidget):
	def __init__(self):
		QWidget.__init__(self)
		self.pageOffset = 0
		self.channelsOffset = 0
		self.fpsCounter = 0
		self.lastUpdated = 0
		self.dmxThread = My_DMX_Receiver()
		self.dmxThread.dataReceived.connect(self.update)
		self.initUI()
		self.dmxThread.start()

	def initUI(self):
		self.setStyleSheet("\
			QWidget { background-color: #000000; color: #ffffff; } \
			QLabel { margin: 0px; padding: 0px; } \
			QSplitter::handle:vertical   { image: none; } \
			QSplitter::handle:horizontal { width: 2px; image: none; } \
			QPushButton { background-color: #404040; } \
			QPushButton::disabled { color: #404040; } \
			QLabel#label { font-size: 30pt; } \
		");

		def mkQLabel(objectName, text='', layout=None, alignment=Qt.AlignLeft):
			o = QLabel()
			o.setObjectName(objectName)
			o.setAlignment(alignment)
			o.setText(text)
			if layout != None:
				layout.addWidget(o)
			return o

		def mkButton(text, function):
			btn = QPushButton(text)
			btn.setFocusPolicy(Qt.TabFocus)
			btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
			if function:
				btn.clicked.connect(function)
			return btn

		layout = QHBoxLayout(self)

		gridlayout = QGridLayout()

		self.labels = []
		for j in range(7):
			for i in range(10):
				l = QLabel("---\n%d" % (len(self.labels)+1))
				l.oldVal = -1
				l.setAlignment(Qt.AlignCenter)
				gridlayout.addWidget(l, j, i)
				self.labels.append(l)

		layout.addLayout(gridlayout, 10)

		buttonsLayout = QVBoxLayout()
		layout.addLayout(buttonsLayout, 0)
		self.fpsLabel = mkQLabel('', '--- fps', buttonsLayout, alignment=Qt.AlignCenter)

		self.pageUpBtn = mkButton(u"△", self.pageUp)
		self.pageUpBtn.setEnabled(False)
		buttonsLayout.addWidget(self.pageUpBtn)

		self.pageDownBtn = mkButton(u"▽", self.pageDown)
		buttonsLayout.addWidget(self.pageDownBtn)

		btn_quit = mkButton("Exit", self.close);
		buttonsLayout.addWidget(btn_quit)

		self.setWindowTitle(u"DMX Monitor")

		self.setWindowState(self.windowState() ^ Qt.WindowMaximized)
		self.showFullScreen()
		self.show()
		self.refreshTimer = QTimer()
		self.refreshTimer.timeout.connect(self.refreshFpsCounter)
		self.refreshTimer.start(1000)

		self.timerHideMouse = QTimer()
		self.timerHideMouse.timeout.connect(self.timerHideMouseTimeout)
		self.timerHideMouse.start(1000)

	def pageUp(self):
		self.pageOffset-=1
		if self.pageOffset <= 0:
			self.pageOffset = 0
			self.pageUpBtn.setEnabled(False)
		self.channelsOffset = self.pageOffset*len(self.labels)
		self.refresh(force=True)
		self.pageDownBtn.setEnabled(True)

	def pageDown(self):
		self.pageOffset+=1
		self.channelsOffset = self.pageOffset*len(self.labels)
		self.pageUpBtn.setEnabled(True)
		self.refresh(force=True)
		if (self.labels[-1].text() == ""):
			self.pageDownBtn.setEnabled(False)

	def update(self):
		self.fpsCounter+=1
		# ~ if time.time() - self.lastUpdated > 0.2:
		self.refresh()


	def refresh(self, force=False):
		i = self.channelsOffset
		data = self.dmxThread.data
		for l in self.labels:
			if force or data[i] != l.oldVal:
				if i>=len(data):
					l.setText("")
				else:
					l.setText("%d\n%d" % (data[i], i+1))
					l.oldVal = data[i]
			i+=1

	def refreshFpsCounter(self):
		self.fpsLabel.setText(str(self.fpsCounter) + " fps")
		self.fpsCounter = 0

	def eventFilter(self, source, event):
		if event.type() == QEvent.MouseMove:
			if event.buttons() == Qt.NoButton:
				self.setCursor(Qt.ArrowCursor)
				self.timerHideMouse.start(750)
		return QMainWindow.eventFilter(self, source, event)

	def timerHideMouseTimeout(self):
		self.timerHideMouse.stop()
		self.setCursor(Qt.BlankCursor)

from ola.ClientWrapper import ClientWrapper
class My_DMX_Receiver(QObject):
	dataReceived = pyqtSignal()

	def __init__(self, universe=1):
		QObject.__init__(self)
		self.exitRequested = False
		self.data = [-1]*512
		self.universe = universe

	def newData(self, data):
		self.data = data
		self.dataReceived.emit()

	def start(self):
		self.thread = QThread()
		self.thread.setObjectName("DMX RX")
		self.moveToThread(self.thread)
		self.thread.started.connect(self.worker)
		self.thread.start()

	def worker(self):
		wrapper = ClientWrapper()
		client = wrapper.Client()
		client.RegisterUniverse(self.universe, client.REGISTER, self.newData)
		wrapper.Run()

	def stop(self):
		wrapper.Stop()


def main():
	app = QApplication(sys.argv)
	m1 = GUI()

	app.installEventFilter(m1)
	ret = app.exec_()

	print("Exiting main()...")
	sys.exit(ret)

if __name__ == '__main__':
	main()
