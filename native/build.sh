#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "⚡ [CAIEDIT] Compiling Native C++ Engines with Clang++..."

CXX="${CXX:-clang++}"
CXXFLAGS="-O3 -fPIC -shared -std=c++17 -Wall -Wextra"

# Check for ARM NEON
if [[ $(uname -m) == "aarch64"* ]]; then
    CXXFLAGS="$CXXFLAGS -march=armv8-a+simd"
    echo "  -> Target Architecture: aarch64 (NEON SIMD Vectorization Enabled)"
fi

echo "  -> Compiling libcaiedit_fx.so..."
$CXX $CXXFLAGS "$SCRIPT_DIR/caiedit_fx.cpp" -o "$SCRIPT_DIR/libcaiedit_fx.so"

echo "  -> Compiling libcaiedit_dsp.so..."
$CXX $CXXFLAGS "$SCRIPT_DIR/caiedit_dsp.cpp" -o "$SCRIPT_DIR/libcaiedit_dsp.so"

echo "  -> Compiling libcaiedit_flow.so..."
$CXX $CXXFLAGS "$SCRIPT_DIR/caiedit_flow.cpp" -o "$SCRIPT_DIR/libcaiedit_flow.so"

echo "✅ [CAIEDIT] All native libraries compiled successfully:"
ls -lh "$SCRIPT_DIR"/*.so
