#!/bin/bash
if [[ -f ~/.xprofile ]]; then
   . ~/.xprofile
fi

exec dbus-launch --exit-with-session coverage run --append --source=libqtile -m libqtile.scripts.main start
