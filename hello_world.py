import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class MyWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title='Hello, world!')

        self.set_default_size(250, 100)

        text = 'Gtk v' + str(Gtk.get_major_version()) + '.' \
        + str(Gtk.get_minor_version()) + '.' + str(Gtk.get_micro_version()) \
        + ' is installed and\nworking correctly' \
        + '\n\nClick here to close the window'
            
        self.button = Gtk.Button(label=text)
        self.button.connect('clicked', self.on_button_clicked)
        self.add(self.button)

    def on_button_clicked(self, widget):
        self.destroy()

win = MyWindow()
win.connect('destroy', Gtk.main_quit)
win.show_all()
Gtk.main()
