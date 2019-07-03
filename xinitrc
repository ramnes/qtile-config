#!/bin/bash
if [[ -f ~/.xprofile ]]; then
   . ~/.xprofile
fi

exec dbus-launch --exit-with-session qtile
