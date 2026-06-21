#!/usr/bin/bash
pacman -S rofi
cp GuiPackageManager.py /bin
cd /bin
mv GuiPackageManager.py PackageViewer
chmod +x PackageViewer
#needs sudo
