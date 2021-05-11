# -*- coding: utf-8 -*-
# python 3.7.0

from PIL import Image
import os
import logging
import threading

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.WARNING, datefmt='%Y-%m-%d %H:%M:%S')


IMG_SUFFIX = [".jpg", ".png", ".jpeg", ".gif", ".bmp"]

CONTENTS_PATH = os.path.join(os.getcwd(), 'compress')

MAX_CONNECTIONS = 20  # 定义最大线程数

MAX_WIDTH = 1800 #目标图片宽

MAX_SIZE = 1024 #目标文件大小，kb

'''文件处理'''


def writefile(fileURI, str):
    with open(fileURI, 'w', encoding='UTF-8') as w:
        w.write(str)


def readfile(fileURI):
    with open(fileURI, 'r', encoding='UTF-8') as r:
        return r.read()


def checkFileExist(fileURI):
    if os.path.isfile(fileURI):
        return True
    return False


def checkFolder(src):
    if not '#' in src:
        return src
    dst = str.replace(src, '#', '_')
    try:
        os.rename(src, dst)
        return dst
        pass
    except:
        return src
        pass


'''
:图片处理部分
'''


def get_size(file):
    # 获取文件大小:KB
    size = os.path.getsize(file)
    return size / 1024


def get_outfile(infile, outSuffix=''):
    if not outSuffix:
        return infile
    dir, suffix = os.path.splitext(infile)
    outfile = '{}{}{}'.format(dir, outSuffix, suffix)
    return outfile


def compress_image(infile, outfile='', kb=1024, step=10, quality=90):
    """不改变图片尺寸压缩到指定大小
    :param infile: 压缩源文件
    :param outfile: 压缩文件保存地址
    :param kb: 压缩目标，KB
    :param step: 每次调整的压缩比率
    :param quality: 初始压缩比率
    :return: 压缩文件地址，压缩文件大小
    """
    o_size = get_size(infile)
    if o_size <= kb:
        return infile, o_size
    # if infile.endswith(('.bmp', '.gif', '.png')):
    #     with Image.open(infile) as im:
    #         im = im.convert('RGB')
    #         im.save(infile[:-3] + 'jpg', quality=100)
    #     os.remove(infile)
    #     infile = infile[:-3] + 'jpg'

    
    outfile = get_outfile(infile)
    with Image.open(infile) as im:
        while o_size > kb:
            im.save(outfile, quality=quality)
            if quality - step <= 0:
                break
            quality -= step
            o_size = get_size(outfile)
    return outfile, get_size(outfile)


def resize_image(infile, outfile='', x_s=1800):
    """修改图片尺寸
    :param infile: 图片源文件
    :param outfile: 重设尺寸文件保存地址
    :param x_s: 设置的宽度
    :return:
    """

    with Image.open(infile) as im:
        x, y = im.size
        if x <= x_s:
            return
        y_s = int(y * x_s / x)
        out = im.resize((x_s, y_s), Image.ANTIALIAS)
        outfile = get_outfile(infile, outfile)
        out.save(outfile, quality=100)

def zip_img(infile):
    if not checkFileExist(infile):
        return
    o_size = get_size(infile)
    # if infile.lower().endswith(('.bmp', '.gif', '.png')):
    #     with Image.open(infile) as im:
    #         im = im.convert('RGB')
    #         im.save(infile[:-3] + 'jpg', quality=100)
    #     os.remove(infile)
    #     infile = infile[:-3] + 'jpg'
    resize_image(infile, x_s = MAX_WIDTH)
    outfile, d_size = compress_image(infile, kb = MAX_SIZE)
    return outfile, o_size, d_size

def gci(filepath):
    # 遍历filepath下所有文件，包括子目录
    files = os.listdir(filepath)
    for fi in files:
        fi_d = os.path.join(filepath, fi)
        if os.path.isdir(fi_d):
            fi_d = checkFolder(fi_d)
            contentPaths.append(fi_d)
            gci(fi_d)


def createImgList(content_path):
    imgs = []
    for _dir in os.listdir(content_path):
        if(os.path.splitext(_dir)[0].startswith('.')):
            continue
        if os.path.splitext(_dir)[1].lower() in IMG_SUFFIX:
            imgs.append(_dir)

    return imgs


class zipImg(threading.Thread):
    tlist = []  # 用来存储队列的线程
    # int(sys.argv[2])最大的并发数量，此处我设置为100，测试下系统最大支持1000多个
    maxthreads = MAX_CONNECTIONS
    evnt = threading.Event()  # 用事件来让超过最大线程设置的并发程序等待
    lck = threading.Lock()  # 线程锁

    def __init__(self, filePath):
        threading.Thread.__init__(self)
        self.filePath = filePath

    def run(self):
        try:
            d_filePath, o_size, d_size = zip_img(self.filePath)
            logging.warning(
                f'{threading.current_thread().name} 压缩成功 File: {self.filePath} => {d_filePath} Size: {int(o_size)}kb => {int(d_size)}kb')
            pass
        except:
           logging.error(
               f'{threading.current_thread().name} 压缩失败 {self.filePath}')
           pass
        
        # 以下用来将完成的线程移除线程队列
        self.lck.acquire()
        self.tlist.remove(self)
        # 如果移除此完成的队列线程数刚好达到99，则说明有线程在等待执行，那么我们释放event，让等待事件执行
        if len(self.tlist) == self.maxthreads-1:
            self.evnt.set()
            self.evnt.clear()
        self.lck.release()

    def newthread(filePath):
        zipImg.lck.acquire()  # 上锁
        sc = zipImg(filePath)
        zipImg.tlist.append(sc)
        zipImg.lck.release()  # 解锁
        sc.start()
    # 将新线程方法定义为静态变量，供调用
    newthread = staticmethod(newthread)


'''
list分块
'''


def partition(lst, n):
    division = len(lst) / float(n)
    return [list(lst)[int(round(division * i)): int(round(division * (i + 1)))] for i in range(n)]


def listChunk(listTemp, n):
    for i in range(0, len(listTemp), n):
        yield listTemp[i:i + n]


if __name__ == '__main__':

    pool_sema = threading.Semaphore(MAX_CONNECTIONS)

    contentPaths = []
    logging.critical('开始遍历文件夹...')
    gci(CONTENTS_PATH)
    listTimer = []
    listPaths = []

    for contentPath in contentPaths:
        imgList = createImgList(contentPath)
        for imgPaths in imgList:
            fileBash = os.path.join(contentPath, imgPaths)
            listPaths.append(fileBash)

    for imgBash in listPaths:
        zipImg.lck.acquire()
        # 如果目前线程队列超过了设定的上线则等待。
        if len(zipImg.tlist) >= zipImg.maxthreads:
            zipImg.lck.release()
            zipImg.evnt.wait()  # zipImg.evnt.set()遇到set事件则等待结束
        else:
            zipImg.lck.release()
        zipImg.newthread(imgBash)

    for list in zipImg.tlist:
        list.join()

    logging.critical('所有线程结束')
