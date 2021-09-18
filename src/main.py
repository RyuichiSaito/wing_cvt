# -*- coding: utf-8 -*-

#=====================
#
#
#
#
#=================
# Import
#=================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as pat
import matplotlib.patches as patches
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import math,sys,os,glob
from scipy.interpolate import UnivariateSpline
from sympy.geometry import Point, Circle, Triangle, Segment, Line
# ---------------------------
from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui 
from PyQt5.QtGui import * 
from PyQt5.QtCore import *

import configparser,math

import subprocess as sp

from test_wingprofile import WingProfile
from read_csv01 import autocad_csv
from output import out_put

import shapely.geometry as shp
from shapely.geometry import Polygon
#
#
#



# =======================================================================
#  WingProfile
#
#  説明:
#  ReadWing    input: file,Spar,skiprow   return: wing(shape 141*2)
#  ReadSection input: Part,file           return: none
#  OffsetRib   input: thin                return: Wing_itr(shape 141*2)
#  CanverLine  input: none                return: Canver(shape 141*2)
#
# =======================================================================






# ======================
#
# PyQt5でGUIをつくる
#
# =====================

# global変数の宣言
FoilList = []
tri_num = np.zeros(2)

class App(QMainWindow):

    def __init__(self, parent=None):
        super(App, self).__init__(parent)
        self.initUI()

    # -------------------
    # UI settings
    # -------------------
    def initUI(self):
        self.resize(1200, 700)
        self.move(300, 100)
        self.setWindowTitle('Airfoil Cam')

        # ------------
        # statusBar
        # ------------
        self.MenuBar()

        # ------------
        # Tab Widget
        # ------------
        self.table_widget = MyTableWidget(self)
        self.setCentralWidget(self.table_widget)

        self.show()

    def MenuBar(self):
        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)

        openFile = QAction('&翼型ファイル', self)
        openFile.setStatusTip('Reference WingProfile')
        openFile.triggered.connect(self.makewindow_1)
        
        openTool = QAction('&工作機械設定', self)
        openTool.triggered.connect(self.makewindow_2)

        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu(' &ファイル ')
        fileMenu.addAction(exitAction)
        
        settings = menubar.addMenu(' &設定 ')
        settings.addAction(openFile)
        settings.addAction(openTool)

    def makewindow_1(self):
        sub_window = SubWindow_1()
        sub_window.show()
        
        print('signal')
        #クラス　継承
        widget = MyTableWidget(self)
        widget.reload_combo()
        
    def makewindow_2(self):
        sub_window = SubWindow_2()
        sub_window.show()
        
        print('signal')
    

class SubWindow_1(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.read_config()
        
        # こいつがサブウィンドウの実体
        self.w = QDialog(parent)
        
        label_1 = QLabel("翼型保存フォルダ")
        self.txtFolder1 = QLabel(self.default_dir)
        self.txtFolder1.setFrameStyle(QFrame.Box | QFrame.Plain)
        btn = QPushButton('変更')
        btn.clicked.connect(self.wing_profile_dir)
        
        layout = QGridLayout()
        layout.addWidget(label_1, 0 ,1)
        layout.addWidget(self.txtFolder1,1,1)
        layout.addWidget(btn, 1,2)
        self.w.setLayout(layout)
    
    def read_config(self):
        # --------------------------------------------------
        # configparserの宣言とiniファイルの読み込み
        # --------------------------------------------------
        self.config_ini = configparser.ConfigParser()
        self.config_ini.read('config.ini', encoding='shift-jis')
        
        # --------------------------------------------------
        # config,iniから値取得
        # --------------------------------------------------
        # config.iniの値取得その1
        # FIXME 動きません

        self.default_dir = self.config_ini['DEFAULT']['wingprofile_dir']
        #self.default_dir = './AIRFOIL'
        # FoilListの作成
        self.Set_WingProfile(self.default_dir)
        
    # Select Airfoil File
    def wing_profile_dir(self):
        # ディレクトリの選択
        dirName = QFileDialog.getExistingDirectory(self,'Open file', os.getcwd())
        self.txtFolder1.setText(dirName)
        
        # config.ini の書き換え
        self.config_ini['DEFAULT']['WingProfile_dir'] = dirName
        with open('config.ini','w') as configfile:
            self.config_ini.write(configfile)
            
        # FoilListの再作成
        self.Set_WingProfile(dirName)

    # global変数に.dファイルを格納
    def Set_WingProfile(self,dirName):
        # Listに格納する
        global FoilList
        FoilList = glob.glob(dirName + '/*.d')
        
    def show(self):
        self.w.exec_()

class SubWindow_2(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.read_config()
        
        # こいつがサブウィンドウの実体
        self.w = QDialog(parent)
        
        label_1 = QLabel("工具登録")
        label_2 = QLabel("工具半径 [mm] :")
        self.toor_r = QDoubleSpinBox()
        self.toor_r.setValue(self.default_toor_r)
        btn = QPushButton('変更')
        btn.clicked.connect(self.change_config)
        
        layout = QGridLayout()
        layout.addWidget(label_1, 0 ,0)
        layout.addWidget(label_2, 1 ,0)
        layout.addWidget(self.toor_r ,1,2)
        layout.addWidget(btn, 1,3)
        self.w.setLayout(layout)
    
    def read_config(self):
        # --------------------------------------------------
        # configparserの宣言とiniファイルの読み込み
        # --------------------------------------------------
        self.config_ini = configparser.ConfigParser()
        self.config_ini.read('config.ini', encoding='shift-jis')
        
        # --------------------------------------------------
        # config,iniから値取得
        # --------------------------------------------------
        # config.iniの値取得その1
        self.default_toor_r = float(self.config_ini['DEFAULT']['Tool_rad'])
        
    def change_config(self):
        after_tool_r = self.toor_r.value()
        
        # config.ini の書き換え
        self.config_ini['DEFAULT']['Tool_rad'] = str(after_tool_r)
        with open('config.ini','w') as configfile:
            self.config_ini.write(configfile)        
        
    def show(self):
        self.w.exec_()



# =================
# Tab のレイアウト
#
# シグナルの説明
# signal_tab1 : Data_Tabがすべて埋まり,Set_Settingsが実行されたとき,1となる。
#　
#　
# =================
class MyTableWidget(QWidget):

    def __init__(self, parent):
        super(QWidget,self).__init__(parent)

        # シグナルを作成
        self.signal_tab1 = 0
        
        # read_configを呼ぶ
        sub_window = SubWindow_1()
        sub_window.read_config()
        
        self.layout = QVBoxLayout(self)

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()
        self.tab5 = QWidget()
        self.tabs.resize(600,500)

        # Add tabs
        self.tabs.addTab(self.tab1,"Data")
        self.tabs.addTab(self.tab2,"フィレット設定")
        self.tabs.addTab(self.tab3,"翼端")
        self.tabs.addTab(self.tab4,"Tab 4")
        self.tabs.addTab(self.tab5,"治具")
        # Create first tab

        self.Tab1Widget()
        self.Tab2Widget()
        self.Tab3Widget()
        self.Tab4Widget()
        self.Tab5Widget()

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)



    def Tab1Widget(self):
        self.tab1.layout = QVBoxLayout(self)

        # ----------------
        # Create Widgets
        # ----------------

        # Step1
        label1 = QLabel(" 翼根 ")
        label2 = QLabel(" 翼型 ")
        self.combo1 = QComboBox(self)
        self.combo1.addItem(" Select Airfoil (root)")
        
        label3 = QLabel(" CSV ")
        self.txtFolder_csv_1 = QLabel()
        self.txtFolder_csv_1.setFrameStyle(QFrame.Box | QFrame.Plain)
        btnFolder1 = QPushButton(' 参照 ')
        btnFolder1.clicked.connect(self.Read_Csv_1)

        label4 = QLabel(" 翼弦長 [mm] ")
        self.txtFolder_length_1 = QLineEdit()
        self.txtFolder_length_1.setValidator(QDoubleValidator())
        # Step2
        
        label5 = QLabel(" オフセット厚み [mm]")
        self.offset_thin_1 = QDoubleSpinBox()
        
        label6 = QLabel(" プランク厚み [mm]")
        self.gawa_thin_1 = QDoubleSpinBox()
        
        label7 = QLabel(" プランク開始位置")
        self.gawa_start_1 = QSpinBox()
        label8 = QLabel(" プランク終了位置")
        self.gawa_fin_1 = QSpinBox()
        
        btn_plot1 = QPushButton(' 描画 ')
        btn_plot1.clicked.connect(self.get_status_1)
            
        # plot 
        self.canvas1 = PlotCanvas(self)
        self.canvas1.axes.cla()

        self.canvas1.plot()


        # ------------------------------
        # end
        # ------------------------------
        label9 = QLabel(" 翼端 ")
        label10 = QLabel(" 翼型 ")
        self.combo2 = QComboBox(self)
        self.combo2.addItem(" Select Airfoil (root)")

        label11 = QLabel(" CSV ")
        self.txtFolder_csv_2 = QLabel()
        self.txtFolder_csv_2.setFrameStyle(QFrame.Box | QFrame.Plain)
        btnFolder2 = QPushButton(' 参照 ')
        btnFolder2.clicked.connect(self.Read_Csv_2)

        label12 = QLabel(" 翼弦長 [mm] ")
        self.txtFolder_length_2 = QLineEdit()
        # Step2
        
        label13 = QLabel(" オフセット厚み [mm]")
        self.offset_thin_2 = QDoubleSpinBox()
        
        label14 = QLabel(" プランク厚み [mm]")
        self.gawa_thin_2 = QDoubleSpinBox()
        
        label15 = QLabel(" プランク開始位置")
        self.gawa_start_2 = QSpinBox()
        label16 = QLabel(" プランク終了位置")
        self.gawa_fin_2 = QSpinBox()
        
        btn_plot2 = QPushButton(' 描画 ')
        btn_plot2.clicked.connect(self.get_status_2)
            
        
        # plot 
        self.canvas2 = PlotCanvas(self)
        self.canvas2.axes.cla()

        self.canvas2.plot()



        # Step3 : foillistが追加されたときの処理
        self.reload_combo()

        # ----------------
        # Setting layout
        # ----------------
        layout = QGridLayout()
        layout.setSpacing(15)

        ### root --------------
        layout.addWidget(label1, 0,0)
        
        layout.addWidget(label2, 1,0)
        layout.addWidget(self.combo1, 1,1,1,2)
        layout.addWidget(label3, 1,3)
        layout.addWidget(self.txtFolder_csv_1, 1,4,1,3)
        layout.addWidget(btnFolder1, 1,7)
        layout.addWidget(label4, 1,9)
        layout.addWidget(self.txtFolder_length_1, 1,10,1,2)
        
        layout.addWidget(label5, 2,0)
        layout.addWidget(self.offset_thin_1, 2,2)

        layout.addWidget(label6, 3,0)
        layout.addWidget(self.gawa_thin_1, 3,2)
        layout.addWidget(label7, 3,3)
        layout.addWidget(self.gawa_start_1, 3,4)
        layout.addWidget(label8, 3,5)
        layout.addWidget(self.gawa_fin_1, 3,6)
        layout.addWidget(btn_plot1, 3,11)

        layout.addWidget(self.canvas1, 4, 0, 2, 12)
        ### -------------------
        
        layout.addWidget(label9, 6,0)
        
        layout.addWidget(label10, 7,0)
        layout.addWidget(self.combo2, 7,1,1,2)
        layout.addWidget(label11, 7,3)
        layout.addWidget(self.txtFolder_csv_2, 7,4,1,3)
        layout.addWidget(btnFolder2, 7,7)
        layout.addWidget(label12, 7,9)
        layout.addWidget(self.txtFolder_length_2, 7,10,1,2)
        
        layout.addWidget(label13, 8,0)
        layout.addWidget(self.offset_thin_2, 8,2)

        layout.addWidget(label14, 9,0)
        layout.addWidget(self.gawa_thin_2, 9,2)
        layout.addWidget(label15, 9,3)
        layout.addWidget(self.gawa_start_2, 9,4)
        layout.addWidget(label16, 9,5)
        layout.addWidget(self.gawa_fin_2, 9,6)
        layout.addWidget(btn_plot2, 9,11)

        layout.addWidget(self.canvas2, 10, 0, 2, 12)
        
        self.tab1.setLayout(layout)


    # -------------
    # Tab 1 functions 
    # -------------
    def Read_Csv_1(self):
        # ディレクトリの選択
        self.csv_file_1 = QFileDialog.getOpenFileName(self,'Open file', os.getcwd())
        #print(self.csv_file)
        self.txtFolder_csv_1.setText(self.csv_file_1[0])
        
    def Read_Csv_2(self):
        # ディレクトリの選択
        self.csv_file_2 = QFileDialog.getOpenFileName(self,'Open file', os.getcwd())
        #print(self.csv_file)
        self.txtFolder_csv_2.setText(self.csv_file_2[0])

    def reload_combo(self):
        # Step3 : foillistが追加されたときの処理
        if len(FoilList) != 0:
            self.combo1.clear()
            self.combo2.clear()
            Foils = [os.path.basename(foil) for foil in FoilList]
            self.combo1.addItems(Foils)
            self.combo2.addItems(Foils)
        
    def get_status_1(self):
        # config.iniの値取得
        self.read_config()
        
        path = self.airfoil_dir + '/' + self.combo1.currentText()
        Csv = self.txtFolder_csv_1.text()
        self.CordLen_1 = float(self.txtFolder_length_1.text())
        offset = self.offset_thin_1.value()
        gawa = self.gawa_thin_1.value()
        gawa_start = self.gawa_start_1.value()
        gawa_fin = self.gawa_fin_1.value()
        
        # プラグラム実行
        wing = WingProfile()
        wing.ReadWing(path=path, CordLen=self.CordLen_1)
        wing.Offset(thin0=offset, thin1=gawa)
        wing.reOffset(gawa_start, gawa_fin)
        self.wing_Data_1,Wing_offseted = wing.return_para()
        
        csv = autocad_csv(self.wing_Data_1)
        csv.read_csv(file=Csv)
        csv.canver_spline()
        csv.keta()
        csv.center_points()
        csv.trianglar_hole()
        canver,self.keta_1,self.center_1,self.correct_y_1,self.tri_para_1 = csv.return_para()
        
        # global変数への代入 
        global tri_num
        tri_num[0] = self.tri_para_1.shape[0]
        # tableの更新
        self.SetTable_2()
        
        # plot 
        self.canvas1.plot_wing(self.wing_Data_1,Wing_offseted,canver,self.keta_1,self.center_1,self.correct_y_1)
        self.canvas1_tri.plot_wing(self.wing_Data_1,Wing_offseted,canver,self.keta_1,self.center_1,self.correct_y_1)
        
        self.wing_Data_1 = Wing_offseted
        print('fin')
        
    def get_status_2(self):
        # config.iniの値取得
        self.read_config()
        
        path = self.airfoil_dir + '/' + self.combo2.currentText()
        Csv = self.txtFolder_csv_2.text()
        self.CordLen_2 = float(self.txtFolder_length_2.text())
        offset = self.offset_thin_2.value()
        gawa = self.gawa_thin_2.value()
        gawa_start = self.gawa_start_2.value()
        gawa_fin = self.gawa_fin_2.value()
        
        # プラグラム実行
        wing = WingProfile()
        wing.ReadWing(path=path, CordLen=self.CordLen_2)
        wing.Offset(thin0=offset, thin1=gawa)
        wing.reOffset(gawa_start, gawa_fin)
        self.wing_Data_2,Wing_offseted = wing.return_para()
        
        csv = autocad_csv(self.wing_Data_2)
        csv.read_csv(file=Csv)
        csv.canver_spline()
        csv.keta()
        csv.center_points()
        csv.trianglar_hole()
        canver,self.keta_2,self.center_2,self.correct_y_2,self.tri_para_2 = csv.return_para()
        
        # global変数への代入 
        global tri_num
        tri_num[1] = self.tri_para_2.shape[0]
        
        # plot 
        self.canvas2.plot_wing(self.wing_Data_2,Wing_offseted,canver,self.keta_2,self.center_2,self.correct_y_2)
        self.canvas2_tri.plot_wing(self.wing_Data_2,Wing_offseted,canver,self.keta_2,self.center_2,self.correct_y_2)
        
        self.wing_Data_2 = Wing_offseted
        print('fin')
        
    def read_config(self):
        # --------------------------------------------------
        # configparserの宣言とiniファイルの読み込み
        # --------------------------------------------------
        self.config_ini = configparser.ConfigParser()
        self.config_ini.read('config.ini', encoding='shift-jis')
        self.airfoil_dir = self.config_ini['DEFAULT']['WingProfile_dir']
        self.tool_r = float(self.config_ini['DEFAULT']['tool_rad'])
        print(self.tool_r)
        
# ===========================================
#  以下 Tab2
#
# ===========================================

    # -------------
    # Set Tab2
    #
    # -------------

    def Tab2Widget(self):

        self.circle_para = []

        self.tab2.layout = QVBoxLayout(self)

        # ----------------
        # Create Widgets
        # ----------------
        
        self.canvas1_tri = PlotCanvas(self)
        self.canvas1_tri.axes.cla()
        self.canvas1_tri.plot()
        
        self.canvas2_tri = PlotCanvas(self)
        self.canvas2_tri.axes.cla()
        self.canvas2_tri.plot()


        label1 = QLabel(" フィレット半径 ")
        label2 = QLabel("     以下にフィレット半径を入力[mm]  　　左の三角から順に，表の1，2，3... に入力してください.")
        
        label3 = QLabel(" 翼端 ")
        label4 = QLabel(" 翼根 ")
        btnFolder1 = QPushButton('描画')
        btnFolder1.clicked.connect(self.get_table_data_2)


        # ----------------
        # Setting layout
        # ----------------
        self.layout_tab2 = QGridLayout()
        
        self.layout_tab2.addWidget(label1, 0, 0)
        self.layout_tab2.addWidget(label2, 1, 0)
        
        self.layout_tab2.addWidget(self.canvas1_tri, 5, 0, 2, 5)
        self.layout_tab2.addWidget(self.canvas2_tri, 8, 0, 2, 5)

        self.layout_tab2.addWidget(label3, 4, 0)
        self.layout_tab2.addWidget(label4, 7, 0)
       
        # -------------------
        # Table Widget
        # -------------------
        self.SetTable_2()
        self.SetTable_3()

        self.layout_tab2.addWidget(btnFolder1, 3, 0)


        self.tab2.setLayout(self.layout_tab2)

    def SetTable_2(self):
        # -------------------
        # Table Widget
        # -------------------
        self.table_data1 = np.zeros((1,int(tri_num[0])))
        
        self.table_1 = QTableView()
        self.TableModel_1 = MyTableModel(self.table_data1)
        self.table_1.setModel(self.TableModel_1)
        self.table_1.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.layout_tab2.addWidget(self.table_1, 2, 0, 1, 5)
        
    def get_table_data_2(self):
        table_data = self.TableModel_1.current_data()
        self.canvas1_tri.plot_circle(table_data,self.tool_r)
        self.canvas2_tri.plot_circle(table_data,self.tool_r)    
        
        self.table_tab2 = table_data[0]
        
    def SetTable_3(self):
        # -------------------
        # Table Widget
        # -------------------
        self.table_data2 = np.zeros((1,int(tri_num[1])))
        
        self.table_2 = QTableView()
        self.TableModel_2 = MyTableModel(self.table_data1)
        self.table_2.setModel(self.TableModel_2)
        self.table_2.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        #self.layout_tab2.addWidget(self.table_2, 6, 0, 1, 5)
        

        

# ===========================================
#  以下 Tab3
#
# ===========================================

    # -------------
    # Set Tab3
    #
    # -------------

    def Tab3Widget(self):
        self.circle_para_ = []

        self.tab3.layout = QVBoxLayout(self)

        # ----------------
        # Create Widgets
        # ----------------

        
        self.canvas_ = PlotCanvas(self)
        self.canvas_.axes.cla()

        self.canvas_.plot()

        #self.canvas.axes.cla()

        label1 = QLabel(" リブ枚数 ")
        self.rib_n = QSpinBox()
        
        btnFolder1 = QPushButton(' Set ')
        btnFolder1.clicked.connect(self.CreateTable_rib)
        
        label2 = QLabel(" リブ位置 ↓ ")
        label3 = QLabel("     リブ位置を以下に入力[mm]    0を翼根とする． ")
        
        btnFolder2 = QPushButton(' 描画 ')
        btnFolder2.clicked.connect(self.plot_sample)

        # ----------------
        # Setting layout
        # ----------------
        self.layout_tab3 = QGridLayout()

        self.layout_tab3.addWidget(label1, 0, 0)
        self.layout_tab3.addWidget(self.rib_n, 0, 1)
        self.layout_tab3.addWidget(btnFolder1, 0, 2)
        
        self.CreateTable_rib()
        
        self.layout_tab3.addWidget(label2, 1, 0)
        self.layout_tab3.addWidget(label3, 2, 0)

        self.layout_tab3.addWidget(btnFolder2, 4, 0)
        self.layout_tab3.addWidget(self.canvas_, 5, 0, 2, 4)

        self.tab3.setLayout(self.layout_tab3)

    def CreateTable_rib(self):
        n = self.rib_n.value()
        # -------------------
        # Table Widget
        # -------------------
        self.data_rib = np.zeros((1,n))
        self.table_rib = QTableView()
        self.TableModel_rib = MyTableModel(self.data_rib)
        self.table_rib.setModel(self.TableModel_rib)
        self.layout_tab3.addWidget(self.table_rib, 3, 0, 1, 4)

    def plot_sample(self):
        self.table_data = self.TableModel_rib.current_data()
        self.canvas_.plot_shape(self.CordLen_1,self.CordLen_2,self.keta_1,self.keta_2,self.table_data)


    def Tab4Widget(self):
        
        self.tab4.layout = QVBoxLayout(self)

        label1 = QLabel("　ファイル作成 : ")
        btnFolder1 = QPushButton('ok')
        btnFolder1.clicked.connect(self.create_dfx)
        
        label2 = QLabel(" Cam実行　: ")
        btnFolder2 = QPushButton('ok')

        
        # ----------------
        # Setting layout
        # ----------------
        layout = QGridLayout()



        layout.addWidget(label1, 0, 0)
        layout.addWidget(btnFolder1, 0, 1)

        layout.addWidget(label2, 1, 0)
        layout.addWidget(btnFolder2, 1, 1)

        self.tab4.setLayout(layout)

    def create_dfx(self):
        points_1, keta_1 = self.canvas1_tri.return_para()
        points_2, keta_2 = self.canvas2_tri.return_para()
        
        out = out_put(self.wing_Data_1,self.wing_Data_2,\
                      points_1,points_2, keta_1,keta_2,\
                      self.table_data)

        out.wing_outer()
        out.wing_corner()
        out.wing_circle(self.correct_y_1,self.correct_y_2)
        out.print_data()
        out.out_dxf(self.table_tab2)
        out.out_dxf_onefile(self.table_tab2)

    def Tab5Widget(self):
        
        self.tab5.layout = QVBoxLayout(self)

        label1 = QLabel("　ファイル作成 : ")
        btnFolder1 = QPushButton('ok')
        btnFolder1.clicked.connect(self.create_dfx)
        
        label2 = QLabel(" Cam実行　: ")
        btnFolder2 = QPushButton('ok')

        
        # ----------------
        # Setting layout
        # ----------------
        layout = QGridLayout()



        layout.addWidget(label1, 0, 0)
        layout.addWidget(btnFolder1, 0, 1)

        layout.addWidget(label2, 1, 0)
        layout.addWidget(btnFolder2, 1, 1)

        self.tab5.setLayout(layout)
    
        
# =================================================================
#
#           end GUI        
#
# =================================================================        


# =============
# 
# Table 
#
# =============

class MyTableModel(QAbstractTableModel):
    def __init__(self, list, headers = [], parent = None):
        QAbstractTableModel.__init__(self, parent)
        self.list = list.tolist()
        self.headers = headers

    def rowCount(self, parent):
        return len(self.list)

    def columnCount(self, parent):
        return len(self.list[0])

    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def data(self, index, role):
        if role == Qt.EditRole:
            row = index.row()
            column = index.column()
            return self.list[row][column]

        if role == Qt.DisplayRole:
            row = index.row()
            column = index.column()
            value = self.list[row][column]
            return value

    def setData(self, index, value, role = Qt.EditRole):
        row = index.row()
        column = index.column()
        if role == Qt.EditRole:
            self.list[row][column] = float(value)
            self.dataChanged.emit(index, index)
            return True
        else:
            return False

    #指定セルのデータを取得
    def get_data(self, index):
        row = index.row()
        column = index.column()
        value  = float(self._weight_data[row][column])
        return value,row

    def current_data(self):
        return list(self.list)





# ========================
# グラフの描画クラス
#
# ========================
class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None, width=25, height=10, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_aspect('equal')
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        plt.rcParams['xtick.direction'] = 'in'
        plt.rcParams['ytick.direction'] = 'in'

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def plot(self):
        self.axes.cla()
        self.axes = self.fig.add_subplot(111)
        self.draw()

        print("1111")

    def plot_wing(self, wing_Data,Wing_offseted,canver,keta,center,correct_y):
        self.wing_Data = wing_Data
        self.Wing_offseted = Wing_offseted
        self.keta = keta
        self.center = center
        self.canver = canver
        self.correct_y = correct_y
        
        self.axes.cla()
        self.axes.plot(wing_Data[:,0],wing_Data[:,1],alpha=.5)
        self.axes.plot(Wing_offseted[:,0],Wing_offseted[:,1])
        self.axes.plot(canver[0],canver[1],alpha=.5)
        
        for p in center:
            p1 = (p[0], p[1]-correct_y)
            p2 = (p[2],p[3]-correct_y)
            p3 = (p[4],p[5]-correct_y)
            
            t = (p1, p2, p3)
            self.axes.add_patch(plt.Polygon(t,alpha=.5))
            
        keta_circle = plt.Circle((keta[0], keta[1]-correct_y), keta[3]/2, alpha =.7)
        self.axes.add_artist(keta_circle)
        self.draw()
        print("plot_wing")

    def plot_circle(self,corner,tool_r):
        
        self.axes.cla()
        self.axes.plot(self.wing_Data[:,0],self.wing_Data[:,1],alpha=.5)
        self.axes.plot(self.Wing_offseted[:,0],self.Wing_offseted[:,1])
        self.axes.plot(self.canver[0],self.canver[1],alpha=.5)
        
        keta_circle = plt.Circle((self.keta[0], self.keta[1]-self.correct_y), self.keta[3]/2, alpha =.7)
        self.axes.add_artist(keta_circle)
            
        
        def getXY(r, deg, xy):
            x,y = xy[0],xy[1]
            rad = math.radians(deg)
            x_re = x + r* math.cos(rad)
            y_re = y + r* math.sin(rad)
            return x_re,y_re
        
        def get_corner(p1,p2,ls,point,corner_r):
            w_x = []
            w_y = []
            if p1 > p2:
                p2 += 360
            rad = np.arange(p1, p2, 0.2)
            for d in rad:
                x,y = getXY(corner_r,d,ls)
                w_x.append(x)
                w_y.append(y)
            point.append((w_x[0],w_y[0]))
            point.append((w_x[-1],w_y[-1]))
                
            return w_x,w_y
        
        """
        ループスタート
        """
        j = 0
        self.points = []
        for p in self.center:
            p1 = (p[0], p[1]-self.correct_y)
            p2 = (p[2],p[3]-self.correct_y)
            p3 = (p[4],p[5]-self.correct_y)
            t = (p1, p2, p3)
            self.axes.add_patch(plt.Polygon(t,alpha=.5))
            
            tri = shp.Polygon(t)
            tri = tri.buffer(-tool_r)
            corner_r = float(corner[0][j])
            j += 1
            tri_1 = tri.buffer(-corner_r) 
            
            ls = list(tri_1.exterior.coords)
            
            corner_point = []
            for i in range(3):
                p_deg = math.atan2(ls[i][0]-ls[i+1][0],ls[i][1]-ls[i+1][1]) *180 /math.pi
                if p_deg < 0:
                    p_deg += 360
                corner_point.append(-p_deg)
            
            point = []
            w_x1,w_y1 = get_corner(corner_point[0],corner_point[2],ls[0],point,corner_r)
            w_x2,w_y2 = get_corner(corner_point[1],corner_point[0],ls[1],point,corner_r)
            w_x3,w_y3 = get_corner(corner_point[2],corner_point[1],ls[2],point,corner_r)
            
            self.points.append(point)
            #以下plot
            self.axes.plot(w_x1,w_y1,color='k')
            self.axes.plot(w_x2,w_y2,color='k')
            self.axes.plot(w_x3,w_y3,color='k')
            
            for i in range(3):
                self.axes.plot(*zip(point[i],point[i+3]),color='k')
            
        self.draw()
        print('fin_corner')
        
    def plot_shape(self,cord1,cord2,keta1,keta2,ls):
        y1,y2 = -keta1[0],-keta2[0]
        y1_p,y2_p = y1+cord1, y2+cord2
        keta_length = ls[0][-1]
        
        p = ((0, y1), (0, y1_p), (keta_length, y2_p), (keta_length, y2))
        self.axes.cla()
        self.axes.add_patch(plt.Polygon(p,alpha=.5))
        
        for x in ls[0]:
            l_minus = (y2-y1)/keta_length * x + y1
            l_plus = (y2_p-y1_p)/keta_length* x + y1_p
            self.axes.plot((x,x),(l_minus,l_plus))
        
        self.draw()

        
    def clear(self):
        self.axes.cla()
        self.draw()

    def return_para(self):
        return self.points, self.keta


class Form(QDialog):
	def __init__(self, parent=None):
		super(Form, self).__init__(parent)
		self.ui = Ui_Form()
		self.ui.setupUi(self)
		self.l = QtWidgets.QVBoxLayout(self.ui.widget)

	def show_graph(self):
		sc = MyStaticMplCanvas(self.ui.widget, width=5, height=4, dpi=100)
		self.l.addWidget(sc)


# =================
#
# output class
#
# =================

class outputData():

    def Paramata(self):
        pass



def main():

    app = QApplication(sys.argv)
    ew = App()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
