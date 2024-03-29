import os
import psutil
import socket
import subprocess

from libqtile import bar, hook, layout, qtile
from libqtile.config import Click, Drag, Group, Key, Screen
from libqtile.lazy import lazy
from libqtile.log_utils import logger
from libqtile.widget import (
    Battery,
    Bluetooth,
    Clock,
    CurrentLayout,
    CurrentLayoutIcon,
    GroupBox,
    Notify,
    PulseVolume,
    Prompt,
    Sep,
    Spacer,
    Systray,
    TaskList,
    TextBox,
)

try:
    import aiomanhole
except ImportError:
    aiomanhole = None

DEBUG = os.environ.get("DEBUG")

GREY = "#222222"
DARK_GREY = "#111111"
BLUE = "#007fdf"
DARK_BLUE = "#002a4a"
ORANGE = "#dd6600"
DARK_ORANGE = "#371900"


def focus_previous_group(qtile):
    group = qtile.current_screen.group
    group_index = qtile.groups.index(group)
    previous_group = group.get_previous_group(skip_empty=True)
    previous_group_index = qtile.groups.index(previous_group)
    if previous_group_index < group_index:
        qtile.current_screen.set_group(previous_group)


def focus_next_group(qtile):
    group = qtile.current_screen.group
    group_index = qtile.groups.index(group)
    next_group = group.get_next_group(skip_empty=True)
    next_group_index = qtile.groups.index(next_group)
    if next_group_index > group_index:
        qtile.current_screen.set_group(next_group)


def window_to_previous_column_or_group(qtile):
    layout = qtile.current_group.layout
    group_index = qtile.groups.index(qtile.current_group)
    previous_group_name = qtile.current_group.get_previous_group().name

    if layout.name != "columns":
        qtile.current_window.togroup(previous_group_name)
    elif layout.current == 0 and len(layout.cc) == 1:
        if group_index != 0:
            qtile.current_window.togroup(previous_group_name)
    else:
        layout.shuffle_left()


def window_to_next_column_or_group(qtile):
    layout = qtile.current_group.layout
    group_index = qtile.groups.index(qtile.current_group)
    next_group_name = qtile.current_group.get_next_group().name

    if layout.name != "columns":
        qtile.current_window.togroup(next_group_name)
    elif layout.current + 1 == len(layout.columns) and len(layout.cc) == 1:
        if group_index + 1 != len(qtile.groups):
            qtile.current_window.togroup(next_group_name)
    else:
        layout.shuffle_right()


def window_to_previous_screen(qtile):
    i = qtile.screens.index(qtile.current_screen)
    if i != 0:
        group = qtile.screens[i - 1].group.name
        qtile.current_window.togroup(group)


def window_to_next_screen(qtile):
    i = qtile.screens.index(qtile.current_screen)
    if i + 1 != len(qtile.screens):
        group = qtile.screens[i + 1].group.name
        qtile.current_window.togroup(group)


def switch_screens(qtile):
    if len(qtile.screens) == 1:
        previous_switch = getattr(qtile, "previous_switch", None)
        qtile.previous_switch = qtile.current_group
        return qtile.current_screen.toggle_group(previous_switch)

    i = qtile.screens.index(qtile.current_screen)
    group = qtile.screens[i - 1].group
    qtile.current_screen.set_group(group)


def init_keys():
    keys = [
        Key([mod], "Left", lazy.function(focus_previous_group)),
        Key([mod], "Right", lazy.function(focus_next_group)),
        Key([mod, "shift"], "Left", lazy.function(window_to_previous_column_or_group)),
        Key([mod, "shift"], "Right", lazy.function(window_to_next_column_or_group)),
        Key([mod, "control"], "Up", lazy.layout.grow_up()),
        Key([mod, "control"], "Down", lazy.layout.grow_down()),
        Key([mod, "control"], "Left", lazy.layout.grow_left()),
        Key([mod, "control"], "Right", lazy.layout.grow_right()),
        Key([mod, "mod1"], "Left", lazy.prev_screen()),
        Key([mod, "mod1"], "Right", lazy.next_screen()),
        Key([mod, "shift", "mod1"], "Left", lazy.function(window_to_previous_screen)),
        Key([mod, "shift", "mod1"], "Right", lazy.function(window_to_next_screen)),
        Key([mod], "t", lazy.function(switch_screens)),
        Key([mod], "Up", lazy.group.prev_window()),
        Key([mod], "Down", lazy.group.next_window()),
        Key([mod, "shift"], "Up", lazy.layout.shuffle_up()),
        Key([mod, "shift"], "Down", lazy.layout.shuffle_down()),
        Key([mod], "space", lazy.next_layout()),
        Key([mod, "shift"], "space", lazy.prev_layout()),
        Key([mod], "f", lazy.window.toggle_floating()),
        Key([mod, "shift"], "f", lazy.window.toggle_fullscreen()),
        Key([mod], "b", lazy.window.bring_to_front()),
        Key([mod], "s", lazy.layout.toggle_split()),
        Key([mod, "control"], "space", lazy.spawn("splatmoji type")),
        Key([mod], "g", lazy.labelgroup()),
        Key([mod], "r", lazy.spawn("rofi -show")),
        Key([mod], "u", lazy.spawn(browser)),
        Key([mod], "Return", lazy.spawn(terminal)),
        Key([mod], "BackSpace", lazy.window.kill()),
        Key([mod, "shift"], "r", lazy.reload_config()),
        Key([mod, "control"], "r", lazy.restart()),
        Key([mod, "shift"], "q", lazy.shutdown()),
        Key([mod], "v", lazy.validate_config()),
        Key([], "Print", lazy.spawn("gnome-screenshot -a")),
        Key([mod], "Print", lazy.spawn("gnome-screenshot -p")),
        Key([], "Scroll_Lock", lazy.spawn(screenlocker)),
        Key([mod], "Delete", lazy.spawn("pactl set-sink-mute @DEFAULT_SINK@ toggle")),
        Key([mod], "Prior", lazy.spawn("pactl set-sink-volume @DEFAULT_SINK@ +5%")),
        Key([mod], "Next", lazy.spawn("pactl set-sink-volume @DEFAULT_SINK@ -5%")),
        Key([mod], "Insert", lazy.spawn("spotify-dbus playpause")),
        Key([mod], "End", lazy.spawn("spotify-dbus next")),
        Key([mod], "Home", lazy.spawn("spotify-dbus previous")),
        Key([mod], "F11", lazy.spawn("headset")),
        Key([mod], "F12", lazy.spawn("speakers")),
    ]
    if DEBUG:
        keys += [
            Key([mod], "Tab", lazy.layout.next()),
            Key([mod, "shift"], "Tab", lazy.layout.previous()),
            Key([mod, "shift"], "f", lazy.layout.flip()),
            Key([mod, "shift"], "s", lazy.group["scratch"].dropdown_toggle("term")),
        ]
    return keys


def init_mouse():
    mouse = [
        Drag(
            [mod],
            "Button1",
            lazy.window.set_position_floating(),
            start=lazy.window.get_position(),
        ),
        Drag(
            [mod],
            "Button3",
            lazy.window.set_size_floating(),
            start=lazy.window.get_size(),
        ),
        Click([mod], "Button2", lazy.window.kill()),
    ]
    if DEBUG:
        mouse += [
            Drag(
                [mod, "shift"],
                "Button1",
                lazy.window.set_position(),
                start=lazy.window.get_position(),
            )
        ]
    return mouse


def init_groups():
    def _inner(key, name):
        keys.append(Key([mod], key, lazy.group[name].toscreen()))
        keys.append(Key([mod, "shift"], key, lazy.window.togroup(name)))
        return Group(name)

    groups = [("dead_grave", "00")]
    groups += [(str(i), "0" + str(i)) for i in range(1, 10)]
    groups += [("0", "10"), ("minus", "11"), ("equal", "12")]
    groups = [_inner(*i) for i in groups]

    if DEBUG:
        from libqtile.config import DropDown, ScratchPad

        dropdowns = [
            DropDown(
                "term",
                terminal,
                x=0.125,
                y=0.25,
                width=0.75,
                height=0.5,
                opacity=0.8,
                on_focus_lost_hide=True,
            )
        ]
        groups.append(ScratchPad("scratch", dropdowns))
    return groups


def init_floating_layout():
    return layout.Floating(border_focus=ORANGE)


def init_layouts():
    margin = 0
    if len(qtile.core.conn.pseudoscreens) > 1:
        margin = 8
    kwargs = dict(
        margin=margin,
        border_width=1,
        border_normal=GREY,
        border_focus=BLUE,
        border_focus_stack=ORANGE,
    )
    layouts = [
        layout.Max(),
        layout.Columns(border_on_single=True, num_columns=2, grow_amount=5, **kwargs),
    ]

    if DEBUG:
        layouts += [
            floating_layout,
            layout.Bsp(fair=False),
            layout.Zoomy(),
            layout.Tile(),
            layout.Matrix(),
            layout.TreeTab(),
            layout.MonadTall(margin=10),
            layout.RatioTile(),
            layout.Stack(),
        ]
    return layouts


def parse_notification(message):
    return message.replace("\n", "⏎")


def init_widgets():
    widgets = [
        CurrentLayoutIcon(scale=0.6, padding=8),
        GroupBox(
            fontsize=9,
            padding=2,
            borderwidth=1,
            urgent_border=DARK_BLUE,
            disable_drag=True,
            highlight_method="border",
            this_screen_border=DARK_BLUE,
            other_screen_border=DARK_ORANGE,
            this_current_screen_border=BLUE,
            other_current_screen_border=ORANGE,
        ),
        TextBox(
            text="◤", fontsize=45, padding=-1, foreground=DARK_GREY, background=GREY
        ),
        TaskList(
            borderwidth=0,
            highlight_method="block",
            background=GREY,
            border=DARK_GREY,
            urgent_border=DARK_BLUE,
            markup_floating="<i>{}</i>",
            markup_minimized="<s>{}</s>",
        ),
        Prompt(background=GREY),
        Systray(background=GREY),
        TextBox(
            text="◤", fontsize=45, padding=-1, foreground=GREY, background=DARK_GREY
        ),
        Notify(
            fmt=" 🔥 {} ",
            parse_text=parse_notification,
            background=DARK_GREY,
            background_low=DARK_GREY,
            background_urgent=DARK_GREY,
            default_timeout=None,
            default_timeout_low=None,
        ),
        Bluetooth(fmt=" ᛒ {} ", default_text="{connected_devices}"),
        PulseVolume(fmt=" {}", emoji=True, volume_app="pavucontrol"),
        PulseVolume(volume_app="pavucontrol"),
        Clock(format=" ⏱ %H:%M  <span color='#666'>%A %d-%m-%Y</span>  "),
    ]
    if os.path.isdir("/sys/module/battery"):
        widgets.insert(
            -1,
            Battery(
                format=" {char} {percent:2.0%} ",
                charge_char="⚡",
                discharge_char="🔋",
                full_char="⚡",
                unknown_char="⚡",
                empty_char="⁉️ ",
                update_interval=2,
                show_short_text=False,
                default_text="",
            ),
        )
        widgets.insert(
            -1,
            Battery(
                fmt="<span color='#666'>{}</span> ",
                format="{hour:d}:{min:02d}",
                update_interval=2,
                show_short_text=True,
                default_text="",
            ),
        )
    if DEBUG:
        widgets += [Sep(), CurrentLayout()]
    return widgets


@hook.subscribe.client_new
def set_floating(window):
    floating_classes = ("nm-connection-editor", "pavucontrol", "gnome-screenshot")
    try:
        if window.window.get_wm_class()[0] in floating_classes:
            window.floating = True
    except IndexError:
        pass


@hook.subscribe.startup_complete
def set_logging():
    if DEBUG:
        qtile.debug()


@hook.subscribe.startup_complete
def set_manhole():
    if aiomanhole:
        aiomanhole.start_manhole(port=7113, namespace={"qtile": qtile})


if __name__ in ["config", "__main__"]:
    local_bin = os.path.expanduser("~") + "/.local/bin"
    if local_bin not in os.environ["PATH"]:
        os.environ["PATH"] = "{}:{}".format(local_bin, os.environ["PATH"])

    mod = "mod4"
    browser = "google-chrome"
    terminal = "roxterm"
    screenlocker = "i3lock -d"
    hostname = socket.gethostname()
    cursor_warp = True
    focus_on_window_activation = "never"

    auto_fullscreen = False
    keys = init_keys()
    mouse = init_mouse()
    groups = init_groups()
    floating_layout = init_floating_layout()
    layouts = init_layouts()
    widgets = init_widgets()
    bar = bar.Bar(widgets=widgets, size=22, opacity=1)
    screens = [Screen(top=bar, wallpaper="~/.background.jpg")]
    widget_defaults = {
        "font": "DejaVu",
        "fontsize": 11,
        "padding": 2,
        "background": DARK_GREY,
    }
