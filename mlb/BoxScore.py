class BoxScore:
    def __init__(self,json):
        self.box = json
        self.players = {}
        self.__create_box()

    def __create_box(self):
        for t in self.box['teams']:
            for p in self.box['teams'][t]['players']:
                pid = self.box['teams'][t]['players'][p]['person']['id']
                self.players[pid] = self.box['teams'][t]['players'][p]

    def print_box(self):
        for batter in self.box['teams']['away']['batters']:
            player = self.players[batter]
            name = player['person']['fullName']
            pos = player['position']['abbreviation']
            print(name,pos)
            #print(player['person']['id'],player['person']['fullName'])
