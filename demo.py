#!/usr/bin/env python3

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QSizePolicy

import cv2
import numpy as np
import sys
import time
import os
import random
import math

import checkAlign
from connectPLC import PLC
from detectYesNo import Detect
from checkOnJig import CheckOn


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class Thread(QThread):
    progress = pyqtSignal()

    def run(self):
        while True:
            self.progress.emit()
            time.sleep(0.1)

class Query(QThread):
    progress = pyqtSignal()

    def run(self):
        while True:
            self.progress.emit()
            time.sleep(0.5)

class Send(QThread):
    progress = pyqtSignal()

    def run(self):
        while True:
            self.progress.emit()
            time.sleep(0.1)

class App(QMainWindow):
    def __init__(self):
        super().__init__()

        # QT Config
        self.title = "UET-CAM"
        self.icon = QIcon(resource_path('data/icon/uet.png'))

        # Declare Main Variable
        self.total = 0
        self.number_tested = 0
        self.number_success = 0
        self.number_error1 = 0
        self.number_error2 = 0
        self.number_error3 = 0
        self.count = 0

        self.cap_detect = any
        self.cap_check = any
        self.get_cap_detect = False
        self.get_cap_check = False

        self.Controller = PLC()
        self.command = "Idle"
        self.delay = True
        self.wait = False
        self.demo_count = 0
        self.report_one_time = True
        self.error_one_time = True

        self.count_file = open(resource_path('data/demo/Test/count.txt'), 'r+')
        self.count_current_ok = int(self.count_file.readline())
        self.count_current_ng = int(self.count_file.readline())
        self.count_file.close()

        # Run QT
        self.initUI()
    
    def initUI(self):

        # Config Main Window
        self.setWindowTitle(self.title)
        self.setWindowIcon(self.icon)
        self.setWindowState(Qt.WindowFullScreen)
        self.setStyleSheet("background-color: rgb(171, 171, 171);")

        # Config Auto Fit Screen Scale Variables
        self.sg = QDesktopWidget().screenGeometry()
        self.width_rate = self.sg.width() / 1920
        self.height_rate = self.sg.height() / 1080
        self.font_rate = math.sqrt(self.sg.width()*self.sg.width() + self.sg.height()*self.sg.height()) / math.sqrt(1920*1920 + 1080*1080)
        
        # Show UET LOGO
        self.uet_logo = QLabel(self)
        self.uet_pixmap = QPixmap(resource_path('data/icon/uet.png')).scaled(111 * self.width_rate, 111 * self.width_rate, Qt.KeepAspectRatio)
        self.uet_logo.setPixmap(self.uet_pixmap)
        self.uet_logo.setGeometry(100 * self.width_rate, 10 * self.height_rate, 111 * self.width_rate, 111 * self.height_rate)

        # Show Title
        self.title_label = QLabel("H??? TH???NG KI???M TRA LINH KI???N (CAM-UET-MEMS)", self)
        self.title_label.setGeometry(341 * self.width_rate, 17 * self.height_rate, 1300 * self.width_rate, 95 * self.height_rate)
        font_title = QFont('', int(35 * self.font_rate), QFont.Bold)
        self.title_label.setFont(font_title)
        self.title_label.setStyleSheet("color: rgb(255, 255, 255);")

        # Show Current Time
        self.time_label = QLabel(self)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setGeometry(1500 * self.width_rate, 20 * self.height_rate, 430 * self.width_rate, 95 * self.height_rate)
        font_timer = QFont('', int(40 * self.font_rate), QFont.Bold)
        self.time_label.setFont(font_timer)
        timer = QTimer(self)
        timer.timeout.connect(self.updateTimer)
        timer.start(1000)
        self.time_label.setStyleSheet("color: rgb(255, 255, 255);")

        # Show Detect Camera
        self.cam1_name = QLabel("DETECT CAMERA", self)
        self.cam1_name.setGeometry(55 * self.width_rate, 127 * self.height_rate, 728 * self.width_rate, 60 * self.height_rate)
        self.cam1_name.setAlignment(Qt.AlignCenter)
        self.cam1_name.setStyleSheet("background-color: rgb(50, 130, 184);"
                                    "color: rgb(255, 255, 255);"
                                    "font: bold 14pt;")
        self.cam1 = QLabel(self)
        self.cam1.setGeometry(55 * self.width_rate, 185 * self.height_rate, 728 * self.width_rate, 410 * self.height_rate)
        self.cam1.setStyleSheet("border-color: rgb(50, 130, 184);"
                                "border-width: 5px;"
                                "border-style: inset;")

        # Show Check Camera
        self.cam2_name = QLabel("CHECK CAMERA", self)
        self.cam2_name.setGeometry(55 * self.width_rate, 606 * self.height_rate, 728 * self.width_rate, 60 * self.height_rate)
        self.cam2_name.setAlignment(Qt.AlignCenter)
        self.cam2_name.setStyleSheet("background-color: rgb(50, 130, 184);"
                                    "color: rgb(255, 255, 255);"
                                    "font: bold 14pt;")
        self.cam2 = QLabel(self)
        self.cam2.setGeometry(55 * self.width_rate, 666 * self.height_rate, 728 * self.width_rate, 410 * self.height_rate)
        self.cam2.setStyleSheet("border-color: rgb(50, 130, 184);"
                                "border-width: 5px;"
                                "border-style: inset;")

        # Set Font
        self.font = QFont('', int(14 * self.font_rate), QFont.Bold)
        
        # Trays Information
        self.tray = []
        for i in range(2):
            tray_name = QLabel("TRAY {}".format(i+1), self)
            tray_name.setGeometry((980 + 400*i - 5) * self.width_rate, 127 * self.height_rate, 372 * self.width_rate, 60 * self.height_rate)
            tray_name.setAlignment(Qt.AlignCenter)
            tray_name.setStyleSheet("background-color:rgb(50, 130, 184);"
                                    "color: rgb(255, 255, 255);"
                                    "font: bold 14pt;")
            table_margin = QLabel(self)
            table_margin.setGeometry((980 + 400*i - 5) * self.width_rate, 181 * self.height_rate, 372 * self.width_rate, 417 * self.height_rate)
            table_margin.setStyleSheet("border-color: rgb(50, 130, 184);"
                                        "border-width: 5px;"
                                        "border-style: inset;")
            table = QTableWidget(7, 3, self)
            table.setGeometry((980 + 400*i) * self.width_rate, 186 * self.height_rate, int(362 * self.width_rate) + 1, int(408 * self.height_rate) + 0.5)
            table.horizontalHeader().hide()
            table.verticalHeader().hide()
            for j in range(3):
                table.setColumnWidth(j, 120 * self.width_rate)
            for j in range(7):
                table.setRowHeight(j, 58 * self.height_rate)
            table.setFont(self.font)
            table.setStyleSheet("color: rgb(255, 255, 255);")
            self.tray.append(table)
        for c in range(42):
            self.tray[int(math.floor(c/21))].setItem(c % 7, int(math.floor(c/7) - math.floor(c/21) * 3), QTableWidgetItem())
            self.tray[int(math.floor(c/21))].item(c % 7, int(math.floor(c/7) - math.floor(c/21) * 3)).setBackground(QColor(192, 192, 192))

        # Table Info Area        
        self.s_name = QLabel("INFORMATION", self)
        self.s_name.setGeometry(830 * self.width_rate, 606 * self.height_rate, 734 * self.width_rate, 60 * self.height_rate)
        self.s_name.setAlignment(Qt.AlignCenter)
        self.s_name.setStyleSheet("background-color:rgb(50, 130, 184);"
                                    "color: rgb(255, 255, 255);"
                                    "font: bold 14pt;")

        self.statistic_table = QTableWidget(5, 3, self)
        self.statistic_table.setGeometry(830 * self.width_rate, 666 * self.height_rate, int(734 * self.width_rate) + 1, int(410 * self.height_rate) + 1)
        self.statistic_table.horizontalHeader().hide()
        self.statistic_table.verticalHeader().hide()
        self.statistic_table.setFont(self.font)
        self.statistic_table.setStyleSheet("color: rgb(255, 255, 255);"
                                            "text-align: center;"
                                            "border-width: 5px;"
                                            "border-style: inset;"
                                            "border-color: rgb(50, 130, 184);")
        for j in range(3):
            self.statistic_table.setColumnWidth(j, 241 * self.width_rate)
        for j in range(5):
            self.statistic_table.setRowHeight(j, 80 * self.height_rate)
        tested_item = QTableWidgetItem("TESTED")
        tested_item.setTextAlignment(Qt.AlignCenter)
        tested_item.setFont(self.font)
        self.statistic_table.setItem(0, 0, tested_item)

        success_item = QTableWidgetItem("SUCCESS")
        success_item.setTextAlignment(Qt.AlignCenter)
        success_item.setFont(self.font)
        self.statistic_table.setItem(1, 0, success_item)

        error1_item = QTableWidgetItem("NEED RETEST")
        error1_item.setTextAlignment(Qt.AlignCenter)
        error1_item.setFont(self.font)
        self.statistic_table.setItem(2, 0, error1_item)

        error2_item = QTableWidgetItem("CONNECTION ERROR")
        error2_item.setTextAlignment(Qt.AlignCenter)
        error2_item.setFont(self.font)
        self.statistic_table.setItem(3, 0, error2_item)

        error3_item = QTableWidgetItem("FAILURE")
        error3_item.setTextAlignment(Qt.AlignCenter)
        error3_item.setFont(self.font)
        self.statistic_table.setItem(4, 0, error3_item)

        # Note Table
        self.s_name = QLabel("REPORT", self)
        self.s_name.setGeometry(1590 * self.width_rate, 606 * self.height_rate, 300 * self.width_rate, 60 * self.height_rate)
        self.s_name.setAlignment(Qt.AlignCenter)
        self.s_name.setStyleSheet("background-color:rgb(50, 130, 184);"
                                    "color: rgb(255, 255, 255);"
                                    "font: bold 14pt;")
        self.textBox = QPlainTextEdit(self)
        self.textBox.setGeometry(1590 * self.width_rate, 666 * self.height_rate, 300 * self.width_rate, 410 * self.height_rate)
        self.textBox.setFont(QFont('', int(14 / self.font_rate), QFont.Bold))
        
        # Exit Button
        self.exit_button = QPushButton(self)
        self.exit_pixmap = QPixmap(resource_path('data/icon/close.jpg')).scaled(100 * self.width_rate, 100 * self.width_rate, Qt.KeepAspectRatio)
        self.exit_icon = QIcon(self.exit_pixmap)
        self.exit_button.setIcon(self.exit_icon)
        self.exit_button.setIconSize(QSize(50, 50))
        self.exit_button.setGeometry(1878 * self.width_rate, -8 * self.height_rate, 50 * self.width_rate, 50 * self.height_rate)
        self.exit_button.setHidden(0)
        self.exit_button.setStyleSheet("border: none")
        self.exit_button.clicked.connect(self.close)

        # Create Thread
        self.main_thread = Thread()
        self.main_thread.progress.connect(self.main_process)
        self.demo_thread = Query()
        self.demo_thread.progress.connect(self.demo_query)
        self.send_thread = Send()
        self.send_thread.progress.connect(self.demo_send)
        
        # Run Thread
        self.setup_camera()
        self.main_thread.start()
        self.demo_thread.start()
        self.send_thread.start()
    
    # H??m stream CAMERA DETECT l??n giao di???n
    def update_detect_image(self, img):
        rgbImage = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgbImage.shape
        bytesPerLine = ch * w
        convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
        self.cam1.setPixmap(QPixmap.fromImage(convertToQtFormat))
    
    # H??m stream CAMERA CHECK l??n giao di???n
    def update_check_image(self, img):
        rgbImage = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgbImage.shape
        bytesPerLine = ch * w
        convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
        self.cam2.setPixmap(QPixmap.fromImage(convertToQtFormat))
    
    def update_statistic(self, data):
        self.number_tested += 1

        # Reset gi?? tr??? ?????m khi ki???m tra h???t linh ki???n
        if self.count == 42:
            self.count = 0
        
        # B??? qua khi kh??ng c?? linh ki???n trong m???ng d??? li???u
        while self.Controller.data[self.count] != 1:
            self.count += 1
        
        # C???p nh???t s??? li???u Ki???m tra
        tested = QTableWidgetItem("{}".format(self.number_tested) + " / {}".format(self.total))
        tested.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(0,1,tested)
        ratio_tested = QTableWidgetItem("{} %".format(int(self.number_tested / self.total * 100)))
        ratio_tested.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(0,2,ratio_tested)
        
        # L???y s??? li???u linh ki???n
        tray_idx = self.count // 21
        row = 6 - self.count % 21 % 7
        col = self.count % 21 // 7

        # Th??ng b??o ?????y
        if data == "1":
            self.number_success += 1
            self.tray[tray_idx].item(row,col).setBackground(QColor(67, 138, 94))
            self.textBox.appendPlainText("Linh Ki???n Tray {}".format(tray_idx+1) + " H??ng {}".format(row+1) + " C???t {}".format(col+1) + " Ho???t ?????ng T???t!\n")
        elif data == "0":
            self.number_error3 += 1
            self.tray[tray_idx].item(row,col).setBackground(QColor(232, 80, 91))
            self.textBox.appendPlainText("Linh Ki???n Tray {}".format(tray_idx+1) + " H??ng {}".format(row+1) + " C???t {}".format(col+1) + " B??? H???ng!\n")
        elif data == "-1":
            self.number_error1 += 1
            self.tray[tray_idx].item(row,col).setBackground(QColor(255, 255, 51))
            self.textBox.appendPlainText("Linh Ki???n Tray {}".format(tray_idx+1) + " H??ng {}".format(row+1) + " C???t {}".format(col+1) + " G???p L???i V??? Tr?? Tr??n Jig. ????? Ngh??? Ki???m Tra!\n")
        elif data == "404":
            self.number_error2 += 1
            self.tray[tray_idx].item(row,col).setBackground(QColor(255, 128, 0))
            self.textBox.appendPlainText("Linh Ki???n Tray {}".format(tray_idx+1) + " H??ng {}".format(row+1) + " C???t {}".format(col+1) + " G???p L???i K???t N???i V???i B??? Test. ????? Ngh??? Ki???m Tra!\n")

        # C???p nh???t s??? li???u
        success = QTableWidgetItem("{}".format(self.number_success) + " / {}".format(self.number_tested))
        success.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(1,1,success)
        ratio_success = QTableWidgetItem("{} %".format(int(self.number_success / self.number_tested * 100)))
        ratio_success.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(1,2,ratio_success)

        error1 = QTableWidgetItem("{}".format(self.number_error1) + " / {}".format(self.number_tested))
        error1.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(2,1,error1)
        ratio_error1 = QTableWidgetItem("{} %".format(int(self.number_error1 / self.number_tested * 100)))
        ratio_error1.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(2,2,ratio_error1)

        error2 = QTableWidgetItem("{}".format(self.number_error2) + " / {}".format(self.number_tested))
        error2.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(3,1,error2)
        ratio_error2 = QTableWidgetItem("{} %".format(int(self.number_error2 / self.number_tested * 100)))
        ratio_error2.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(3,2,ratio_error2)

        error3 = QTableWidgetItem("{}".format(self.number_error3) + " / {}".format(self.number_tested))
        error3.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(4,1,error3)
        ratio_error3 = QTableWidgetItem("{} %".format(int(self.number_error3 / self.number_tested * 100)))
        ratio_error3.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(4,2,ratio_error3)
        
        # Linh ki???n ki???m tra xong s??? x??a kh???i m???ng d??? li???u
        self.Controller.data[self.count] = 0
        self.count += 1

        # Ch??? l???nh
        self.delay = False
    
    # H??m Kh???i t???o gi?? tr??? cho B???ng s??? li???u
    def init_statistic(self):
        tested = QTableWidgetItem("{}".format(0) + " / {}".format(self.total))
        tested.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(0,1,tested)
        ratio_tested = QTableWidgetItem("{} %".format(0))
        ratio_tested.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(0,2,ratio_tested)

        success = QTableWidgetItem("{}".format(0) + " / {}".format(0))
        success.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(1,1,success)
        ratio_success = QTableWidgetItem("{} %".format(0))
        ratio_success.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(1,2,ratio_success)

        error1 = QTableWidgetItem("{}".format(0) + " / {}".format(0))
        error1.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(2,1,error1)
        ratio_error1 = QTableWidgetItem("{} %".format(0))
        ratio_error1.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(2,2,ratio_error1)

        error2 = QTableWidgetItem("{}".format(0) + " / {}".format(0))
        error2.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(3,1,error2)
        ratio_error2 = QTableWidgetItem("{} %".format(0))
        ratio_error2.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(3,2,ratio_error2)

        error3 = QTableWidgetItem("{}".format(0) + " / {}".format(0))
        error3.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(4,1,error3)
        ratio_error3 = QTableWidgetItem("{} %".format(0))
        ratio_error3.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(4,2,ratio_error3)

        # Ch??? l???nh
        self.delay = False

    def update_data(self, data):
        
        # Update Data to Table
        for c in range(42):
            self.tray[int(math.floor(c/21))].setItem(c % 7, int(math.floor(c/7) - math.floor(c/21) * 3), QTableWidgetItem())
            if bool(data[c]):
                self.tray[int(math.floor(c/21))].item(c % 7, int(math.floor(c/7) - math.floor(c/21) * 3)).setBackground(QColor(102, 102, 255))
                self.total += 1

        # Send Data to PLC
        self.Controller.data = data
        
    def updateTimer(self):
        cr_time = QTime.currentTime()
        time = cr_time.toString('hh:mm AP')
        self.time_label.setText(time)

    def main_process(self):
        if self.command == "Idle":
            # Ki???m tra xem ???? nh???n Camera Check ch??a
            if self.get_cap_detect == True:

                # Reset Main Variables
                self.total = 0
                self.number_tested = 0
                self.number_success = 0
                self.number_error1 = 0
                self.number_error2 = 0
                self.number_error3 = 0
                self.count = 0

                # Hi???n Video khi ch???
                # ret, image = self.cap_detect.read()
                image = cv2.imread(resource_path('data/demo/Detect/origin.jpg'))
                image = cv2.resize(image, (int(717 * self.width_rate), int(450 * self.height_rate)), interpolation = cv2.INTER_AREA) # Resize cho Giao di???n
                self.update_detect_image(image)
        elif self.command == "Detect":
            # Ki???m tra xem ???? nh???n Camera Check ch??a
            if self.get_cap_detect == True:
                
                # L???y d??? li???u t??? camera
                # ret, image = self.cap_detect.read()
                image = cv2.imread(resource_path('data/demo/Detect/origin.jpg'))
                resize_img = cv2.resize(image, (int(717 * self.width_rate), int(450 * self.height_rate)), interpolation = cv2.INTER_AREA) # Resize cho Giao di???n
                detect = Detect()

                # X??? l?? ???nh
                detect.image = cv2.resize(image, (1920, 1080), interpolation=cv2.INTER_AREA)
                detect.thresh()

                # Detect YES/NO
                result = detect.check(detect.crop_tray_1)
                result = np.append(result, detect.check(detect.crop_tray_2))
                self.update_detect_image(resize_img) # ????a ???nh l??n giao di???n

                # G???i k???t qu??? Detect YES/NO cho PLC v?? Table  
                self.update_data(result)
                self.init_statistic()
                self.command = "Wait"
            
        elif self.command == "Check":
            # Ki???m tra xem ???? nh???n Camera Check ch??a
            if self.get_cap_check == True:

                # Demo c?? CAMERA CHECK
                # ret, image = self.cap_check.read() # L???y d??? li???u t??? camera
                # resize_img = cv2.resize(image, (int(717 * self.width_rate), int(450 * self.height_rate)), interpolation = cv2.INTER_AREA) # Resize cho Giao di???n

                # Demo ???nh c?? s???n
                rand_list = os.listdir(resource_path('data/demo/Test/data'))
                folder = random.choice(rand_list)
                image = cv2.imread(resource_path('data/demo/Test/data/' + folder + '/image.jpg'))
                resize_img = cv2.resize(image, (int(717 * self.width_rate), int(450 * self.height_rate)), interpolation = cv2.INTER_AREA) # Resize cho Giao di???n

                self.update_check_image(resize_img) # ????a video l??n giao di???n
                
                # Khai b??o ki???m tra Jig
                CheckOnOK = CheckOn()
                CheckOnOK.image = image

                # N???u kh??ng c?? linh ki???n tr??n Jig
                if CheckOnOK.check(CheckOnOK.crop_image()) == 0:
                    self.Controller.command = "SOS"
                    self.Controller.sendCommand()
                    self.wait = False
                    self.command = "Wait"
                
                # N???u c?? linh ki???n tr??n Jig
                else:
                    # Ki???m tra l???ch
                    crop_list = checkAlign.crop_image(image)
                    mean = checkAlign.calc_mean_all(crop_list)
                    check = checkAlign.check(mean)
                    
                    # K???t qu??? tr??? v??? linh ki???n kh??ng l???ch
                    if check:
                        # Auto l??u d??? li???u ki???m th???
                        # self.count_file = open(resource_path('data/demo/Test/count.txt'), 'w')
                        # os.mkdir(resource_path('data/demo/Test/data/OK-{}'.format(self.count_current_ok)))
                        # cv2.imwrite('data/demo/Test/data/OK-{}/image.jpg'.format(self.count_current_ok), image)
                        # f = open(resource_path('data/demo/Test/data/OK-{}/mean.txt'.format(self.count_current_ok)), 'x')
                        # for i in range(4):
                        #     cv2.imwrite('data/demo/Test/data/OK-{}/'.format(self.count_current_ok) + 'crop_{}.jpg'.format(i+1), crop_list[i])
                        #     f.write(str(int(mean[i])) + " ")
                        # self.count_current_ok += 1
                        # self.count_file.write(str(self.count_current_ok) + "\n" + str(self.count_current_ng))
                        # self.count_file.close()

                        # ?????i State -> G???i State m???i cho PLC
                        self.Controller.command = "Grip-1"
                        self.wait = False

                    # K???t qu??? tr??? v??? linh ki???n l???ch
                    else:
                        # Auto l??u d??? li???u ki???m th???
                        # self.count_file = open(resource_path('data/demo/Test/count.txt'), 'w')
                        # os.mkdir(resource_path('data/demo/Test/data/NG-{}'.format(self.count_current_ng)))
                        # cv2.imwrite('data/demo/Test/data/NG-{}/image.jpg'.format(self.count_current_ng), image)
                        # f = open(resource_path('data/demo/Test/data/NG-{}/mean.txt'.format(self.count_current_ng)), 'x')
                        # for i in range(4):
                        #     cv2.imwrite('data/demo/Test/data/NG-{}/'.format(self.count_current_ng) + 'crop_{}.jpg'.format(i+1), crop_list[i])
                        #     f.write(str(int(mean[i])) + " ")
                        # self.count_current_ng += 1
                        # self.count_file.write(str(self.count_current_ok) + "\n" + str(self.count_current_ng))
                        # self.count_file.close()

                        # ?????i State -> G???i State m???i cho PLC
                        self.Controller.command = "Grip-0"
                        self.wait = False
                    self.command = "Wait"
                        
        # Nh???n k???t qu??? t??? PLC -> C???p nh???t b???ng s??? li???u -> G???i l???nh cho PLC ti???p t???c g???p linh ki???n m???i -> Ch??? tay g???p
        elif self.command == "1":
            self.update_statistic(self.command)
            self.command = "Wait"
        elif self.command == "0":
            self.update_statistic(self.command)
            self.command = "Wait"
        elif self.command == "-1":
            self.update_statistic(self.command)
            self.command = "Wait"
        elif self.command == "404":
            self.update_statistic(self.command)
            self.command = "Wait"

        # K???t th??c -> Xu???t ra th??ng b??o
        elif self.command == "Finish":
            if self.report_one_time:
                self.report_one_time = False
                QMessageBox.about(self, "Ki???m Tra Ho??n T???t", "???? Ki???m Tra " + str(self.total) + " linh ki???n!\n" + "C??n " + str(self.number_error1) + " linh ki???n c???n ki???m tra l???i!")
                self.command = "Stop"

        # D???ng kh???n c???p
        elif self.command == "SOS":
            if self.error_one_time:
                self.error_one_time = False
                QMessageBox.about(self, "D???ng Kh???n C???p", "Kh??ng th???y linh ki???n tr??n Jig!")
                self.command = "Stop"

    # Init Camera
    def setup_camera(self):
        # Khai b??o USB Camera Detect Config
        # self.cap_detect = cv2.VideoCapture(0) # Khai b??o USB Camera Detect Config
        # self.cap_detect.set(3, 1920)
        # self.cap_detect.set(4, 1080)
        self.get_cap_detect = True

        # Khai b??o USB Camera Check Config
        # self.cap_check = cv2.VideoCapture(1)
        # self.cap_check.set(3, 1280)
        # self.cap_check.set(4, 720)
        self.get_cap_check = True

    # Demo without PLC
    def demo_query(self):
        if self.command == "Wait":
            if self.demo_count <= self.total:
                if self.Controller.command == "Grip-0":
                        self.command = "-1"
                elif self.Controller.command == "Grip-1":
                        rand_list = ['1', '0', '404', '1', '1', '1', '1', '1']
                        self.command = random.choice(rand_list)
                if self.demo_count == self.total:
                    self.demo_count += 1
            else:
                self.command = "Finish"      

    def demo_send(self):
        if self.delay == False:
            self.Controller.command = "Grip"
            self.wait = False
            self.delay = True

    # Demo Press Key to change State
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.command = "Detect"
        elif event.key() == Qt.Key_Escape:
            self.command = "Idle"
            self.cam1.clear()
            self.cam2.clear()
            for c in range(42):
                self.tray[int(math.floor(c/21))].setItem(c % 7, int(math.floor(c/7) - math.floor(c/21) * 3), QTableWidgetItem())
                self.tray[int(math.floor(c/21))].item(c % 7, int(math.floor(c/7) - math.floor(c/21) * 3)).setBackground(QColor(192, 192, 192))
            self.statistic_table.clear()
            tested_item = QTableWidgetItem("TESTED")
            tested_item.setTextAlignment(Qt.AlignCenter)
            tested_item.setFont(self.font)
            self.statistic_table.setItem(0, 0, tested_item)

            success_item = QTableWidgetItem("SUCCESS")
            success_item.setTextAlignment(Qt.AlignCenter)
            success_item.setFont(self.font)
            self.statistic_table.setItem(1, 0, success_item)

            error1_item = QTableWidgetItem("NEED RETEST")
            error1_item.setTextAlignment(Qt.AlignCenter)
            error1_item.setFont(self.font)
            self.statistic_table.setItem(2, 0, error1_item)

            error2_item = QTableWidgetItem("CONNECTION ERROR")
            error2_item.setTextAlignment(Qt.AlignCenter)
            error2_item.setFont(self.font)
            self.statistic_table.setItem(3, 0, error2_item)

            error3_item = QTableWidgetItem("FAILURE")
            error3_item.setTextAlignment(Qt.AlignCenter)
            error3_item.setFont(self.font)
            self.statistic_table.setItem(4, 0, error3_item)
            self.textBox.clear()

            self.report_one_time = True
            self.error_one_time = True
            self.Controller.command = "Idle"
            self.demo_count = 0
            self.wait = False
        elif (event.key() == Qt.Key_F12) and (self.Controller.command == "Grip"):
            self.command = "Check"
            self.demo_count += 1

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())