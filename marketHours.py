from datetime import datetime
from fileinput import close

class MarketHours:
    def create():
        self = MarketHours()
        self.closing_hours = self.parse_closing_hours()
        return self


    def parse_closing_hours(self):
        closed_hours = []
        with open('pause.txt') as f:
            while True:
                open_time = f.readline().strip('\n')
                close_time = f.readline().strip('\n')
                separator = f.readline()

                if not open_time or not close_time or not separator: break  # EOF

                closed_hours.append((datetime.strptime(open_time, "%Y-%m-%d %H:%M"), datetime.strptime(close_time, "%Y-%m-%d %H:%M")))
                
        return closed_hours


    def is_open_hour(self):

        if len(self.closing_hours) == 0: return True

        start, end = self.closing_hours[0]
        now = datetime.datetime.now()

        #dont run in down hours
        if now >= start and now <= end:
            return False
        
        else:
            #when close window ends, delete it from list
            if now > end:
                self.closing_hours.pop(0)
            
            return True