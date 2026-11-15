# test_1 旨在对命中数次序的规律进行研究，即权重因子分析

from datetime import datetime

def create_33():
    a = []
    for i in range(33):
        a.append(0)
    return a

def merge_33(a,b):
    c = create_33()
    for i in range(33):
        c[i] = a[i] + b[i]
    return c 

# 权重筛选
def guess(a,p): # a=weight
    res = []
    comp = -1
    num = 0
    for i in range(len(a)):
        for j in range(len(a)):
            if a[j] > comp:
                comp = a[j]
                num = j+1
        a[num-1] = -1
        res.append(num)
        comp = -1
    res1 = []
    for i in range(p): #选择参数
        res1.append(res[i])
    return res1

def intlst(a):
    b = []
    for i in a:
        b.append(int(i))
    return b 

# 数字验证
def acc(a,b,i):
    res1 = []
    for j in range(len(b[i])):
        for k in range(len(a)):
            if a[k] == b[i][j]:
                res1.append(k)
    res = []
    res1.sort()
    res.append(res1)
    res.append(b[i])

    return res

def main(h,d,p,l,dataset):

    f = open("C:\\Users\\29158\\Desktop\\彩票研究\\{}.txt".format(dataset))
    lst = f.readlines()
    sumi = len(lst)

    # 参数控制
    #l = 20  #遗传代际 711 921
    r = sumi-l #测试轮次
    hit = h
    diffusive = d

    now = datetime.now()
    time = now.strftime("%Y-%m-%d-%H-%M-%S")
    parameter = "r="+str(r)+"-l="+str(l)+"-h="+str(hit)+"-d="+str(diffusive)
    parameter2 = "Hit="+str(hit)+"_Diffusive="+str(diffusive)+"_Possibility="+str(p)
    
    import os
    os.makedirs("C:\\Users\\29158\\Desktop\\彩票研究\\t1_{}\\{}".format(dataset,parameter2), exist_ok=True)
    log = open("C:\\Users\\29158\\Desktop\\彩票研究\\t1_{}\\{}\\log_{}.txt".format(dataset,parameter2,parameter),"w+",encoding="UTF-8")

    log.write(time+"\n")

    weight_red_all = []


    # 权重控制
    lst_processed = []
    for i in lst:
        a = i.split(",")
        red = a[2].split(" ")
        red = intlst(red)
        weight_red = create_33()
        for j in red:
            if j == 1:
                weight_red[j-1] += hit  # 命中数
                weight_red[j] += diffusive    # 右侧
            elif j == 33:
                weight_red[j-1] += hit  # 命中数
                weight_red[j-2] += diffusive  # 左侧
            else:
                weight_red[j] += diffusive    # 右侧
                weight_red[j-1] += hit  # 命中数
                weight_red[j-2] += diffusive  # 左侧
        weight_red_all.append(weight_red)
        lst_processed.append(red)

    accl =  create_33()
    acclst = []
    for i in range(r):
        weight_red_10 = create_33()
        for j in range(l):
            weight_red_10 = merge_33(weight_red_all[j+i],weight_red_10)

        #print(weight_red_10)
        guess_res = guess(weight_red_10,p)
        accs = acc(guess_res,lst_processed,i+j+1)
        log.write("第 "+str(i+1)+" 轮\n")
        log.write("猜测命中次序："+str(accs[0])+"\n")
        log.write("命中集合："+str(accs[1])+"\n")

        for k in accs[0]:
            accl[k] += 1
        acclst.append(accs)
        
    import matplotlib.pyplot as plt
    for i in range(len(accl)):
        plt.scatter(i, accl[i], color="red", marker="*", s=100)
    plt.title(parameter)
    plt.xlabel("X-axis")
    plt.ylabel("Y-axis")

    plt.savefig("C:\\Users\\29158\\Desktop\\彩票研究\\t1_{}\\{}\\log_{}.png".format(dataset,parameter2,parameter), dpi=300, bbox_inches="tight")
    plt.close()

    log.write(str(accl)+"\n")
    #print(accl)
    log.write(time+"\n")
    #print(add/r)
    #print(acclst)

    f.close()
    log.close()

    return accl

if __name__ == "__main__":

    h = 2
    d = 3
    p = 33
    dataset = "data_3"
    parameter = "Hit="+str(h)+"_Diffusive="+str(d)+"_Possibility="+str(p)

    res = []
    accli = create_33()
    for i in range(1,20):
        hitp = main(h,d,p,i,dataset)
        accli = merge_33(accli,hitp)
    #for i in range(len(accli)):
    #    accli[i] = accli[i]/10
    print(accli)


