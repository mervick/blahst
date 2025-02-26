import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk, GObject
from rlottie_python import LottieAnimation
from PIL import Image
import cairo
import json
from gi.repository import GdkPixbuf
import numpy as np
from pydbus import SessionBus

from rlottie_python import LottieAnimation
import json


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

    def load_animation(self, file: str) -> None:
        self.animation = LottieAnimation.from_file(file)
        self.frame_count  = self.animation.lottie_animation_get_totalframe()
        self.frame_number = 0

    def __init__(self):
        super().__init__(title="Lottie Animation in GTK")
        window_width, window_height = WIN_SIZE
        self.set_default_size(window_width, window_height)
        # self.set_default_size(window_width, window_height + 20)

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
            window.emit('show_spinner', {"label": message})


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

            # Создаем окно
            window = LottieWindow()
            window.set_title(f"Monitor {i + 1}")
            window.set_decorated(False)  # Убираем рамку
            window.set_app_paintable(True)  # Разрешаем рисование
            window.set_visual(window.get_screen().get_rgba_visual())  # Прозрачность
            window.set_type_hint(Gdk.WindowTypeHint.DOCK)  # Окно поверх всех окон
            window.set_keep_above(True)  # Окно всегда поверх других окон
            window.connect("destroy", Gtk.main_quit)

            # # Добавляем анимацию (например, Spinner)
            # spinner = Gtk.Spinner()
            # spinner.set_size_request(100, 100)
            # spinner.start()
            # window.add(spinner)

            window.show_all()

            window_width, window_height = 320, 320
            x = geometry.x + (geometry.width - window_width) // 2
            y = geometry.y + (geometry.height - window_height) // 2
            window.move(x, y)

            self.windows.append(window)
        # for i in range(n_monitors):
        #     monitor = display.get_monitor(i)
        #     geometry = monitor.get_geometry()
        #
        #     # Создаем окно
        #     window = Gtk.Window()
        #     window.set_title(f"Monitor {i + 1}")
        #     window.set_decorated(False)  # Убираем рамку
        #     window.set_app_paintable(True)  # Разрешаем рисование
        #     window.set_visual(window.get_screen().get_rgba_visual())  # Прозрачность
        #     window.set_type_hint(Gdk.WindowTypeHint.DOCK)  # Окно поверх всех окон
        #     window.set_keep_above(True)  # Окно всегда поверх других окон
        #     window.connect("destroy", Gtk.main_quit)
        #
        #     # Добавляем анимацию (например, Spinner)
        #     spinner = Gtk.Spinner()
        #     spinner.set_size_request(100, 100)
        #     spinner.start()
        #     window.add(spinner)
        #
        #     # Показываем окно
        #     window.show_all()
        #
        #     # Центрируем окно на мониторе
        #     window_width, window_height = 200, 200  # Размер окна
        #     x = geometry.x + (geometry.width - window_width) // 2
        #     y = geometry.y + (geometry.height - window_height) // 2
        #     window.move(x, y)
        #
        #     self.windows.append(window)

if __name__ == "__main__":
    app = MultiMonitorApp()
    bus = SessionBus()
    bus.publish("dev.mervick.blahstSpinner", app)
    Gtk.main()
