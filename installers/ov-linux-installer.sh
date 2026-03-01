#!/bin/bash

echo "Starting Open Vulnera installation..."
sleep 2
echo "This will take approximately 5 minutes..."
sleep 2

# Detect Termux
if [ -n "$TERMUX_VERSION" ] || [ "$PREFIX" = "/data/data/com.termux/files/usr" ] || [ -f "/data/data/com.termux/files/usr/bin/termux-info" ]; then
    echo "Termux detected. Installing dependencies..."
    
    # Set Termux mirror
    echo "deb https://mirror.grimler.se stable main" > $PREFIX/etc/apt/sources.list
    
    # Update and upgrade
    pkg update && pkg upgrade -y
    
    # Install required packages
    pkg install clang rust make binutils python tur-repo -y
    
    # Set Termux environment variables
    export ANDROID_API_LEVEL=$(getprop ro.build.version.sdk)
    export CC=clang
    export CXX=clang++
    export LDFLAGS="-lpthread"
    export CXXFLAGS="-lpthread -D__ANDROID_API__=$ANDROID_API_LEVEL"
    
    # Install pre-built binaries via pkg
    pkg install python-numpy python-pillow python-cryptography python-pydantic-core python-grpcio python-msgspec python-rpds-py -y 2>/dev/null || true
    
    # Install setuptools compatible version for Python 3.12
    pip install "setuptools<70.0.0"
    
    # Install cycler and dependencies
    pip install cycler fonttools pyparsing python-dateutil
    
    # Force lower API level for packages that need compiling
    CFLAGS="-D__ANDROID_API__=24" CXXFLAGS="-D__ANDROID_API__=24" pip install kiwisolver 2>/dev/null || true
    
    # Install open-vulnera
    pip install open-vulnera
else
    # Check if Rust is installed
    if ! command -v rustc &> /dev/null
    then
        echo "Rust is not installed. Installing now..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    else
        echo "Rust is already installed."
    fi

    # Install pyenv
    curl https://pyenv.run | bash

    # Define pyenv location
    pyenv_root="$HOME/.pyenv/bin/pyenv"

    python_version="3.11.7"

    # Install specific Python version using pyenv
    $pyenv_root init
    $pyenv_root install $python_version --skip-existing
    $pyenv_root shell $python_version

    $pyenv_root exec pip install open-vulnera --break-system-packages
    # Unset the Python version
    $pyenv_root shell --unset
fi

echo ""
echo "Open Vulnera has been installed. Run the following command to use it: "
echo ""
echo "vulnera"
