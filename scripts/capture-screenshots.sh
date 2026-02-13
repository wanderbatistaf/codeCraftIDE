#!/bin/bash
#
# Screenshot Capture Helper for Story 3.2
# This script helps prepare the IDE for screenshot capture
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEMO_FILE="$PROJECT_ROOT/examples/nested_blocks_demo.4gl"
SCREENSHOTS_DIR="$PROJECT_ROOT/screenshots/story-3.2"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Story 3.2 Screenshot Capture Helper${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Create screenshots directory
mkdir -p "$SCREENSHOTS_DIR"
echo -e "${GREEN}✓${NC} Created screenshots directory: $SCREENSHOTS_DIR"

# Check if demo file exists
if [ ! -f "$DEMO_FILE" ]; then
    echo -e "${YELLOW}⚠${NC} Demo file not found: $DEMO_FILE"
    echo "Please ensure the file exists before capturing screenshots."
    exit 1
fi

echo -e "${GREEN}✓${NC} Demo file found: $DEMO_FILE"
echo ""

# Display the demo file content summary
echo -e "${BLUE}Demo file structure:${NC}"
echo "  Lines 1-10:   MAIN block start and variable definitions"
echo "  Lines 18-35:  Nested IF blocks (Screenshot 1 - Indentation)"
echo "  Lines 45-65:  FOR inside WHILE (Screenshot 2 - Bracket colors)"
echo "  Lines 68-90:  CASE statement (Screenshot 3 & 4 - Sticky scroll)"
echo ""

# Instructions
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo -e "${YELLOW}1. Start the backend:${NC}"
echo "   cd $PROJECT_ROOT/src/fglinterpreter"
echo "   python -m api.main"
echo ""
echo -e "${YELLOW}2. Start the IDE (in a new terminal):${NC}"
echo "   cd $PROJECT_ROOT/ide"
echo "   npm run dev"
echo ""
echo -e "${YELLOW}3. Open browser:${NC}"
echo "   http://localhost:5173"
echo ""
echo -e "${YELLOW}4. Load demo file:${NC}"
echo "   Copy and paste content from: $DEMO_FILE"
echo ""
echo -e "${BLUE}Screenshot positions:${NC}"
echo ""

# Screenshot checklist
cat << 'EOF'
📸 Screenshot 1: Indentation Guides
   Position: Line 26, column 6-8
   Features: Vertical guides, active path highlighted
   File: screenshot-1-indentation-guides.png

📸 Screenshot 2: Bracket Pair Colorization
   Position: Lines 45-65 visible, cursor at line 50
   Features: Gold/purple/blue bracket pairs
   File: screenshot-2-bracket-colorization.png

📸 Screenshot 3: Sticky Scroll
   Position: Scrolled to lines 70-85
   Features: Context bar at top showing MAIN > CASE
   File: screenshot-3-sticky-scroll.png

📸 Screenshot 4: All Features Combined
   Position: Line 52, full editor visible
   Features: All enhancements working together
   File: screenshot-4-all-features-combined.png

📸 Screenshot 5: Before/After (Optional)
   Create side-by-side comparison
   File: screenshot-5-before-after-comparison.png

EOF

echo ""
echo -e "${BLUE}Saving screenshots:${NC}"
echo "Save your screenshots to: $SCREENSHOTS_DIR"
echo ""
echo -e "${GREEN}Tip:${NC} After capturing, run this script again with 'verify' to check:"
echo "  ./capture-screenshots.sh verify"
echo ""

# If verify argument is provided
if [ "$1" = "verify" ]; then
    echo -e "${BLUE}Verifying screenshots...${NC}"
    echo ""

    REQUIRED_SCREENSHOTS=(
        "screenshot-1-indentation-guides.png"
        "screenshot-2-bracket-colorization.png"
        "screenshot-3-sticky-scroll.png"
        "screenshot-4-all-features-combined.png"
    )

    MISSING=0
    for screenshot in "${REQUIRED_SCREENSHOTS[@]}"; do
        if [ -f "$SCREENSHOTS_DIR/$screenshot" ]; then
            echo -e "${GREEN}✓${NC} Found: $screenshot"
        else
            echo -e "${YELLOW}✗${NC} Missing: $screenshot"
            MISSING=$((MISSING + 1))
        fi
    done

    # Optional screenshot
    if [ -f "$SCREENSHOTS_DIR/screenshot-5-before-after-comparison.png" ]; then
        echo -e "${GREEN}✓${NC} Found: screenshot-5-before-after-comparison.png (optional)"
    fi

    echo ""
    if [ $MISSING -eq 0 ]; then
        echo -e "${GREEN}✓ All required screenshots present!${NC}"
        echo ""
        echo "Next: Upload these to your PR on GitHub"
        echo "See: docs/PR_TEMPLATE_STORY_3.2.md for the PR description"
    else
        echo -e "${YELLOW}⚠ $MISSING required screenshot(s) missing${NC}"
        echo "Run without 'verify' to see capture instructions."
    fi
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Ready to capture!${NC}"
echo -e "${BLUE}========================================${NC}"
