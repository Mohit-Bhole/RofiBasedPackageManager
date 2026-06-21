#!/usr/bin/bash
pacman -S rofi
cp PackageViewer.py /bin
cd /bin
mv PackageViewer.py PackageViewer
chmod +x PackageViewer
