import utils

URL = "https://covidtracking.com/api/"

def format_data(data):
    l = list()
    l.append({'name':'positive', 'total':data['positive']})
    l.append({'name':'negative', 'total':data['negative']})
    l.append({'name':'hospitalized', 'total':data['hospitalized']})
    l.append({'name':'deaths', 'total':data['death']})
    l.append({'name':'total tested', 'total':data['totalTestResults']})
    return l

def format_number(number):
    if int(number) > 1000000:
        return str(int(number / 10000)/100.0) + 'M'
    elif int(number) > 100000:
        return str(int(number/1000)) + 'k'
    elif int(number) > 999:
        return str(int(number/100)/10.0) + 'k'
    else:
        return str(number)

def add_day_columns(data_list, day, c1_name, c2_name, subtract_key):
    l = data_list
    yesterday = day
    l[0][c1_name] = yesterday['positive']
    l[0][c1_name + "_str"] = format_number(yesterday['positive'])
    l[0][c2_name] = format_number(l[0][subtract_key] - yesterday['positive'])
    l[1][c1_name] = yesterday['negative']
    l[1][c1_name + "_str"] = format_number(yesterday['negative'])
    l[1][c2_name] = format_number(l[1][subtract_key] - yesterday['negative'])
    l[2][c1_name] = yesterday['hospitalized']
    l[2][c1_name + "_str"] = format_number(yesterday['hospitalized'])
    l[2][c2_name] = format_number(l[2][subtract_key] - yesterday['hospitalized'])
    l[3][c1_name] = yesterday['death']
    l[3][c1_name + "_str"] = format_number(yesterday['death'])
    l[3][c2_name] = format_number(l[3][subtract_key] - yesterday['death'])
    l[4][c1_name] = yesterday['totalTestResults']
    l[4][c1_name + "_str"] = format_number(yesterday['totalTestResults'])
    l[4][c2_name] = format_number(l[4][subtract_key] - yesterday['totalTestResults'])
    return l

def convert_date(date_int):
    date_str_cat = str(date_int)[4:]
    return date_str_cat[:2] + '/' + date_str_cat[2:]

def get_us(delta=None):
    url = URL + "us"
    if delta is None:
        data = utils.get_json(url)[0]
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

if __name__ == "__main__":
    print(get_us())
    print(get_state("VA"))

