#!/bin/bash

# Tibetan Fonts Installation Script
# This script downloads and installs commonly used Tibetan fonts on macOS

set -e

echo "================================================"
echo "  Tibetan Fonts Installation Script"
echo "================================================"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "⚠️  This script is designed for macOS."
    echo "For other operating systems, please follow the manual installation instructions."
    exit 1
fi

# Create temporary directory
TEMP_DIR=$(mktemp -d)
FONT_DIR="$HOME/Library/Fonts"

echo "📂 Using temporary directory: $TEMP_DIR"
echo "📂 Installing fonts to: $FONT_DIR"
echo ""

# Function to download and install a font
install_font() {
    local font_name=$1
    local font_url=$2
    local font_file=$3
    
    echo "📥 Downloading $font_name..."
    
    if curl -L -o "$TEMP_DIR/$font_file" "$font_url" 2>/dev/null; then
        echo "✅ Downloaded $font_name"
        
        # Check file extension and handle accordingly
        if [[ "$font_file" == *.zip ]]; then
            echo "📦 Extracting $font_name..."
            unzip -q "$TEMP_DIR/$font_file" -d "$TEMP_DIR/${font_name}_extracted"
            find "$TEMP_DIR/${font_name}_extracted" -name "*.ttf" -o -name "*.otf" | while read font; do
                cp "$font" "$FONT_DIR/"
                echo "   Installed: $(basename "$font")"
            done
        else
            cp "$TEMP_DIR/$font_file" "$FONT_DIR/"
            echo "   Installed: $font_file"
        fi
        echo ""
    else
        echo "❌ Failed to download $font_name"
        echo "   You can manually download from: $font_url"
        echo ""
    fi
}

# Install Tibetan Machine Uni
echo "1️⃣  Installing Tibetan Machine Uni..."
install_font "Tibetan Machine Uni" \
    "https://collab.its.virginia.edu/access/content/group/26a34146-33a6-48ce-001e-f16ce7908a6a/Tibetan%20fonts/Tibetan%20Machine%20Uni/TibetanMachineUni.ttf" \
    "TibetanMachineUni.ttf"

# Install Jomolhari
echo "2️⃣  Installing Jomolhari..."
install_font "Jomolhari" \
    "https://collab.its.virginia.edu/access/content/group/26a34146-33a6-48ce-001e-f16ce7908a6a/Tibetan%20fonts/Jomolhari/Jomolhari-ID.ttf" \
    "Jomolhari-ID.ttf"

echo "================================================"
echo "✨ Font Installation Complete!"
echo "================================================"
echo ""
echo "Installed fonts:"
echo "  • Tibetan Machine Uni"
echo "  • Jomolhari"
echo ""
echo "Next steps:"
echo "  1. The fonts are now available in all applications"
echo "  2. You may need to restart applications to see the new fonts"
echo "  3. To install a Tibetan keyboard:"
echo "     - Open System Settings → Keyboard → Input Sources"
echo "     - Click '+' and add Tibetan keyboard"
echo ""
echo "For more fonts and detailed instructions, visit:"
echo "  https://butter-dots-dot-com/resources"
echo ""

# Cleanup
rm -rf "$TEMP_DIR"
echo "🧹 Cleaned up temporary files"
echo ""
echo "Enjoy typing in Tibetan! བཀྲ་ཤིས་བདེ་ལེགས།"
echo ""
