from datetime import datetime
from fileinput import close

def parse_closing_hours():
    closed_hours = []
    with open('pause.txt') as f:
        while True:
            open_time = f.readline().strip('\n')
            close_time = f.readline().strip('\n')
            separator = f.readline()

            if not open_time or not close_time or not separator: break  # EOF

            closed_hours.append((datetime.strptime(open_time, "%Y-%m-%d %H:%M"), datetime.strptime(close_time, "%Y-%m-%d %H:%M")))
            
    return closed_hours