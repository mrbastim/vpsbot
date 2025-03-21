#!/bin/bash

usage() {
  echo "Usage: $0 [-c <client_name>] [-p <password_option>] [-r <revoke_client_name>] [-l <yes|no>] [-h]"
  echo "Options:"
  echo "  -c <client_name>      Add a new client with the specified name."
  echo "  -p <password_option>  Password option for the new client (1 for passwordless, 2 for password-protected)."
  echo "  -r <revoke_client_name> Revoke the specified client certificate."
  echo "  -l <yes|no>           Enable (yes) or disable (no) local network grouping for clients."
  echo "  -h                    Display this help message."
  exit 1
}


while getopts ":c:p:r:l:h" opt; do
  case $opt in
    c)
      CLIENT="$OPTARG"
      ;;
    p)
      PASS="$OPTARG"
      ;;
    r)
      REVOKE_CLIENT="$OPTARG"
      ;;
    l)
      LOCAL_NETWORK="$OPTARG"
      if [[ "$LOCAL_NETWORK" != "yes" && "$LOCAL_NETWORK" != "no" ]]; then
        echo "Invalid option for -l. Use 'yes' or 'no'." >&2
        usage
      fi
      ;;
    h)
      usage
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      usage
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      usage
      ;;
  esac
done

newClient() {
  if [[ ! "$CLIENT" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "Client name must consist of alphanumeric characters, underscores, or dashes."
    exit 1
  fi

  if [[ "$PASS" -ne 1 && "$PASS" -ne 2 ]]; then
    echo "Invalid password option. Use 1 for passwordless or 2 for password-protected."
    exit 1
  fi


  CLIENTEXISTS=$(tail -n +2 /etc/openvpn/easy-rsa/pki/index.txt | grep -c -E "/CN=$CLIENT\$")
  if [[ $CLIENTEXISTS == '1' ]]; then
    echo "The specified client CN already exists. Choose a different name."
    exit 1
  fi

  cd /etc/openvpn/easy-rsa/ || return 1

  case "$PASS" in
    1)
      EASYRSA_CERT_EXPIRE=3650 ./easyrsa --batch build-client-full "$CLIENT" nopass
      ;;
    2)
      echo "⚠️ You will be asked for the client password below ⚠️"
      EASYRSA_CERT_EXPIRE=3650 ./easyrsa --batch build-client-full "$CLIENT"
      ;;
  esac

  if [[ $? -ne 0 ]]; then  # Check for errors during client creation
    echo "Error creating client certificate."
    exit 1
  fi


  	# Home directory of the user, where the client configuration will be written
	if [ -e "/home/${CLIENT}" ]; then
		# if $1 is a user name
		homeDir="/home/${CLIENT}"
	elif [ "${SUDO_USER}" ]; then
		# if not, use SUDO_USER
		if [ "${SUDO_USER}" == "root" ]; then
			# If running sudo as root
			homeDir="/root/vpn_configs"
		else
			homeDir="/home/${SUDO_USER}"
		fi
	else
		# if not SUDO_USER, use /root
		homeDir="/root/vpn_configs"
	fi

	# Determine if we use tls-auth or tls-crypt
	if grep -qs "^tls-crypt" /etc/openvpn/server.conf; then
		TLS_SIG="1"
	elif grep -qs "^tls-auth" /etc/openvpn/server.conf; then
		TLS_SIG="2"
	fi

	# Generates the custom client.ovpn
	cp /etc/openvpn/client-template.txt "$homeDir/$CLIENT.ovpn"
	{
		echo "<ca>"
		cat "/etc/openvpn/easy-rsa/pki/ca.crt"
		echo "</ca>"

		echo "<cert>"
		awk '/BEGIN/,/END CERTIFICATE/' "/etc/openvpn/easy-rsa/pki/issued/$CLIENT.crt"
		echo "</cert>"

		echo "<key>"
		cat "/etc/openvpn/easy-rsa/pki/private/$CLIENT.key"
		echo "</key>"

		case $TLS_SIG in
		1)
			echo "<tls-crypt>"
			cat /etc/openvpn/tls-crypt.key
			echo "</tls-crypt>"
			;;
		2)
			echo "key-direction 1"
			echo "<tls-auth>"
			cat /etc/openvpn/tls-auth.key
			echo "</tls-auth>"
			;;
		esac
	} >>"$homeDir/$CLIENT.ovpn"

    # Если включено объединение в локальную сеть, добавляем дополнительные настройки.
  if [[ "$LOCAL_NETWORK" == "yes" ]]; then
    {
      echo ""
      echo "# Local network grouping enabled"
      echo "# Example: Adding route for clients to access the VPN subnet"
      echo "route 10.8.0.0 255.255.255.0"
    } >>"$homeDir/$CLIENT.ovpn"
  fi

	echo ""
	echo "The configuration file has been written to $homeDir/$CLIENT.ovpn."
	echo "Download the .ovpn file and import it in your OpenVPN client."

	exit 0

}


revokeClient() {
  if [[ -z "$REVOKE_CLIENT" ]]; then
    echo "Please specify a client name to revoke using -r <client_name>"
    tail -n +2 /etc/openvpn/easy-rsa/pki/index.txt | grep "^V" | cut -d '=' -f 2 | nl -s ') '
    exit 1
  fi

    # ... (rest of the revokeClient function remains the same, but use $REVOKE_CLIENT instead of prompting)
    cd /etc/openvpn/easy-rsa/ || return
	./easyrsa --batch revoke "$REVOKE_CLIENT"
	EASYRSA_CRL_DAYS=3650 ./easyrsa gen-crl
	rm -f /etc/openvpn/crl.pem
	cp /etc/openvpn/easy-rsa/pki/crl.pem /etc/openvpn/crl.pem
	chmod 644 /etc/openvpn/crl.pem
	find /home/ -maxdepth 2 -name "$REVOKE_CLIENT.ovpn" -delete
	rm -f "/root/vpn_configs/$REVOKE_CLIENT.ovpn"
	sed -i "/^$REVOKE_CLIENT,.*/d" /etc/openvpn/ipp.txt
	cp /etc/openvpn/easy-rsa/pki/index.txt{,.bk}

	echo ""
	echo "Certificate for client $REVOKE_CLIENT revoked."

}


if [[ -n "$CLIENT" ]]; then
  newClient
elif [[ -n "$REVOKE_CLIENT" ]]; then
  revokeClient
else
  usage
fi