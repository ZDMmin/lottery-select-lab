# test_3 

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
def guess_t(a,p): # a=weight
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

def guess_m(a,w): # a=weight
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
    weight = w
    for i in weight: #选择参数
        res1.append(res[i])
    return res1

def intlst(a):
    b = []
    for i in a:
        b.append(int(i))
    return b 

# 数字验证
def acc_t(a,b,i):
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

def acc(a,b): # 特殊处理
    correct = 0
    for j in range(len(a)):
        if a[j] in b:
            correct += 1
    res = []
    res.append(a)
    res.append(b)
    res.append(correct)

    return res

def find_w(h,d,p,l,dataset): # 寻找最佳权重

    f = open("C:\\Users\\29158\\Desktop\\彩票研究\\{}.txt".format(dataset))
    lst = f.readlines()
    sumi = len(lst)

    # 参数控制
    #l = 20  #遗传代际 711 921
    r = sumi-l #测试轮次
    hit = h
    diffusive = d

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

        guess_res = guess_t(weight_red_10,33)
        accs = acc_t(guess_res,lst_processed,i+j+1)

        for k in accs[0]:
            accl[k] += 1
        acclst.append(accs)

    f.close()

    weight = []
    maxi = 0
    maxp = 0
    weight_i = []
    weight_p = []
    for i in range(6):
        for j in range(33):
            if accl[j] > maxi:
                maxi = accl[j]
                maxp = j
        accl[maxp] = 0
        weight_i.append(maxi)
        weight_p.append(maxp)
        maxi = 0
        maxp = 0
    weight.append(weight_p)
    weight.append(weight_i)
    return weight_p

def find_r(h,d,p,l,dataset,w,k):

    f = open("C:\\Users\\29158\\Desktop\\彩票研究\\{}.txt".format(dataset))
    lst = f.readlines()
    sumi = len(lst)

    lstr = []
    for i in range(l):
        lstr.append(lst[sumi-i-1-k])

    # 参数控制
    hit = h
    diffusive = d

    weight_red_all = []


    # 权重控制
    lst_processed = []
    for i in lstr:
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

    for i in range(1):
        weight_red_10 = create_33()
        for j in range(l):
            weight_red_10 = merge_33(weight_red_all[j+i],weight_red_10)

        #print(weight_red_10)
        guess_res = guess_m(weight_red_10,w)

    a = lst[sumi-k].split(",")
    red = a[2].split(" ")
    red = intlst(red)
    res = []
    res.append(guess_res)
    res.append(red)

    f.close()
    return res


def main(h,d,p,k,dataset):
    res = []
    weight_all = []
    resm = create_33()
    for i in range(1,20):
        weight = find_w(h,d,p,i,dataset)
        weight_all.append(weight)
    for i in range(1,20):
        resi = find_r(h,d,p,i,dataset,weight_all[i-1],k)
        res.append(resi[0])

    for i in range(19):
        for j in range(6):
            resm[res[i][j]-1] += 1

    resl = []
    maxi = -1
    maxp = 0
    for i in range(33):
        for j in range(33):
            if resm[j] > maxi:
                maxi = resm[j]
                maxp = j
        resl.append(maxp+1)
        resm[maxp] = -1
        maxi = -1
        maxp = 0

    resk = []
    for i in range(p):
        resk.append(resl[i])

    res = acc(resk,resi[1])
    return res


if __name__ == "__main__":
    
    
    h = 2
    d = 1
    p = 6
    r = 100
    dataset = "data_4"
    parameter = "Hit="+str(h)+"_Diffusive="+str(d)+"_Possibility="+str(p)+"_Round="+str(r)

    res = []
    for i in range(1,r+1):
        resi = main(h,d,p,i,dataset)
        res.append(resi)

    import os
    os.makedirs("C:\\Users\\29158\\Desktop\\彩票研究\\t4_{}".format(dataset), exist_ok=True)
    Log = open("C:\\Users\\29158\\Desktop\\彩票研究\\t4_{}\\LOG_{}.txt".format(dataset,parameter),"w+",encoding="UTF-8")
    for i in range(r):
        Log.write("猜测集合："+str(res[i][0])+"\n")
        Log.write("命中集合："+str(res[i][1])+"\n")
        Log.write("命中数："+str(res[i][2])+"\n")

    add = 0
    hitnum = [0,0,0,0,0,0,0]
    for i in range(r):
        add += res[i][2]/6
        hitnum[res[i][2]] += 1

    hitp = []
    Log.write("\n平均命中率："+str(add/r)+"\n")
    for i in range(7):
        Log.write("命中数为{}，共计{}次\n".format(i,hitnum[i]))
    #Log.flush()
    Log.close()

