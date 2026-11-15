

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
    correct = 0
    for j in range(len(a)):
        if a[j] in b[i]:
            correct += 1
    res = []
    res.append(a)
    res.append(b[i])
    res.append(correct)

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
    os.makedirs("C:\\Users\\29158\\Desktop\\彩票研究\\{}\\{}".format(dataset,parameter2), exist_ok=True)
    log = open("C:\\Users\\29158\\Desktop\\彩票研究\\{}\\{}\\log_{}.txt".format(dataset,parameter2,parameter),"w+",encoding="UTF-8")

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


    acclst = []
    for i in range(r):
        weight_red_10 = create_33()
        for j in range(l):
            weight_red_10 = merge_33(weight_red_all[j+i],weight_red_10)

        #print(weight_red_10)
        guess_res = guess(weight_red_10,p)
        accs = acc(guess_res,lst_processed,i+j+1)
        log.write("第 "+str(i+1)+" 轮\n")
        log.write("猜测集合："+str(accs[0])+"\n")
        log.write("命中集合："+str(accs[1])+"\n")
        log.write("命中数："+str(accs[2])+"\n")

        acclst.append(accs)
        

    add = 0
    hitnum = [0,0,0,0,0,0,0]
    for i in range(len(acclst)):
        add += acclst[i][2]/6
        hitnum[acclst[i][2]] += 1

    hitp = []
    log.write("\n平均命中率："+str(add/r)+"\n")
    for i in range(7):
        log.write("命中数为{}，共计{}次\n".format(i,hitnum[i]))
        hitp.append(hitnum[i]/r)
    log.write(time+"\n")
    #print(add/r)
    #print(acclst)

    f.close()
    log.close()

    return hitp

if __name__ == "__main__":

    h = 1
    d = 0
    p = 6
    dataset = "data_3"
    parameter = "Hit="+str(h)+"_Diffusive="+str(d)+"_Possibility="+str(p)

    res = []
    
    for i in range(1,20):
        hitp = main(h,d,p,i,dataset)
        res.append(hitp)

    s = ""
    Log = open("C:\\Users\\29158\\Desktop\\彩票研究\\{}\\LOG_{}.txt".format(dataset,parameter),"w+",encoding="UTF-8")
    for i in range(0,19):
        for j in range(7):
            s += "{}:{}\t".format(str(j),str(res[i][j])[:5])
        print(s)
        Log.write(s+"\n")
        s = ""
    #Log.flush()
    Log.close()