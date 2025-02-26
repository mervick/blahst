import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

class MultiMonitorApp:
    def __init__(self):
        self.windows = []
        self.create_windows()

    def create_windows(self):
        # Получаем экран и информацию о мониторах
        screen = Gdk.Screen.get_default()
        display = screen.get_display()
        n_monitors = display.get_n_monitors()

        # Создаем окно для каждого монитора
        for i in range(n_monitors):
            monitor = display.get_monitor(i)
            geometry = monitor.get_geometry()

            # Создаем окно
            window = Gtk.Window()
            window.set_title(f"Monitor {i + 1}")
            window.set_decorated(False)  # Убираем рамку
            window.set_app_paintable(True)  # Разрешаем рисование
            window.set_visual(window.get_screen().get_rgba_visual())  # Прозрачность
            window.set_type_hint(Gdk.WindowTypeHint.DOCK)  # Окно поверх всех окон
            window.set_keep_above(True)  # Окно всегда поверх других окон
            window.connect("destroy", Gtk.main_quit)

            # Добавляем анимацию (например, Spinner)
            spinner = Gtk.Spinner()
            spinner.set_size_request(100, 100)
            spinner.start()
            window.add(spinner)

            # Показываем окно
            window.show_all()

            # Центрируем окно на мониторе
            window_width, window_height = 200, 200  # Размер окна
            x = geometry.x + (geometry.width - window_width) // 2
            y = geometry.y + (geometry.height - window_height) // 2
            window.move(x, y)

            self.windows.append(window)

if __name__ == "__main__":
    app = MultiMonitorApp()
    Gtk.main()
