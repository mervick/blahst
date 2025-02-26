import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk, GObject
from PIL import Image
from gi.repository import GdkPixbuf
import numpy as np
from pydbus import SessionBus
from rlottie_python import LottieAnimation


WIN_SIZE = (235, 235)


def pil_to_pixbuf_numpy(image: Image.Image) -> GdkPixbuf.Pixbuf:
    """Convert PIL Image to GdkPixbuf.Pixbuf using numpy."""
    array = np.array(image)
    height, width = array.shape[:2]
    has_alpha = array.shape[2] == 4 if len(array.shape) == 3 else False
    stride = width * (4 if has_alpha else 3)

    return GdkPixbuf.Pixbuf.new_from_data(
        array.tobytes(),
        GdkPixbuf.Colorspace.RGB,
        has_alpha,
        8,
        width,
        height,
        stride,
        lambda _: None,
        None
    )


class LottieWindow(Gtk.Window):
    __gsignals__ = {
        'show_spinner': (GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    }

    animation: LottieAnimation
    frame_count: int
    frame_number: int

    def load_animation(self, file: str) -> None:
        self.animation = LottieAnimation.from_file(file)
        self.frame_count  = self.animation.lottie_animation_get_totalframe()
        self.frame_number = 0

    def __init__(self):
        super().__init__(title="Lottie Animation in GTK")
        window_width, window_height = WIN_SIZE
        self.set_default_size(window_width, window_height)

        file = os.path.join(os.path.dirname(__file__), "animation.json")
        self.load_animation(file)
        self.frame_per_iter = 1

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.connect("draw", self.on_draw)
        self.add(self.drawing_area)

        self.fps = self.animation.lottie_animation_get_framerate()
        interval = int(1000 / self.fps)
        self.timer = GLib.timeout_add(interval, self.update_frame)

    def do_show_spinner(self, obj):
        file = os.path.join(os.path.dirname(__file__), "animation2.json")
        self.load_animation(file)
        self.frame_per_iter = 3

        GLib.source_remove(self.timer)
        self.fps = self.animation.lottie_animation_get_framerate() * 5
        interval = int(1000 / self.fps)
        self.timer = GLib.timeout_add(interval, self.update_frame)

    def on_draw(self, widget, cr):
        buffer = self.animation.lottie_animation_render(frame_num=self.frame_number)
        width, height = self.animation.lottie_animation_get_size()
        img = Image.frombuffer("RGBA", (width, height), buffer, "raw", "BGRA")
        img = img.resize(WIN_SIZE, Image.ANTIALIAS)
        pixbuf = pil_to_pixbuf_numpy(img)
        surface = Gdk.cairo_surface_create_from_pixbuf(pixbuf, 0, None)
        cr.set_source_surface(surface, 0, 0)
        cr.paint()

    def update_frame(self):
        self.frame_number = (self.frame_number + self.frame_per_iter) % self.frame_count
        self.drawing_area.queue_draw()
        return True


class MultiMonitorApp:
    """
    <node>
        <interface name='dev.mervick.blahstSpinner'>
            <method name='SendMessage'>
                <arg type='s' name='message' direction='in'/>
            </method>
        </interface>
    </node>
    """
    def SendMessage(self, message):
        print(f"Received: {message}")
        if message == "close":
            for window in self.windows:
                window.destroy()
            Gtk.main_quit()
            return

        for window in self.windows:
            window.emit('show_spinner', {"message": message})

    def __init__(self):
        self.windows = []
        self.create_windows()

    def create_windows(self):
        screen = Gdk.Screen.get_default()
        display = screen.get_display()
        n_monitors = display.get_n_monitors()

        for i in range(n_monitors):
            monitor = display.get_monitor(i)
            geometry = monitor.get_geometry()

            window = LottieWindow()
            window.set_title(f"Monitor {i + 1}")
            window.set_decorated(False)  # Remove frame
            window.set_app_paintable(True)  # Enable drawing
            window.set_visual(window.get_screen().get_rgba_visual())  # Transparency
            window.set_type_hint(Gdk.WindowTypeHint.DOCK)  # Window on top of all windows
            window.set_keep_above(True)  # Window always on top of other windows
            window.connect("destroy", Gtk.main_quit)
            window.show_all()

            window_width, window_height = 320, 320
            x = geometry.x + (geometry.width - window_width) // 2
            y = geometry.y + (geometry.height - window_height) // 2
            window.move(x, y)

            self.windows.append(window)

if __name__ == "__main__":
    app = MultiMonitorApp()
    bus = SessionBus()
    bus.publish("dev.mervick.blahstSpinner", app)
    Gtk.main()
