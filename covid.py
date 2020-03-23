import utils

URL = "https://covidtracking.com/api/"

def get_us(delta=None):
    url = URL + "us"
    if delta is None:
        data = utils.get_json(url)[0]
        l = list()
        l.append({'name':'positive', 'total':data['positive']})
        l.append({'name':'negative', 'total':data['negative']})
        l.append({'name':'pos+neg', 'total':data['posNeg']})
        l.append({'name':'hospitalized', 'total':data['hospitalized']})
        l.append({'name':'deaths', 'total':data['death']})
        l.append({'name':'total', 'total':data['total']})
        labels = ['name', 'total']
        repl_map = {'name':''}
        return "``python\n%s```" % utils.format_table(labels, l, repl_map=repl_map, left_list=['name'])

if __name__ == "__main__":
    print(get_us())

