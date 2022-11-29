import os
import imageio
from django.test import TestCase




# Create your tests here.


def png2gif(source, gifname, time):
    os.chdir(source)  # os.chdir()：改变当前工作目录到指定的路径
    file_list = os.listdir()  # os.listdir()：文件夹中的文件/文件夹的名字列表
    frames = []  # 读入缓冲区
    for png in file_list:
        frames.append(imageio.v2.imread(png))
    imageio.mimsave(gifname, frames, 'GIF', duration=time)



