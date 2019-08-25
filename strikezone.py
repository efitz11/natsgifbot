import matplotlib.pyplot as plt
import matplotlib.patches as patches

class StrikeZone():
    def __init__(self, sz_top, sz_bot):
        plt.figure(figsize=(5.2,6.2))
        rect = patches.Rectangle((-0.72,sz_bot),1.44,sz_top-sz_bot, fill=None, linewidth=2)
        plt.gca().add_patch(rect)
        # plt.axis('scaled')
        plt.ylim((0,4))
        plt.xlim((-2,2))
        self.plt = plt
        self.num_pitches = 0

    def add_pitch(self, px, pz, strike=False):
        #draw pitch location on chart
        self.num_pitches += 1
        if strike:
            color="red"
        else:
            color="green"
        circle = patches.Circle((px, pz), radius=0.09, color=color)
        self.plt.gca().add_patch(circle)
        self.plt.annotate(str(self.num_pitches), (px-.045, pz-.045), color="white", weight="bold")
        # self.plt.axis('scaled')

    def show_plot(self):
        self.plt.show()

if __name__ == "__main__":
    zone = StrikeZone(3.39, 1.62)
    zone.add_pitch(1.58,3.37)
    zone.add_pitch(.6, 1.89, strike=True)
    zone.add_pitch(0.02,0.56)
    zone.add_pitch(-.56, .87)
    zone.add_pitch(-.49, 1.95, strike=True)
    zone.add_pitch(.81, 2.13, strike=True)
    zone.add_pitch(-.9, 1.74, strike=True)
    zone.show_plot()

