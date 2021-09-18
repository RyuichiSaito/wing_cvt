# -*- coding: utf-8 -*-
#=================
# Import
#=================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import shapely.geometry as shp
from scipy.interpolate import UnivariateSpline

# ---------------------------
#
#
# =======================================================================
#  WingProfile
#
#  説明:
#  ReadWing    input: path, CordLen       return: wing(shape 141*2)
#  Offset      input: thin0, thin1        return: afpolypts_0(shape 141*2),afpolypts_1(shape 141*2),
#                                                 Canver(shape 141*2)
#  reOffset    input: n_up,n_down         return: afpoly_re(shape 143*2)
#  plotWing    input: none                return: none
#
# =======================================================================


class WingProfile():

    def __init__(self):
        super().__init__()


    # =====================================
    # 翼型ファイルを開いてnumpyで扱える形に変換する
    # =====================================
    def ReadWing(self,path,CordLen):
        #path = './airfoil/' + file
        df_wing = pd.read_table(path,names=['x','y'],delim_whitespace=True,skiprows=2)


        # ---------------------
        #　Pandas to numpy.array
        # 例 : d+03 →　10^3　
        # ---------------------
        wing = []
        for i in range (df_wing.shape[0]):
            wingReal = []
            for j in range(df_wing.shape[1]):
                wing_d = df_wing.iloc[i][j]

                wingInt = float(wing_d[:-4])
                tenE = int(wing_d[-3:])
                wing_d = wingInt * CordLen * 10**tenE

                wingReal.append(wing_d)
            wing.append(wingReal)

        self.Wing = np.array(wing)
        #return self.Wing

    def Offset(self,thin0,thin1):
        # =====================
        # offset rib
        # 
        # thin0 :　通常部分のオフセット量
        # thin1 : プランク部分のオフセット量
        #
        # =====================
        
        afpoly = shp.Polygon(self.Wing)
        afpoly_0 = afpoly.buffer(-1*thin0)  # Inward offset
        afpoly_1 = afpoly.buffer(-1*thin1)  # Inward offset
        
        # Turn polygon points into numpy arrays for plotting
        self.afpolypts = np.array(afpoly.exterior)
        self.afpolypts_0 = np.array(afpoly_0.exterior)
        self.afpolypts_1 = np.array(afpoly_1.exterior)
        
        # =======================
        # make canver_line
        #
        # =======================
        
        x,y = self.Wing[:,0], self.Wing[:,1]
        # -----------------------
        # Step1
        # B-Spline interpolate
        # -----------------------
        WingUp = UnivariateSpline(x[:71],y[:71])
        WingDown = UnivariateSpline(np.fliplr([x[71:]])[0], np.fliplr([y[71:]])[0])

        xi = np.arange(0,max(x),0.1)
        yi = 0.5*(WingUp(xi)+WingDown(xi))
        self.Canver = [xi, yi]
        
        #return self.afpolypts_0,self.afpolypts_1,self.Canver
    
    def reOffset(self,n_up,n_down):
        # ========================
        #
        # n_up : 上側のプランク位置
        #　n_down :　下側のプランク位置
        #
        # ========================
        
        #print(self.afpolypts_1[:,1])
        #TODO :　頂点のindexを探索したい　∴上と下の分かれ目
    
        # 上側の探索処理
        a1 = self.afpolypts_0[n_up,0]
        up = (abs(self.afpolypts_1[:,0] - a1)).tolist()
        up = up.index(min(up))
    
        # 下側の探索処理
        a2 = self.afpolypts_0[n_down,0]
        down = (abs(self.afpolypts_1[:,0] - a2)).tolist()
        down = down.index(min(down))
        
        print(up,down)
        afpoly_0 = self.afpolypts_0[:n_up,:]
        afpoly_1 = self.afpolypts_1[up-1:down+1,:]
        afpoly_2 = self.afpolypts_0[n_down:,:]

        self.afpoly_re =np.concatenate([afpoly_0,afpoly_1,afpoly_2])
        #print (*self.afpoly_re.T)
        
    def plot_wing(self):
        
        #plt.plot(self.Wing[:,0],self.Wing[:,1])
        fig = plt.figure(figsize=(20,4))
        plt.plot(*self.afpolypts.T, color='black')
        #plt.plot(*self.afpolypts_0.T, color='green')
        #plt.plot(*self.afpolypts_1.T, color='green')
        
        plt.plot(*self.afpoly_re.T, color='green')
        plt.plot(self.Canver[0], self.Canver[1])
        plt.axis('equal')

        plt.show()

    def return_para(self):
        return self.Wing,self.afpoly_re

def main():
    path = 'dae21.d'
    CordLen = 200
    
    wing = WingProfile()
    wing.ReadWing(path=path, CordLen=CordLen)
    wing.Offset(thin0=1, thin1=2)
    wing.reOffset(40,86)
    
    wing.plot_wing()
    
if __name__ == '__main__':
    main()