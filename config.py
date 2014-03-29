# -*- coding: utf-8 -*-
import os

from libqtile.config import Key, Screen, Group
from libqtile.command import lazy
from libqtile import layout, bar, widget, hook


@lazy.function
def window_to_prev_group(qtile):
    if qtile.currentWindow is not None:
        i = qtile.groups.index(qtile.currentGroup)
        qtile.currentWindow.togroup(qtile.groups[i - 1].name)


@lazy.function
def window_to_next_group(qtile):
    if qtile.currentWindow is not None:
        i = qtile.groups.index(qtile.currentGroup)
        qtile.currentWindow.togroup(qtile.groups[i + 1].name)


def init_keys():
    return [Key([mod, "control"], "j", lazy.layout.shuffle_up()),
            Key([mod, "control"], "k", lazy.layout.shuffle_down()),

            Key([mod], "Left", lazy.screen.prevgroup()),
            Key([mod], "Right", lazy.screen.nextgroup()),

            Key([mod, "shift"], "Left", window_to_prev_group),
            Key([mod, "shift"], "Right", window_to_next_group),

            Key([mod], "Tab", lazy.layout.previous()),
            Key([mod, "shift"], "Tab", lazy.layout.next()),

            Key([mod], "space", lazy.nextlayout()),
            Key([mod, "shift"], "space", lazy.prevlayout()),

            Key([mod], "j", lazy.layout.up()),
            Key([mod], "k", lazy.layout.down()),

            Key([mod], "r", lazy.spawncmd("cmd")),
            Key([mod, "shift"], "c", lazy.window.kill()),
            Key([mod], "Return", lazy.spawn("gnome-terminal")),
            Key([mod], "l", lazy.spawn("i3lock -d -c000000")),
            Key([mod, "control"], "r", lazy.restart())]

def init_colors():
    return ["c52929",
            "ded401",
            "555555",
            "282828"]

def init_groups():
    groups = []
    for i in range(1, 10):
        name = str(i)
        groups.append(Group(name))
        keys.append(Key([mod], name, lazy.group[name].toscreen()))
        keys.append(Key([mod, "shift"], name, lazy.window.togroup(name)))
    return groups


def init_layouts():
    return [layout.Max(),
            layout.Tile(ratio=0.5),
            layout.Floating()]


def init_widgets():
    return [widget.GroupBox(fontsize=8, padding=4, borderwidth=1,
                            this_current_screen_border=colors[0]),
            widget.Prompt(prompt=" ", font="DejaVu Bold",
                          background=colors[1], foreground=colors[3]),
            widget.TaskList(borderwidth=1, border=colors[0],
                            urgent_border=colors[1]),
            widget.Systray(),
            widget.TextBox(text=" (", foreground=colors[0]),
            widget.TextBox(text="↯", foreground=colors[1]),
            widget.Battery(update_delay=5),
            widget.TextBox(text="|", foreground=colors[0]),
            widget.TextBox(text="⌚", foreground=colors[1]),
            widget.Clock(fmt="%a %d-%m-%Y %H:%M"),
            widget.TextBox(text=") ", foreground=colors[0])]

def init_top_bar():
    return bar.Bar(widgets=init_widgets(), size=25)


def init_screens():
    return [Screen(top=init_top_bar())]


def init_widgets_defaults():
    return dict(font="DejaVu",
                fontsize=12,
                padding=2,
                background=colors[3])


@hook.subscribe.client_new
def floating_dialogs(window):
    dialog = window.window.get_wm_type() == 'dialog'
    transient = window.window.get_wm_transient_for()
    if dialog or transient:
        window.floating = True


if __name__ == "config":
    mod = "mod4"
    colors = init_colors()
    keys = init_keys()
    groups = init_groups()
    layouts = init_layouts()
    screens = init_screens()
    widget_defaults = init_widgets_defaults()
    os.system("feh --bg-scale ~/.background.jpg")
