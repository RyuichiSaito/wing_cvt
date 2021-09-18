# -*- coding: utf-8 -*-
from test_wingprofile import WingProfile
import pandas as pd
import numpy as np
from scipy.interpolate import UnivariateSpline

import matplotlib.pyplot as plt
import matplotlib.patches as pat
from sympy.geometry import Point, Circle, Triangle, Segment, Line

class autocad_csv():
    
    def __init__(self,wing):
        self.wing = wing
    
    def read_csv(self, file):
        self.df_csv = pd.read_csv(file)
        self.df_new = self.df_csv[['名前','印刷スタイル','色','長さ','中心 X','中心 Y','直径','半径',\
                     '角度','始点 X','始点 Y','終点 X','終点 Y','増減 X','増減 Y']]
    
    def read_wing(self, dat, cord_length):
        df_wing = pd.read_table(dat, names=['x','y'], delim_whitespace=True,skiprows=2)
        
        wing = []
        for i in range (df_wing.shape[0]):
            wingReal = []
            for j in range(df_wing.shape[1]):
                wing_d = df_wing.iloc[i][j]
    
                wingInt = float(wing_d[:-4])
                tenE = int(wing_d[-3:])
                wing_d = wingInt * cord_length * 10**tenE
    
                wingReal.append(wing_d)
            wing.append(wingReal)
        
        self.wing = np.array(wing)


    # canver_spline 
    # キャンバーラインのスプライン補完を返す。　(B-spline)
    # self : spline(イテレータ), spine（2d array）
    
    def canver_spline(self):
        x,y = self.wing[:,0], self.wing[:,1]
        
        WingUp = UnivariateSpline(x[:71],y[:71])
        WingDown = UnivariateSpline(np.fliplr([x[71:]])[0], np.fliplr([y[71:]])[0])
    
        xi = np.arange(0,max(x),0.1)
        yi = 0.5*(WingUp(xi)+WingDown(xi))
        
        self.canver_spline = UnivariateSpline(xi,yi)
        self.Canver = [xi, yi]    
        
    
    # ------------------------
    # keta
    # 桁のプロファイルを読む　
    # XXX:円が一つの場合しか想定していない。
    #　TODO:他の肉抜きが円である場合の，処理を書く。
    # ------------------------- 
    
    def keta(self):
        df_cir = self.df_new.dropna(subset=['直径'])
        self.keta = df_cir[['中心 X','中心 Y','直径']].values.tolist()[0]
        self.keta.append(float(self.canver_spline(self.keta[0])))
        self.correct_y = self.keta[1] - self.keta[3]
        
        
        # keta  : x, y, 計算値y, 直径

    
    # ---------------------------
    # center_points
    # 縦の直線とキャンバーラインとの交点を計算する。
    #　!Caution! : 縦線は90度でないといけない
    # self :　df_point , point
    # --------------------------------
    
    def center_points(self):
        df_point = self.df_new[(self.df_csv['名前'] == '線分') & (self.df_csv['角度'] == 90)]
        self.df_point = np.array(df_point['始点 X'].T)
        self.point = [float(self.canver_spline(p)) + self.correct_y for p in self.df_point]
    
        
    # --------------------------------
    # trianglar_hole
    # 三角形の肉抜きの位置を計算する。
    #　!Caution! : 色は黄色でないといけない。
    #
    # TODO: '色==yellow' 以外でも動くようにする。
    # --------------------------------
    
    def trianglar_hole(self):
        df_tri = self.df_new[(self.df_csv['名前'] =='線分') & (self.df_csv['色'] == 'yellow')][['始点 X','始点 Y','終点 X','終点 Y']]
        df_tri = df_tri.drop_duplicates()
        
        num_tri = int(df_tri.shape[0]/3) 
        tri_points = np.zeros((num_tri,6))
        #print(tri_points.shape)
        
        for i in range(num_tri):
            tri_points[i,:4] = df_tri.iloc[0,:]
            
            x = df_tri.iloc[0,0]
            df_tri = df_tri.drop(df_tri.index[0])
            
            ## 
            if len(df_tri[df_tri['始点 X'] == x]) == 1:
                dxy = df_tri[df_tri['始点 X'] == x].iloc[0,2:]
                tri_points[i,4:] = dxy
                df_tri = df_tri[df_tri['始点 X'] != x]
                dx = dxy[0]
                
                # もう一点を消す。---------------------------------
                if len(df_tri[df_tri['始点 X'] == dx]) == 1:
                    df_tri = df_tri[df_tri['始点 X'] != dx]
                elif len(df_tri[df_tri['終点 X'] == dx]) == 1:
                    df_tri =  df_tri[df_tri['終点 X'] != dx]
                # -------------------------------------------------------
                
            ## 
            elif len(df_tri[df_tri['終点 X'] == x]) == 1:
                dxy = df_tri[df_tri['終点 X'] == x].iloc[0,:2]
                tri_points[i,4:] = dxy
                df_tri =  df_tri[df_tri['終点 X'] != x]
                dx = dxy[0]
                
                # もう一点を消す。---------------------------------
                if len(df_tri[df_tri['始点 X'] == dx]) == 1:
                    df_tri = df_tri[df_tri['始点 X'] != dx]
                elif len(df_tri[df_tri['終点 X'] == dx]) == 1:
                    df_tri =  df_tri[df_tri['終点 X'] != dx]
                # -------------------------------------------------------
                
        # 3角形の3点を取り出す。
        #　平均をとり、向きと対応する点を計算する。
        # 
        
        tri_ave = ((tri_points[:,0]+tri_points[:,2]+tri_points[:,4])/3, (tri_points[:,1]+tri_points[:,3]+tri_points[:,5])/3)

        def getNearestValue(list, num):
            idx = np.abs(np.array(list) - num).argmin()
            return list[idx]
        
        center = []
        for x in tri_ave[0]:
            center.append(getNearestValue(self.df_point,x))
        
        center_y = [float(self.canver_spline(p)) + self.correct_y for p in center]
        center = [center, center_y]
        center_p = np.array(center).T
        #print(center_p.shape)
        
        center = np.concatenate([tri_points, center_p],1)
        
        self.center = center
        #print(center.shape)
        
        tx,ty = center[:,6],center[:,7]
        
        #最終出力
        tri_para = []
        tri_para.append(tx)
        tri_para.append(ty)
        
        for i in range(3):
            px,py = tri_points[:,2*(i)],tri_points[:,2*(i)+1]
            
            #距離
            tl = np.sqrt((px-tx)**2 + (py-ty)**2)
        
            #偏角
            arg = (px - tx) +1j*(py - ty)
            ang = np.angle(arg)*180/np.pi
            ang_p = []
            for a in ang:
                if(0<=a<60):
                    pass
                elif(60<=a<120): #-alpha 
                    a = -a + 60
                elif (120<= a <= 180):
                    a -= 120
                elif (-60<= a < 0): #-alpha
                    pass
                elif(-120<=a<-60):
                    a += 120
                elif(-180 <= a < -120): #-alpha
                    a += 120 
                ang_p.append(np.round(a, decimals=3))
            
        
            tri_para.append(tl)
            tri_para.append(ang_p)
        
        # to nparray    
        tri_para = np.array(tri_para)
        

        # sortして渡す。
        # shape 8*三角形の個数
        #
        # [[x座標,y座標,頂点までの距離×3,偏角×3] ×個数]
        #
        self.center_sorted = center[np.argsort(center[:,0])]
        self.tri_para_sorted = tri_para[np.argsort(tri_para[:,0])]
        
        # debag
        #print(self.tri_para_sorted.T)
        #print(self.center)
        #
        
        ##print(self.center)
        ##print(self.center_sorted)
    def return_para(self):
        #
        # 必要データを返すメソッド  
        #
        
        return self.Canver,self.keta,self.center_sorted,self.correct_y,self.tri_para_sorted.T
        
class plot():
    
    def __init__(self,wing,wing_offset,canver,keta,center,correct_y):
        self.wing = wing
        self.Wing_offseted = wing_offset
        self.canver = canver
        self.keta = keta
        self.center = center
        self.correct_y = correct_y
        print(wing_offset.shape)
        
    def plot(self):
        fig = plt.figure(figsize=(25,5))
        ax = fig.add_subplot(111)
        
        plt.plot(self.wing[:,0],self.wing[:,1])
        plt.plot(self.Wing_offseted[:,0],self.Wing_offseted[:,1])
        plt.plot(self.canver[0],self.canver[1])
        
        
        for p in self.center:
            #print(p)
            p1 = Point(p[0], p[1]-self.correct_y)
            p2 = Point(p[2],p[3]-self.correct_y)
            p3 = Point(p[4],p[5]-self.correct_y)
            
            pc = Point(p[6],p[7]-self.correct_y)
            t = Triangle(p1, p2, p3)
        
            ax.add_patch(plt.Polygon(t.vertices,alpha=.5))
            ax.plot(*zip(p1, pc))
            
        #plt.scatter(tri_ave[0],tri_ave[1],color='r')
        
        keta_circle = plt.Circle((self.keta[0],self.keta[1]-self.correct_y), self.keta[3]/2, alpha =.7)
        ax.add_artist(keta_circle)
        
        #plt.scatter(df_point,point,color='g')
        #plt.scatter(self.center[:2,6],self.center[:2,7],color='k')
        
        
        plt.show()

        

def main():
    path = 'fx76mp140.d'
    CordLen = 899.20
    
    wing = WingProfile()
    wing.ReadWing(path=path, CordLen=CordLen)
    wing.Offset(thin0=2, thin1=5)
    wing.reOffset(45,95)
    wing_Data,Wing_offseted = wing.return_para()
    
    #wing.plot_wing()
    
    csv = autocad_csv(wing_Data)
    csv.read_csv(file='3m_data1.csv')
    csv.canver_spline()
    csv.keta()
    csv.center_points()
    csv.trianglar_hole()
    canver,keta,center,correct_y,tri_para = csv.return_para()
    
    #print(tri_para)
    plot_wing = plot(wing_Data,Wing_offseted,canver,keta,center,correct_y)
    plot_wing.plot()
    
if __name__ == '__main__':
    main()