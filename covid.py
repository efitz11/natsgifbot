import utils

URL = "https://covidtracking.com/api/"

def format_data(data):
    l = list()
    l.append({'name':'positive', 'total':data['positive']})
    l.append({'name':'negative', 'total':data['negative']})
    l.append({'name':'hospitalized', 'total':data['hospitalized']})
    l.append({'name':'deaths', 'total':data['death']})
    l.append({'name':'total', 'total':data['total']})
    return l

def get_us(delta=None):
    url = URL + "us"
    if delta is None:
        data = utils.get_json(url)[0]
        l = format_data(data)
        l.insert(2, {'name':'pos+neg', 'total':data['posNeg']})

        yesterday_url = URL + "us/daily"
        yesterday = utils.get_json(yesterday_url)[0]
        l[0]['yesterday'] = yesterday['positive']
        l[0]['delta'] = l[0]['total'] - yesterday['positive']
        l[1]['yesterday'] = yesterday['negative']
        l[1]['delta'] = l[1]['total'] - yesterday['negative']
        l[2]['yesterday'] = yesterday['posNeg']
        l[2]['delta'] = l[2]['total'] - yesterday['posNeg']
        l[3]['yesterday'] = yesterday['hospitalized']
        l[3]['delta'] = l[3]['total'] - yesterday['hospitalized']
        l[4]['yesterday'] = yesterday['death']
        l[4]['delta'] = l[4]['total'] - yesterday['death']
        l[5]['yesterday'] = yesterday['total']
        l[5]['delta'] = l[5]['total'] - yesterday['total']

        labels = ['name', 'total', 'yesterday', 'delta']
        repl_map = {'name':''}
        return "```python\n%s\n\n%s```" % ("US current totals:", utils.format_table(labels, l, repl_map=repl_map, left_list=['name']))

def get_state(state, delta=None):
    url = URL + "states"
    if delta is None:
        data = utils.get_json(url)
        state_entry = None
        for st in data:
            if st['state'].lower() == state.lower():
                state_entry = st
                break
        if state_entry is not None:
            l = format_data(state_entry)
            l.append({'name':'data quality', 'total':state_entry['grade']})
            l.append({'name':'updated', 'total':state_entry['lastUpdateEt']})
            labels = ['name', 'total']
            repl_map = {'name':''}
            return "```python\n%s\n\n%s```" % ("%s current totals:" % state_entry['state'], utils.format_table(labels, l, repl_map=repl_map, left_list=['name']))
        else:
            return "State not found."

if __name__ == "__main__":
    print(get_us())
    print(get_state("VA"))

