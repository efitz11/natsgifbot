import utils
import json

URL = "https://covidtracking.com/api/"

def format_data(data):
    l = list()
    l.append({'name':'positive', 'total':data['positive']})
    l.append({'name':'negative', 'total':data['negative']})
    l.append({'name':'hosp. now', 'total':data['hospitalizedCurrently']})
    l.append({'name':'hosp. total', 'total':data['hospitalizedCumulative']})
    l.append({'name':'recovered', 'total':data['recovered']})
    l.append({'name':'deaths', 'total':data['death']})
    l.append({'name':'total tested', 'total':data['totalTestResults']})
    return l

def format_number(number):
    if abs(int(number)) > 1000000:
        return str(int(number / 10000)/100.0) + 'M'
    elif abs(int(number)) > 100000:
        return str(int(number/1000)) + 'k'
    elif abs(int(number)) > 999:
        return str(int(number/100)/10.0) + 'k'
    else:
        return str(number)

def number_commas(number):
    return "{:,}".format(number)

def add_day_columns(data_list, day, c1_name, c2_name, subtract_key):
    l = data_list
    yesterday = day
    l[0][c1_name] = yesterday['positive']
    l[0][c1_name + "_str"] = format_number(yesterday['positive'])
    l[0][c2_name] = format_number(l[0][subtract_key] - yesterday['positive'])
    l[1][c1_name] = yesterday['negative']
    l[1][c1_name + "_str"] = format_number(yesterday['negative'])
    l[1][c2_name] = format_number(l[1][subtract_key] - yesterday['negative'])
    l[2][c1_name] = yesterday['hospitalizedCurrently']
    l[2][c1_name + "_str"] = format_number(yesterday['hospitalizedCurrently'])
    l[2][c2_name] = format_number(l[2][subtract_key] - yesterday['hospitalizedCurrently'])
    l[3][c1_name] = yesterday['hospitalizedCumulative']
    l[3][c1_name + "_str"] = format_number(yesterday['hospitalizedCumulative'])
    l[3][c2_name] = format_number(l[3][subtract_key] - yesterday['hospitalizedCumulative'])
    l[4][c1_name] = yesterday['recovered']
    l[4][c1_name + "_str"] = format_number(yesterday['recovered'])
    l[4][c2_name] = format_number(l[4][subtract_key] - yesterday['recovered'])
    l[5][c1_name] = yesterday['death']
    l[5][c1_name + "_str"] = format_number(yesterday['death'])
    l[5][c2_name] = format_number(l[5][subtract_key] - yesterday['death'])
    l[6][c1_name] = yesterday['totalTestResults']
    l[6][c1_name + "_str"] = format_number(yesterday['totalTestResults'])
    l[6][c2_name] = format_number(l[6][subtract_key] - yesterday['totalTestResults'])
    return l

def convert_date(date_int):
    date_str_cat = str(date_int)[4:]
    return date_str_cat[:2] + '/' + date_str_cat[2:]

def get_us(delta=None, jsondata=None):
    url = URL + "us"
    if delta is None:
        if jsondata is None:
            data = utils.get_json(url)[0]
        else:
            data = jsondata
        l = format_data(data)

        yesterday_url = URL + "us/daily"
        days = utils.get_json(yesterday_url)
        days_index = 0
        if days[0]['totalTestResults'] == data['totalTestResults']:
            days_index += 1
        l = add_day_columns(l, days[days_index], 'yesterday', 'delta', 'total')
        l = add_day_columns(l, days[days_index + 1], '2 days', 'delta2', 'yesterday')

        yesterday_date = convert_date(days[days_index]['date'])
        two_days_date = convert_date(days[days_index + 1]['date'])

        for idx in l:
            idx['total'] = number_commas(idx['total'])

        labels = ['name', 'total', 'yesterday_str', '2 days_str', 'delta', 'delta2']
        repl_map = {'name':'', 'yesterday_str':yesterday_date, '2 days_str':two_days_date}
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

def check_for_updates():
    miscfile = 'misc.json'
    with open(miscfile, 'r') as f:
        s = json.loads(f.read())
    url = URL + "us"
    data = utils.get_json(url)[0]
    if 'covid' not in s:
        s['covid'] = data['totalTestResults']
        with open(miscfile, 'w') as f:
            f.write(json.dumps(s, indent=4))
        return get_us(jsondata=data)
    else:
        if s['covid'] < data['totalTestResults']:
            s['covid'] = data['totalTestResults']
            with open(miscfile, 'w') as f:
                f.write(json.dumps(s, indent=4))
            return get_us(jsondata=data)
        else:
            return None

def get_usa():
    url = "https://disease.sh/v2/countries/usa"
    urly = url + "?yesterday=true"

    todaydata = utils.get_json(url)
    todaydata['state'] = "Today"
    yestdata = utils.get_json(urly)
    yestdata['state'] = "Yest."
    l = [todaydata, yestdata]

    labels = ['state','cases', 'todayCases', 'deaths', 'todayDeaths']
    replmap = {'state':'', 'todayCases':'new cases', 'todayDeaths':'new deaths'}

    # get top 5 states
    l.append({'state':'top 5 states:'})
    l.extend(get_state_data()[:5])

    for data in l:
        for lab in labels:
            if lab in data and isinstance(data[lab], int):
                data[lab] = format_number(data[lab])
    tab = utils.format_table(labels, l, repl_map=replmap, left_list=['name'])

    return "```python\n%s```" % tab

def get_state_data():
    url = "https://disease.sh/v2/states"

    statedata = utils.get_json(url)
    statedata = sorted(statedata, key = lambda i: i['todayCases'], reverse=True)
    return statedata

if __name__ == "__main__":
    print(get_usa())
    # print(get_state("VA"))
    # print(check_for_updates())

