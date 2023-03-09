#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, fnmatch, threading
import array, time

data = [0]*100
fogChannel = 40 #40
fanChannel = 41 #41

FAN_OFF = 0
FAN_ON = 255

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

class JumpSlider(QSlider):
	def mousePressEvent(self, event):
		val = self.pixelPosToRangeValue(event.pos())
		self.setValue(val)

	def mouseMoveEvent(self, event):
		val = self.pixelPosToRangeValue(event.pos())
		self.setValue(val)

	def pixelPosToRangeValue(self, pos):
		opt = QStyleOptionSlider()
		self.initStyleOption(opt)
		gr = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
		sr = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)

		if self.orientation() == Qt.Horizontal:
			sliderLength = sr.width()
			sliderMin = gr.x()
			sliderMax = gr.right() - sliderLength + 1
		else:
			sliderLength = sr.height()
			sliderMin = gr.y()
			sliderMax = gr.bottom() - sliderLength + 1;
		pr = pos - sr.center() + sr.topLeft()
		p = pr.x() if self.orientation() == Qt.Horizontal else pr.y()
		return QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), p - sliderMin, sliderMax - sliderMin, opt.upsideDown)

class GUI(QWidget):
	def __init__(self):
		super(GUI, self).__init__()
		self.initUI()

	def initUI(self):
		self.setStyleSheet("\
			QWidget { background-color: #000000; color: #ffffff; } \
			QLabel { margin: 0px; padding: 0px; } \
			QSplitter::handle:vertical   { image: none; } \
			QSplitter::handle:horizontal { width: 2px; image: none; } \
			QPushButton { background-color: #404040; background: #404040; } \
			QLabel#label { font-size: 30pt; } \
			QSlider { height: 25px; color: red; padding: 0px; margin: 0px; } \
			QSlider::groove:horizontal { border: 1px solid #bbb; height: 20px; border-radius: 4px; } \
			QSlider::sub-page:horizontal { background: qlineargradient(x1: 0, y1: 0,    x2: 0, y2: 1, stop: 0 #66e, stop: 1 #bbf); background: qlineargradient(x1: 0, y1: 0.2, x2: 1, y2: 1, stop: 0 #bbf, stop: 1 #55f); border: 1px solid #777; height: 10px; border-radius: 4px; } \
			QSlider::handle:horizontal { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eee, stop:1 #ccc); border: 1px solid #777; width: 30px; margin-top: -2px; margin-bottom: -2px; border-radius: 4px; } \
			QSlider::handle:horizontal:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #fff, stop:1 #ddd); border: 1px solid red; border-radius: 4px; } \
			QSlider::sub-page:horizontal:disabled { background: #bbb; border-color: #999; } \
			QSlider::add-page:horizontal:disabled { background: #eee; border-color: #999; } \
			QSlider::handle:horizontal:disabled { background: #eee; border: 1px solid #aaa; border-radius: 4px; } \
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

		layout = QVBoxLayout(self)

		gridlayout = QGridLayout()

		mkQLabel('', "OFF time", layout, Qt.AlignLeft | Qt.AlignBottom);
		self.OffTimeSlider = JumpSlider(Qt.Horizontal);
		self.OffTimeSlider.setMaximum(3000) # 300s
		self.OffTimeSlider.setValue(600) # 60s
		layout.addWidget(self.OffTimeSlider)

		mkQLabel('', "ON Time", layout, Qt.AlignLeft | Qt.AlignBottom);
		self.durationSlider = JumpSlider(Qt.Horizontal);
		self.durationSlider.setMaximum(100) # 100 = 10s
		self.durationSlider.setValue(30)
		layout.addWidget(self.durationSlider)

		mkQLabel('', "Pressure", layout, Qt.AlignLeft | Qt.AlignBottom);
		self.pressureSlider = JumpSlider(Qt.Horizontal);
		self.pressureSlider.setMaximum(255)
		self.pressureSlider.setValue(50)
		layout.addWidget(self.pressureSlider)

		self.qlabel = mkQLabel('label', "---", layout, Qt.AlignLeft | Qt.AlignTop)

		buttonsLayout = QHBoxLayout()
		layout.addLayout(buttonsLayout)

		y = mkButton("Make some\nfog now!", self.fogNow)
		buttonsLayout.addWidget(y)

		z = mkButton("Start/Stop\ntimer", self.OnOffButton)
		buttonsLayout.addWidget(z)

		btn_quit = mkButton("Exit", self.close);
		buttonsLayout.addWidget(btn_quit)

		self.setWindowTitle(u"Fog timer")

		# ~ self.setWindowState(self.windowState() ^ Qt.WindowMaximized)
		self.showFullScreen()
		self.show()
		self.tickingTimer = QTimer()
		self.tickingTimer.timeout.connect(self.tickingTimerTimeout)
		self.tickingTimer.start(100)
		self.state = 0
		self.tick = 0

		self.timerHideMouse = QTimer()
		self.timerHideMouse.timeout.connect(self.timerHideMouseTimeout)
		self.timerHideMouse.start(1000)

	def eventFilter(self, source, event):
		if event.type() == QEvent.MouseMove:
			if event.buttons() == Qt.NoButton:
				self.setCursor(Qt.ArrowCursor)
				self.timerHideMouse.start(750)
		return QMainWindow.eventFilter(self, source, event)

	def timerHideMouseTimeout(self):
		self.timerHideMouse.stop()
		self.setCursor(Qt.BlankCursor)

	def OnOffButton(self):
		self.tick = 0
		if self.state == 0:
			self.state = 1
		else:
			self.state = 0

	def fogNow(self):
		self.tick = 0
		self.state = 2


	def tickingTimerTimeout(self):
		global data
		self.tick+=1
		if self.state == 0:
			self.qlabel.setText("Standby")
			data[fogChannel-1] = 0
			data[fanChannel-1] = FAN_OFF

		elif self.state == 1:
			remaining = self.OffTimeSlider.value() - self.tick
			if remaining > 0:
				self.qlabel.setText("Waiting... %.1f"%(remaining/10.0))
				data[fogChannel-1] = 0
				if remaining < 30:
					data[fanChannel-1] = FAN_ON
			else:
				self.tick = 0
				self.state = 2

		elif self.state == 2:
			remaining = self.durationSlider.value() - self.tick
			if remaining > 0:
				self.qlabel.setText("Fogging now! %.1f" % (remaining/10.0))
				data[fogChannel-1] = int(self.pressureSlider.value())
				data[fanChannel-1] = FAN_ON
			else:
				self.tick = 0
				self.state = 1
				data[fogChannel-1] = 0
				data[fanChannel-1] = FAN_OFF

i = 0
exitLoop = False

def DmxLoop():
	from ola.ClientWrapper import ClientWrapper
	global exitLoop, data
	wrapper = ClientWrapper()
	client = wrapper.Client()

	def sendDmx():
		global i, data
		time.sleep(0.1)
		client.SendDmx(1, array.array('B', data), DmxSent)

	def DmxSent(state):
		global i, exitLoop, data
		i+=1
		if i>255:
			i=0
		if exitLoop:
			data = [0]*100
			sendDmx()
			time.sleep(2)
			wrapper.Stop()
		else:
			sendDmx()

	sendDmx()
	wrapper.Run()

def main():
	global m1, exitLoop
	app = QApplication(sys.argv)
	m1 = GUI()

	threads = []
	dmxLoopThread = threading.Thread(target=DmxLoop)
	threads.append(dmxLoopThread)
	dmxLoopThread.start()

	app.installEventFilter(m1)
	ret = app.exec_()

	print("Exiting main()...")
	exitLoop = True
	sys.exit(ret)

if __name__ == '__main__':
	main()
