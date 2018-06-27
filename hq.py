import pickle, os
from datetime import datetime, time

f = "hqsers.txt"

def check_hq():
    dayst = time(19,57,0)
    dayet = time(19,0,0)
    nightst = time(20,57,0)
    nightet = time(21,0,0)
    
    dayofweek = datetime.today().weekday()
    now = datetime.time(datetime.now())
    if dayofweek >= 5 and (now<nightst): #weekends are nights only
        return False
    else:
        if (now>dayst and now<dayet)  or (now>nightst and now<nightet):
            return True
    return False
    
def __load_map():
    try:
        map = pickle.load(open(f,"rb"))
    except:
        map = []
    return map
    
def register_user(user):
    map = __load_map()
    if not is_user_registered(user):
        map.append(user)
        pickle.dump(map, open(f,"wb"))
        return "registered successfully"
    else:
        return "user already registered"
    
def unregister_user(user):
    map = __load_map()
    if is_user_registered(user):
        map.remove(user)
        pickle.dump(map, open(f,"wb"))
        return "unregistered successfully"
    else:
        return "user already unregistered"
    
def is_user_registered(user):
    map = __load_map()
    return user in map
    
def list_users(mention=False):
    map = __load_map()
    output = ""
    for u in map:
        if mention:
            output = output + u.mention + ", "
        else:
            output = output + u.display_name + ", "
    if len(output) > 0:
        return output[:-2]
    else:
        if mention:
            return "No one to ping"
        else:
            return "No one to list"