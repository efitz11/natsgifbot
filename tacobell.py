import random

def random_items(num):
    with open("tbellmenu.csv", 'r', encoding="utf-8") as f:
        content = f.readlines()
    items = [x.strip() for x in content]
    order = []
    cals = 0
    for i in range(num):
        n = random.randint(0,len(items))
        chosen = items[n].split(',')
        order.append(chosen[0])
        cals += int(chosen[1])
    orderstr = ""
    for s in order:
        orderstr = orderstr + s + ", "
    orderstr = orderstr[:-2] + "\nTotal calories: %d" % cals
    return orderstr

if __name__ == "__main__":
    print(random_items(3))
