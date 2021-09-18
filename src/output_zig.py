# -*- coding: utf-8 -*-
import numpy as np
import os

class out_put():
    
    def __init__(self, wing_1,wing_2, points_1,points_2, keta_1,keta_2, table):
        self.wing_1 = wing_1
        self.points_1 = points_1
        self.keta_1 = keta_1
        
        self.wing_2 = wing_2
        self.points_2 = points_2
        self.keta_2 = keta_2
        
        self.table = table[0]
        print(table)
    
    def lerp(self, cord_p,a,b):
        """
        x : tableの値 shape:1*n
        a : 補間する x or y　の最初の値
        b :　補間する x or y　の最後の値
        """
        cord_root, cord_end = self.table[0], self.table[-1]
        ans = a + (b - a)/(cord_end - cord_root) * (cord_p - cord_root)
        return ans
    
    def wing_outer(self):
        # 中心座標
        cx_1, cy_1 = self.keta_1[0], self.keta_1[1]
        cx_2, cy_2 = self.keta_2[0], self.keta_2[1]
        
        #
        m = self.wing_1.shape[0]
        n = len(self.table)
        self.wing_x = np.zeros((m,n))
        self.wing_y = np.zeros((m,n))
        
        for i in range(m):
            x_root, y_root = self.wing_1[i,0]-cx_1, self.wing_1[i,1]-cx_2
            x_end, y_end = self.wing_2[i,0]-cy_1, self.wing_2[i,1]-cy_2
            
            for j in range(n):
                # 各コード長における補間値を計算
                cord_p = self.table[j]
                x = self.lerp(cord_p, x_root,x_end)
                y = self.lerp(cord_p, y_root,y_end)
                cx = self.lerp(cord_p, cx_1,cx_2)
                cy = self.lerp(cord_p, cy_1,cy_2)
                
                self.wing_x[i,j] = x + cx
                self.wing_y[i,j] = y + cy
                
    def wing_corner(self):
        # 中心座標
        cx_1, cy_1 = self.keta_1[0], self.keta_1[1]
        cx_2, cy_2 = self.keta_2[0], self.keta_2[1]
        
        #
        m = len(self.points_1) #三角の個数
        n = 12 # 一つの三角あたりのデータ数
        o = len(self.table)# リブの枚数
        self.point = np.zeros((m,n,o))
        
        i = 0
        for point_d1,point_d2 in zip(self.points_1,self.points_2):
            j = 0
            for p1,p2 in zip(point_d1,point_d2):
                p1_x, p1_y = p1[0]-cx_1, p1[1]-cy_1
                p2_x, p2_y = p2[0]-cx_2, p2[1]-cy_2
                
                for k in range(o):
                    # 各コード長における補間値を計算
                    cord_p = self.table[k]
                    x = self.lerp(cord_p, p1_x,p2_x)
                    y = self.lerp(cord_p, p1_y,p2_y)
                    cx = self.lerp(cord_p, cx_1,cx_2)
                    cy = self.lerp(cord_p, cy_1,cy_2)
                    
                    self.point[i,j,k] = x + cx
                    self.point[i,j+1,k] = y + cy
                    
                j += 2
            i += 1
            
    def wing_circle(self,c1,c2):
        # 中心座標
        cx_1, cy_1 = self.keta_1[0], self.keta_1[1]-c1
        cx_2, cy_2 = self.keta_2[0], self.keta_2[1]-c2
        
        c_R = self.keta_1[3]
        
        #
        m = 3 # 桁１つあたりのデータ数
        n = len(self.table) # リブの枚数
        
        self.circle = np.zeros((m,n))             
        for i in range(n):
            cord_p = self.table[i]
            x = self.lerp(cord_p, cx_1,cx_2)
            y = self.lerp(cord_p, cy_1,cy_2)
            
            self.circle[0,i] = x
            self.circle[1,i] = y
            self.circle[2,i] = c_R
            
    def print_data(self):
        print(self.wing_x.shape)
        print(self.point.shape)
    
    def out_dxf(self,table_tab2):
        n = len(self.table) # リブの枚数
        points = self.point
        circle = self.circle
        
        path = './output'
        os.makedirs(path, exist_ok=True)
        
        for i in range(n):
            path_i = path + '/{}.dnc'.format(i+1)
            f = open(path_i, 'w')
            
            f.write('%\nG00 X0 Y0 Z5.000\nM03S2000\nG01Z-22.500F 800\n')
            
            x_re,y_re = self.wing_x[0,i], self.wing_y[0,i]
            
            # 翼の出力
            for x,y in zip(self.wing_x[:,i],self.wing_y[:,i]):
                f.write('X{}Y{}\n'.format(x-x_re,y-y_re))
            f.write('G00 Z5.000\n')
            
            #　肉抜きの出力
            for j in range(points.shape[0]):
                r = table_tab2[j]
                x1,y1 = points[j,0,i],points[j,1,i]
                x2,y2 = points[j,2,i],points[j,3,i]
                x3,y3 = points[j,4,i],points[j,5,i]
                x4,y4 = points[j,6,i],points[j,7,i]
                x5,y5 = points[j,8,i],points[j,9,i]
                x6,y6 = points[j,10,i],points[j,11,i]
                
                f.write('G00 X{} Y{}\n'.format(x1,y1))
                f.write('G01 Z-22.500\n')
                if y1 == y2:
                    f.write('X{} Y{}\n'.format(x3,y3))
                    f.write('X{} Y{}\n'.format(x5,y5))
                    f.write('X{} Y{}\n'.format(x1,y1))
                else:
                    f.write('G03 X{} Y{} R{}\n'.format(x2,y2,r))
                    f.write('G01 X{} Y{}\n'.format(x5,y5))
                    f.write('G03 X{} Y{} R{}\n'.format(x6,y6,r))
                    f.write('G01 X{} Y{}\n'.format(x3,y3))
                    f.write('G03 X{} Y{} R{}\n'.format(x4,y4,r))
                    f.write('G01 X{} Y{}\n'.format(x1,y1))
                    
                f.write('G00 Z 5.000\n')
            
            print(x1,y1,x2,y2,x3,y3,x4,y4,x5,y5,x6,y6)
            # 桁穴の出力
            xc,yc,rc = circle[0,i],circle[1,i],circle[2,i]/2
            f.write('G00 X{} Y{}\n'.format(xc,yc+rc))
            f.write('G01 Z-22.500\n')
            #f.write('G01X{}Y{}\n'.format(xc+40,yc-rc))
            f.write('G02 X{} Y{} I0 J{}\n'.format(xc,yc+rc,-rc))
            f.write('G00Z 5.000\n')
            f.close()
            
    def out_dxf_onefile(self,table_tab2):
        n = len(self.table) # リブの枚数
        points = self.point
        circle = self.circle
        
        path = './output'
        os.makedirs(path, exist_ok=True)
        
        path_i = path + '/out.dnc'
        f = open(path_i, 'w')
        f.write('%\nG00 X0 Y0 Z5.000\nM03S2000\n')
        
        y_inter = 0
        for i in range(n):
            x_re,y_re = self.wing_x[0,i], self.wing_y[0,i]
            
            # 翼の出力
            f.write('G00 X{} Y{}\n'.format(0,y_inter))
            f.write('G01 Z-22.500 F 800\n')
            for x,y in zip(self.wing_x[:,i],self.wing_y[:,i]):
                f.write('X{} Y{}\n'.format(x-x_re,y-y_re+y_inter))
            f.write('G00 Z5.000\n')
            
            #　肉抜きの出力
            for j in range(points.shape[0]):
                r = table_tab2[j]
                x1,y1 = points[j,0,i],points[j,1,i] + y_inter
                x2,y2 = points[j,2,i],points[j,3,i] + y_inter
                x3,y3 = points[j,4,i],points[j,5,i] + y_inter
                x4,y4 = points[j,6,i],points[j,7,i] + y_inter
                x5,y5 = points[j,8,i],points[j,9,i] + y_inter
                x6,y6 = points[j,10,i],points[j,11,i] + y_inter
                
                f.write('G00 X{} Y{}\n'.format(x1,y1))
                f.write('G01 Z-22.500\n')
                if y1 == y2:
                    f.write('X{} Y{}\n'.format(x3,y3))
                    f.write('X{} Y{}\n'.format(x5,y5))
                    f.write('X{} Y{}\n'.format(x1,y1))
                else:
                    f.write('G03 X{} Y{} R{}\n'.format(x2,y2,r))
                    f.write('G01 X{} Y{}\n'.format(x5,y5))
                    f.write('G03 X{} Y{} R{}\n'.format(x6,y6,r))
                    f.write('G01 X{} Y{}\n'.format(x3,y3))
                    f.write('G03 X{} Y{} R{}\n'.format(x4,y4,r))
                    f.write('G01 X{} Y{}\n'.format(x1,y1))
                    
                f.write('G00 Z5.000\n')
            
            #print(x1,y1,x2,y2,x3,y3,x4,y4,x5,y5,x6,y6)
            # 桁穴の出力
            xc,yc,rc = circle[0,i],circle[1,i] + y_inter,circle[2,i]/2
            f.write('G00 X{} Y{}\n'.format(xc,yc+rc))
            f.write('G01 Z-22.500\n')
            #f.write('G01X{}Y{}\n'.format(xc+40,yc-rc))
            f.write('G02 X{} Y{} I0 J{}\n'.format(xc,yc+rc,-rc))
            f.write('G00 Z5.000\n')
            
            y_inter += max(self.wing_y[:,i]) - y_re + 15
        
        f.close()