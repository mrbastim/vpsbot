#!/bin/bash
# Выводит список активных клиентов OpenVPN (CN из index.txt)

pki_index="/etc/openvpn/easy-rsa/pki/index.txt"
tail -n +2 "$pki_index" | grep "^V" | cut -d '=' -f 2
