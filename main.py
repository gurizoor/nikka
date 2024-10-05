
from lib import *

def main(*args):
    app = tk.Tk()
    LabelManagerApp(app)
    
    #App(app)   
    app.mainloop()

#toast('日課',on_click=main)
main()