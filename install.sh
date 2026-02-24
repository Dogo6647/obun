#!/bin/bash
echo "Installing/updating Obun..."
cp obun.py obun
chmod +x obun
sudo mkdir -p /usr/local/bin/ 
sudo mv obun /usr/local/bin/
echo "Installation process finished. Try running 'obun --help' to confirm it works."
